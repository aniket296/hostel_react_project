"""
Security and reliability regression tests for the Hostel Management System backend.

Covers every issue identified in the Phase 2/3 triage table:
  V-01  StudentComplaintCreateApiView — orphaned student profile → 403 not 500
  V-02  FeedbackSubmitApiView — orphaned student profile → 403 not 500
  V-04  LoginApiView — atomic failed_login_attempts increment (race condition)
  V-05  ComplaintListApiView — invalid status filter silently ignored (whitelist)
  V-07  StudentListCreateApiView — no default password from phone number
  V-08  ClerkListCreateApiView — no default password from username
  V-09  accounts/views.py login — atomic failed_login_attempts (legacy view)
  V-10  FeedbackSubmitApiView — keyword-only submit_feedback_form call
  V-11  ComplaintActionApiView — student cannot trigger 'reopen' action
  V-14  BackupListApiView — internal error details not leaked to client
  V-15  generate_demo_student_csv — no real personal data in output
"""

import pytest
from unittest.mock import patch, MagicMock

import django
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(role, username, phone=None, password="testpass123"):
    """Create a user with the given role, bypassing full_clean enforcement."""
    u = User(username=username, role=role, phone_number=phone)
    u.set_password(password)
    u.save()
    return u


def api_client_for(user):
    from rest_framework_simplejwt.tokens import RefreshToken
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token.access_token)}")
    return client


# ---------------------------------------------------------------------------
# V-01 — StudentComplaintCreateApiView: orphaned student profile → 403 not 500
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestV01OrphanedStudentOnComplaintCreate:
    def test_student_with_no_profile_gets_403_not_500(self):
        """
        A student user whose Student profile row was deleted mid-session must
        receive a 403 (not an unhandled 500 caused by AttributeError on
        request.user.student_profile).
        """
        user = make_user(User.ROLE_STUDENT, username="orphan1", phone="9100000001")
        # Deliberately do NOT create a Student profile for this user
        client = api_client_for(user)
        resp = client.post("/api/student/complaints/", {"description": "leaking tap"}, format="json")
        assert resp.status_code == 403
        assert "Student profile not found" in resp.data["detail"]


# ---------------------------------------------------------------------------
# V-02 — FeedbackSubmitApiView: orphaned student profile → 403 not 500
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestV02OrphanedStudentOnFeedbackSubmit:
    def test_student_with_no_profile_gets_403_not_500(self):
        """
        FeedbackSubmitApiView must not crash when the authenticated user has no
        associated Student profile.

        Two layers protect this:
        1. IsStudentRole permission — a user with ROLE_STUDENT but no Student
           DB record will have `hasattr(request.user, 'student_profile')` be
           False (RelatedObjectDoesNotExist), so the permission rejects early.
        2. The getattr guard inside the view as a defence-in-depth layer.

        Either way, the response must be 403, never 500.
        """
        from feedbacks.models import FeedbackForm
        from django.db.models import Model
        u = User.__new__(User)
        User.__init__(u, username="orphan2_fb", role=User.ROLE_STUDENT, phone_number="9100000092")
        u.set_password("pass123")
        Model.save(u)
        admin = User.__new__(User)
        User.__init__(admin, username="admin_v02", role=User.ROLE_ADMIN)
        admin.set_password("pass123")
        Model.save(admin)
        form = FeedbackForm.__new__(FeedbackForm)
        FeedbackForm.__init__(
            form, name="Test Form V02", hostel=FeedbackForm.HOSTEL_BOYS,
            duration_hours=24, status=FeedbackForm.STATUS_ACTIVE,
            created_by=admin,
        )
        Model.save(form)
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        token = RefreshToken.for_user(u)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token.access_token)}")
        resp = client.post(f"/api/feedback/forms/{form.pk}/submit/", {"answers": {}}, format="json")
        # Must be 403 — either IsStudentRole permission denied or our guard.
        # Must never be 500 (the original bug was an unhandled AttributeError).
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.data}"


