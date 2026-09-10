"""
Root conftest.py — shared fixtures for the entire test suite.

Settings are loaded from hostel_management_system.test_settings via pytest.ini.
This file only provides reusable fixtures.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# ─── Low-level user factory ──────────────────────────────────────────────────

def _create_user(role, username, phone=None, password="Testpass123!", **kwargs):
    """
    Create a User bypassing the single-admin constraint in User.clean().
    We call save(update_fields=...) after creation to avoid full_clean on the
    admin check, since test isolation means we never have two admins concurrently.
    """
    u = User.__new__(User)
    User.__init__(u, username=username, role=role, phone_number=phone, **kwargs)
    u.set_password(password)
    # Bypass full_clean for test speed; individual tests exercise clean() separately
    from django.db.models import Model
    Model.save(u)
    return u


# ─── pytest fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def admin_user(db):
    return _create_user(User.ROLE_ADMIN, username="admin", password="AdminPass1!")


@pytest.fixture
def clerk_user(db):
    from clerks.models import Clerk
    u = _create_user(User.ROLE_CLERK, username="clerk1", phone="9000000099", password="ClerkPass1!")
    Clerk.objects.create(
        user=u, full_name="Test Clerk", phone_number="9000000099",
        assigned_hostel="boys_hostel",
    )
    return u


@pytest.fixture
def girl_clerk_user(db):
    from clerks.models import Clerk
    u = _create_user(User.ROLE_CLERK, username="clerk_girl", phone="9000000088", password="ClerkPass1!")
    Clerk.objects.create(
        user=u, full_name="Girl Clerk", phone_number="9000000088",
        assigned_hostel="girls_hostel",
    )
    return u


@pytest.fixture
def department(db):
    from students.models import Department
    dept, _ = Department.objects.get_or_create(name="Test Department")
    return dept


@pytest.fixture
def student_user(db, department):
    from students.models import Student
    from django.db.models import Model
    u = _create_user(User.ROLE_STUDENT, username="9100000001", phone="9100000001", password="StudentPass1!")
    s = Student.__new__(Student)
    Student.__init__(
        s, user=u, full_name="Test Student", phone_number="9100000001",
        department=department, year="year_1", gender="male", room_number="101",
        hostel="boys_hostel",
    )
    Model.save(s)
    return u


@pytest.fixture
def female_student_user(db, department):
    from students.models import Student
    from django.db.models import Model
    u = _create_user(User.ROLE_STUDENT, username="9100000002", phone="9100000002", password="StudentPass1!")
    s = Student.__new__(Student)
    Student.__init__(
        s, user=u, full_name="Female Student", phone_number="9100000002",
        department=department, year="year_1", gender="female", room_number="201",
        hostel="girls_hostel",
    )
    Model.save(s)
    return u


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(student_user):
    client = APIClient()
    token = RefreshToken.for_user(student_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token.access_token)}")
    return client


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    token = RefreshToken.for_user(admin_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token.access_token)}")
    return client


@pytest.fixture
def clerk_client(clerk_user):
    client = APIClient()
    token = RefreshToken.for_user(clerk_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token.access_token)}")
    return client


@pytest.fixture
def girl_clerk_client(girl_clerk_user):
    client = APIClient()
    token = RefreshToken.for_user(girl_clerk_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token.access_token)}")
    return client


@pytest.fixture
def complaint(db, student_user):
    from complaints.models import Complaint
    from django.db.models import Model
    student = student_user.student_profile
    c = Complaint.__new__(Complaint)
    Complaint.__init__(
        c,
        student=student,
        student_name_snapshot=student.full_name,
        student_phone_snapshot=student.phone_number,
        department_name_snapshot="",
        year_snapshot=student.year,
        hostel_snapshot=student.hostel,
        room_number_snapshot=student.room_number,
        description="pipe burst",
        status=Complaint.STATUS_NEW,
    )
    Model.save(c)
    return c


@pytest.fixture
def active_feedback_form(db, admin_user):
    from feedbacks.models import FeedbackForm, FeedbackQuestion
    from django.db.models import Model
    form = FeedbackForm(
        name="Test Form", hostel=FeedbackForm.HOSTEL_BOYS,
        duration_hours=24, status=FeedbackForm.STATUS_ACTIVE,
        created_by=admin_user,
    )
    form.save()
    q = FeedbackQuestion(
        feedback_form=form, question_text="Rate the cleanliness",
        question_type=FeedbackQuestion.TYPE_RATING, display_order=1,
    )
    q.save()
    return form
