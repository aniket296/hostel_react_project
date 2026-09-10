"""
tests/test_auth_api.py — Integration tests for the authentication endpoints.

Endpoints covered:
  POST /api/auth/login/
  POST /api/auth/refresh/
  POST /api/auth/logout/
  GET  /api/auth/me/

Scenarios:
  - Successful login returns tokens + user data
  - Login with wrong password returns 400
  - Login with unknown identifier returns 400 (no user disclosure)
  - Locked account (non-admin) returns 403
  - Admin login bypasses lockout
  - Failed attempts increment counter atomically
  - Three failures lock the account
  - Refresh with valid cookie succeeds
  - Refresh with missing token returns 400
  - Refresh with invalid token returns 401
  - Logout blacklists refresh token
  - /me/ with valid token returns user data
  - /me/ without token returns 401
"""
import pytest
from django.contrib.auth import get_user_model
from django.db.models import Model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def _make_user(role, username, phone=None, password="Pass123!"):
    u = User.__new__(User)
    User.__init__(u, username=username, role=role, phone_number=phone)
    u.set_password(password)
    Model.save(u)
    return u


# ─────────────────────────────────────────────────────────────────────────────
# Login
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLoginApiView:
    def test_successful_login_by_phone(self, student_user):
        """Login with phone number + correct password returns 200 with tokens."""
        client = APIClient()
        resp = client.post("/api/auth/login/", {
            "identifier": "9100000001",
            "password": "StudentPass1!",
        }, format="json")
        assert resp.status_code == 200
        assert "access" in resp.data
        assert "refresh" in resp.data
        assert resp.data["user"]["role"] == "student"

    def test_successful_login_by_username(self, admin_user):
        """Login with username + correct password returns 200 with tokens."""
        client = APIClient()
        resp = client.post("/api/auth/login/", {
            "identifier": "admin",
            "password": "AdminPass1!",
        }, format="json")
        assert resp.status_code == 200
        assert "access" in resp.data

    def test_login_sets_refresh_cookie(self, student_user):
        """Successful login must set an httpOnly refresh_token cookie."""
        client = APIClient()
        resp = client.post("/api/auth/login/", {
            "identifier": "9100000001",
            "password": "StudentPass1!",
        }, format="json")
        assert "refresh_token" in resp.cookies

    def test_wrong_password_returns_400(self, student_user):
        """Wrong password must return 400."""
        client = APIClient()
        resp = client.post("/api/auth/login/", {
            "identifier": "9100000001",
            "password": "WRONGPASSWORD",
        }, format="json")
        assert resp.status_code == 400
        assert "Invalid credentials" in resp.data.get("detail", "")

    def test_unknown_identifier_returns_400(self):
        """An identifier that matches no user returns 400 (no user disclosure)."""
        client = APIClient()
        resp = client.post("/api/auth/login/", {
            "identifier": "nobody_exists",
            "password": "whatever",
        }, format="json")
        assert resp.status_code == 400
        assert "Invalid credentials" in resp.data.get("detail", "")

    def test_locked_account_returns_403(self, student_user):
        """A locked non-admin account must return 403 immediately."""
        User.objects.filter(pk=student_user.pk).update(is_locked=True)
        client = APIClient()
        resp = client.post("/api/auth/login/", {
            "identifier": "9100000001",
            "password": "StudentPass1!",
        }, format="json")
        assert resp.status_code == 403
        assert "locked" in resp.data.get("detail", "").lower()

    def test_admin_locked_can_still_login(self, admin_user):
        """Admin account must be able to login even if is_locked=True."""
        User.objects.filter(pk=admin_user.pk).update(is_locked=True)
        client = APIClient()
        resp = client.post("/api/auth/login/", {
            "identifier": "admin",
            "password": "AdminPass1!",
        }, format="json")
        assert resp.status_code == 200

    def test_failed_attempts_increment_on_bad_password(self, student_user):
        """Each wrong password atomically increments failed_login_attempts."""
        client = APIClient()
        client.post("/api/auth/login/", {"identifier": "9100000001", "password": "bad"}, format="json")
        client.post("/api/auth/login/", {"identifier": "9100000001", "password": "bad"}, format="json")
        student_user.refresh_from_db()
        assert student_user.failed_login_attempts == 2

    def test_three_failures_lock_account(self, student_user):
        """After 3 bad passwords the account must be marked is_locked=True."""
        client = APIClient()
        for _ in range(3):
            client.post("/api/auth/login/", {"identifier": "9100000001", "password": "bad"}, format="json")
        student_user.refresh_from_db()
        assert student_user.is_locked is True

    def test_successful_login_resets_attempts(self, student_user):
        """Successful login must reset failed_login_attempts to 0."""
        User.objects.filter(pk=student_user.pk).update(failed_login_attempts=2)
        client = APIClient()
        client.post("/api/auth/login/", {"identifier": "9100000001", "password": "StudentPass1!"}, format="json")
        student_user.refresh_from_db()
        assert student_user.failed_login_attempts == 0

    def test_admin_wrong_password_does_not_increment_attempts(self, admin_user):
        """Admin's failed_login_attempts must NOT be incremented (admins are never locked)."""
        client = APIClient()
        client.post("/api/auth/login/", {"identifier": "admin", "password": "bad"}, format="json")
        admin_user.refresh_from_db()
        assert admin_user.failed_login_attempts == 0

    def test_empty_identifier_returns_400(self):
        """Empty identifier string returns 400."""
        client = APIClient()
        resp = client.post("/api/auth/login/", {"identifier": "", "password": "x"}, format="json")
        assert resp.status_code == 400

    def test_missing_body_returns_400(self):
        """Missing body returns 400."""
        client = APIClient()
        resp = client.post("/api/auth/login/", {}, format="json")
        assert resp.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# Refresh
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRefreshApiView:
    def test_refresh_with_valid_cookie_returns_new_access(self, student_user):
        """A valid refresh cookie must produce a new access token."""
        client = APIClient()
        # Login to set cookie
        login_resp = client.post("/api/auth/login/", {
            "identifier": "9100000001", "password": "StudentPass1!"
        }, format="json")
        assert login_resp.status_code == 200
        resp = client.post("/api/auth/refresh/", {}, format="json")
        assert resp.status_code == 200
        assert "access" in resp.data

    def test_refresh_without_token_returns_400(self):
        """Refresh with no cookie and no body returns 400."""
        client = APIClient()
        resp = client.post("/api/auth/refresh/", {}, format="json")
        assert resp.status_code == 400

    def test_refresh_with_invalid_token_returns_401(self):
        """Tampered/invalid refresh token returns 401."""
        client = APIClient()
        client.cookies["refresh_token"] = "not.a.valid.jwt"
        resp = client.post("/api/auth/refresh/", {}, format="json")
        assert resp.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# Logout
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLogoutApiView:
    def test_logout_deletes_cookie(self, student_user):
        """Logout must delete the refresh_token cookie."""
        client = APIClient()
        client.post("/api/auth/login/", {
            "identifier": "9100000001", "password": "StudentPass1!"
        }, format="json")
        resp = client.post("/api/auth/logout/", {}, format="json")
        assert resp.status_code == 200
        # After logout the cookie value must be empty or cleared
        cookie_val = resp.cookies.get("refresh_token")
        assert cookie_val is None or cookie_val.value == ""

    def test_logout_without_cookie_still_returns_200(self):
        """Logout even without a cookie returns 200 (idempotent)."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        u = _make_user(User.ROLE_ADMIN, username="admin_logout")
        client = APIClient()
        token = RefreshToken.for_user(u)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token.access_token)}")
        resp = client.post("/api/auth/logout/", {}, format="json")
        assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# Me
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestMeApiView:
    def test_me_with_valid_token_returns_user_data(self, auth_client, student_user):
        resp = auth_client.get("/api/auth/me/")
        assert resp.status_code == 200
        assert resp.data["role"] == "student"

    def test_me_without_token_returns_401(self):
        client = APIClient()
        resp = client.get("/api/auth/me/")
        assert resp.status_code == 401