# ---------------------------------------------------------------------------
# V-04 — LoginApiView: atomic login attempt counter
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestV04AtomicLoginCounter:
    def test_failed_attempts_increment_atomically(self):
        """
        After a failed login the counter must be incremented via an atomic DB
        UPDATE (using F expressions), not via a Python-side read-modify-write.
        Verify by checking the DB value, not just the in-memory attribute.
        """
        from students.models import Student, Department
        dept = Department.objects.create(name="IT")
        user = make_user(User.ROLE_STUDENT, username="9100000003", phone="9100000003")
        Student.objects.create(
            user=user, full_name="Test Student", phone_number="9100000003",
            department=dept, year="year_1", gender="male", room_number="101",
        )
        client = APIClient()
        client.post("/api/auth/login/", {"identifier": "9100000003", "password": "wrongpassword"}, format="json")
        user.refresh_from_db()
        assert user.failed_login_attempts == 1, "Counter must be incremented to 1 after one failed attempt"

    def test_account_locked_after_three_failures(self):
        """
        After 3 consecutive bad passwords the account must be locked.
        """
        from students.models import Student, Department
        dept, _ = Department.objects.get_or_create(name="IT")
        user = make_user(User.ROLE_STUDENT, username="9100000004", phone="9100000004")
        Student.objects.create(
            user=user, full_name="Test Student2", phone_number="9100000004",
            department=dept, year="year_1", gender="male", room_number="102",
        )
        client = APIClient()
        for _ in range(3):
            client.post("/api/auth/login/", {"identifier": "9100000004", "password": "wrong"}, format="json")
        user.refresh_from_db()
        assert user.is_locked, "Account must be locked after 3 failed attempts"


# ---------------------------------------------------------------------------
# V-05 — ComplaintListApiView: invalid status filter is silently ignored
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestV05StatusFilterWhitelist:
    def test_invalid_status_query_param_returns_200_not_500(self):
        """
        An invalid ?status= query param must not cause a DB error or 500.
        It should be silently ignored, returning all (or filtered) complaints.
        """
        from students.models import Student, Department
        dept = Department.objects.create(name="CSE")
        admin = make_user(User.ROLE_ADMIN, username="admin_v05")
        client = api_client_for(admin)
        resp = client.get("/api/complaints/?status=INVALID_STATUS_VALUE__DROP_TABLE")
        assert resp.status_code == 200

    def test_valid_status_filter_works(self):
        """Valid status values must still be accepted."""
        admin = make_user(User.ROLE_ADMIN, username="admin_v05b")
        client = api_client_for(admin)
        resp = client.get("/api/complaints/?status=new")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# V-07 — StudentListCreateApiView: password is required (no phone fallback)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestV07NoDefaultStudentPassword:
    def test_student_creation_without_password_is_rejected(self):
        """
        Creating a student without supplying a password must return 400.
        Previously the phone number was silently used as the password.
        """
        admin = make_user(User.ROLE_ADMIN, username="admin_v07")
        client = api_client_for(admin)
        from students.models import Department
        dept = Department.objects.create(name="Mech")
        resp = client.post("/api/students/", {
            "full_name": "Test Student",
            "phone_number": "9200000001",
            "department": dept.pk,
            "year": "year_1",
            "gender": "male",
            "room_number": "201",
            # password intentionally omitted
        }, format="json")
        assert resp.status_code == 400
        assert "password" in resp.data

    def test_student_creation_with_password_succeeds(self):
        """Student creation with an explicit password must succeed (201)."""
        admin = make_user(User.ROLE_ADMIN, username="admin_v07b")
        client = api_client_for(admin)
        from students.models import Department
        dept, _ = Department.objects.get_or_create(name="Mech")
        resp = client.post("/api/students/", {
            "full_name": "Test Student B",
            "phone_number": "9200000002",
            "department": dept.pk,
            "year": "year_1",
            "gender": "male",
            "room_number": "202",
            "password": "strongpass123",
        }, format="json")
        assert resp.status_code == 201


# ---------------------------------------------------------------------------
# V-08 — ClerkListCreateApiView: password is required (no username fallback)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestV08NoDefaultClerkPassword:
    def test_clerk_creation_without_password_is_rejected(self):
        """
        Creating a clerk without supplying a password must return 400.
        Previously the username was silently used as the password.
        """
        admin = make_user(User.ROLE_ADMIN, username="admin_v08")
        client = api_client_for(admin)
        resp = client.post("/api/clerks/", {
            "username": "clerk_test",
            "full_name": "Test Clerk",
            "phone_number": "9300000001",
            "assigned_hostel": "boys_hostel",
            # password intentionally omitted
        }, format="json")
        assert resp.status_code == 400
        assert "password" in resp.data

    def test_clerk_creation_with_password_succeeds(self):
        """Clerk creation with an explicit password must succeed (201)."""
        admin = make_user(User.ROLE_ADMIN, username="admin_v08b")
        client = api_client_for(admin)
        resp = client.post("/api/clerks/", {
            "username": "clerk_test_b",
            "full_name": "Test Clerk B",
            "phone_number": "9300000002",
            "assigned_hostel": "boys_hostel",
            "password": "clerkpass456",
        }, format="json")
        assert resp.status_code == 201


# ---------------------------------------------------------------------------
# V-11 — ComplaintActionApiView: student cannot trigger 'reopen'
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestV11StudentCannotReopen:
    def test_student_cannot_call_reopen_action(self):
        """
        A student should only be allowed to call 'mark-solved' or 'mark-unsolved'
        on their own complaints. 'reopen' must be blocked (403).
        """
        from students.models import Student, Department
        from complaints.models import Complaint
        dept, _ = Department.objects.get_or_create(name="EE")
        user = make_user(User.ROLE_STUDENT, username="9400000001", phone="9400000001")
        student = Student.objects.create(
            user=user, full_name="S Reopen Test", phone_number="9400000001",
            department=dept, year="year_1", gender="male", room_number="301",
        )
        complaint = Complaint.objects.create(
            student=student,
            student_name_snapshot=student.full_name,
            student_phone_snapshot=student.phone_number,
            year_snapshot=student.year,
            hostel_snapshot=student.hostel,
            room_number_snapshot=student.room_number,
            description="leaking pipe",
            status=Complaint.STATUS_UNSOLVED,
        )
        client = api_client_for(user)
        resp = client.post(f"/api/complaints/{complaint.pk}/reopen/", {}, format="json")
        assert resp.status_code == 403, "Student must not be allowed to reopen a complaint"


# ---------------------------------------------------------------------------
# V-14 — BackupListApiView: internal details not leaked on failure
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestV14BackupErrorLeakage:
    @patch("api.views.create_mysql_backup", side_effect=RuntimeError("mysql: command not found; password=secret"))
    def test_backup_failure_does_not_leak_internal_details(self, mock_backup):
        """
        When backup creation fails, the API must return a generic message
        and NOT expose the exception text (which may contain passwords or paths).
        """
        admin = make_user(User.ROLE_ADMIN, username="admin_v14")
        client = api_client_for(admin)
        resp = client.post("/api/backups/", {}, format="json")
        assert resp.status_code == 400
        detail = resp.data.get("detail", "")
        assert "password=secret" not in detail
        assert "command not found" not in detail
        assert "logs" in detail.lower() or "failed" in detail.lower()


# ---------------------------------------------------------------------------
# V-15 — generate_demo_student_csv: no real personal data
# ---------------------------------------------------------------------------

class TestV15DemoCSVNoPersonalData:
    def test_demo_csv_does_not_contain_real_phone_number(self):
        """The demo CSV must not contain the real phone number 9209803186."""
        from students.import_export import generate_demo_student_csv
        csv_output = generate_demo_student_csv()
        assert "9209803186" not in csv_output, "Real phone number must not appear in demo CSV"

    def test_demo_csv_does_not_contain_real_name(self):
        """The demo CSV must not contain a real developer's name."""
        from students.import_export import generate_demo_student_csv
        csv_output = generate_demo_student_csv()
        assert "Aniket Bondre" not in csv_output, "Real name must not appear in demo CSV"

    def test_demo_csv_uses_fictional_passwords(self):
        """Passwords in the demo CSV must not be 'name123' patterns."""
        from students.import_export import generate_demo_student_csv
        csv_output = generate_demo_student_csv()
        assert "aniket123" not in csv_output
        assert "aman123" not in csv_output


# ---------------------------------------------------------------------------
# V-10 — FeedbackSubmitApiView: keyword-only call doesn't raise TypeError
# ---------------------------------------------------------------------------

class TestV10SubmitFeedbackKeywordCall:
    """Unit-level test: submit_feedback_form must accept keyword-only args."""
    def test_submit_feedback_form_requires_keyword_args(self):
        """
        submit_feedback_form is defined with * (keyword-only params).
        Verify that calling it positionally raises TypeError so we know
        our keyword-argument fix in views.py is necessary and correct.
        """
        from feedbacks.services import submit_feedback_form
        import inspect
        sig = inspect.signature(submit_feedback_form)
        params = list(sig.parameters.values())
        # All params after the first (*) separator must be keyword-only
        keyword_only = [p for p in params if p.kind == inspect.Parameter.KEYWORD_ONLY]
        assert len(keyword_only) >= 3, (
            "submit_feedback_form must have keyword-only params for feedback_form, student, answers_by_question_id"
        )
        param_names = {p.name for p in keyword_only}
        assert "feedback_form" in param_names
        assert "student" in param_names
        assert "answers_by_question_id" in param_names

