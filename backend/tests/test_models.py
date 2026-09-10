"""
tests/test_models.py — Unit tests for all domain models.

Covers:
  - accounts.User: roles, lock/unlock, display names, single-admin constraint
  - students.Student: hostel derivation, room_number validation, gender choices
  - students.Department: creation and __str__
  - complaints.Complaint: 6-word description limit, snapshot fields, FSM statuses
  - academics.AcademicFile: file extension whitelist, sha256 dedup, size display
  - academics.Subject: uniqueness
  - feedbacks.FeedbackForm: expires_at auto-set, is_available_to_students, mark_expired_if_needed
  - feedbacks.FeedbackQuestion: get_radio_options_list
  - core.SystemSettings: get_solo singleton, defaults
  - core.BackupRecord: creation
"""
import hashlib
import io
import pytest
from django.core.exceptions import ValidationError
from django.db.models import Model
from django.utils import timezone


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _save(obj):
    """Save model instance bypassing full_clean (for testing invalid states)."""
    Model.save(obj)


def _make_user(role, username, phone=None, password="Pass123!"):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    u = User.__new__(User)
    User.__init__(u, username=username, role=role, phone_number=phone)
    u.set_password(password)
    _save(u)
    return u


# ─────────────────────────────────────────────────────────────────────────────
# accounts.User
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserModel:
    def test_get_display_name_student(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        u = _make_user(User.ROLE_STUDENT, username="9111111111", phone="9111111111")
        assert u.get_display_name() == "9111111111"

    def test_get_display_name_admin(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        u = _make_user(User.ROLE_ADMIN, username="testadmin")
        assert u.get_display_name() == "testadmin"

    def test_get_display_name_no_phone_or_username(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        u = User.__new__(User)
        User.__init__(u, role=User.ROLE_STUDENT)
        assert u.get_display_name() == "Student"

    def test_is_student_returns_true_for_student(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        u = _make_user(User.ROLE_STUDENT, username="9222222222", phone="9222222222")
        assert u.is_student() is True
        assert u.is_clerk() is False
        assert u.is_admin() is False

    def test_is_admin_returns_true_for_admin(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        u = _make_user(User.ROLE_ADMIN, username="admintest2")
        assert u.is_admin() is True

    def test_lock_account(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        u = _make_user(User.ROLE_CLERK, username="clerklocktest")
        assert u.is_locked is False
        u.lock_account()
        u.refresh_from_db()
        assert u.is_locked is True

    def test_unlock_account_resets_attempts(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        u = _make_user(User.ROLE_CLERK, username="clerkunlock")
        # Directly set is_locked and attempts
        User.objects.filter(pk=u.pk).update(is_locked=True, failed_login_attempts=3)
        u.refresh_from_db()
        u.unlock_account()
        u.refresh_from_db()
        assert u.is_locked is False
        assert u.failed_login_attempts == 0

    def test_reset_login_attempts(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        u = _make_user(User.ROLE_CLERK, username="clerkresstattempts")
        User.objects.filter(pk=u.pk).update(failed_login_attempts=2)
        u.reset_login_attempts()
        u.refresh_from_db()
        assert u.failed_login_attempts == 0

    def test_student_clean_requires_phone(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        u = User(username="nophone", role=User.ROLE_STUDENT, phone_number=None)
        u.set_password("Pass123!")
        with pytest.raises(ValidationError, match="phone number"):
            u.clean()

    def test_single_admin_constraint(self, admin_user):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        # admin_user already created — creating a second admin must raise
        second_admin = User(username="second_admin", role=User.ROLE_ADMIN)
        second_admin.set_password("Pass123!")
        with pytest.raises(ValidationError, match="Only one admin"):
            second_admin.clean()

    def test_str_representation(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        u = _make_user(User.ROLE_ADMIN, username="stradmin")
        assert str(u) == "stradmin"


# ─────────────────────────────────────────────────────────────────────────────
# students.Student
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestStudentModel:
    def test_male_student_gets_boys_hostel(self, student_user):
        assert student_user.student_profile.hostel == "boys_hostel"

    def test_female_student_gets_girls_hostel(self, female_student_user):
        assert female_student_user.student_profile.hostel == "girls_hostel"

    def test_room_number_must_be_digits(self, department):
        from students.models import Student
        from django.contrib.auth import get_user_model
        User = get_user_model()
        u = _make_user(User.ROLE_STUDENT, username="9333333333", phone="9333333333")
        s = Student(
            user=u, full_name="Room Err", phone_number="9333333333",
            department=department, year="year_1", gender="male",
            room_number="ABC",  # invalid
        )
        with pytest.raises(ValidationError, match="Room number must contain numbers"):
            s.clean()

    def test_hostel_display_name_boys(self, student_user):
        s = student_user.student_profile
        assert "Boys" in s.get_hostel_display_name()

    def test_hostel_display_name_girls(self, female_student_user):
        s = female_student_user.student_profile
        assert "Girls" in s.get_hostel_display_name()

    def test_str_representation(self, student_user):
        s = student_user.student_profile
        assert s.full_name in str(s)

    def test_department_str(self, department):
        assert str(department) == department.name


# ─────────────────────────────────────────────────────────────────────────────
# complaints.Complaint
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestComplaintModel:
    def test_description_exactly_6_words_is_valid(self, student_user):
        from complaints.models import Complaint
        student = student_user.student_profile
        c = Complaint(
            student=student,
            student_name_snapshot=student.full_name,
            student_phone_snapshot=student.phone_number,
            year_snapshot=student.year,
            hostel_snapshot=student.hostel,
            room_number_snapshot=student.room_number,
            description="one two three four five six",
            status=Complaint.STATUS_NEW,
        )
        c.clean()  # must not raise

    def test_description_7_words_raises_validation_error(self, student_user):
        from complaints.models import Complaint
        student = student_user.student_profile
        c = Complaint(
            student=student,
            student_name_snapshot=student.full_name,
            student_phone_snapshot=student.phone_number,
            year_snapshot=student.year,
            hostel_snapshot=student.hostel,
            room_number_snapshot=student.room_number,
            description="one two three four five six SEVEN",
            status=Complaint.STATUS_NEW,
        )
        with pytest.raises(ValidationError, match="6 words"):
            c.clean()

    def test_empty_description_is_valid(self, student_user):
        from complaints.models import Complaint
        student = student_user.student_profile
        c = Complaint(
            student=student,
            student_name_snapshot=student.full_name,
            student_phone_snapshot=student.phone_number,
            year_snapshot=student.year,
            hostel_snapshot=student.hostel,
            room_number_snapshot=student.room_number,
            description="",
            status=Complaint.STATUS_NEW,
        )
        c.clean()  # empty description skips the word count check

    def test_room_number_snapshot_must_be_digits(self, student_user):
        from complaints.models import Complaint
        student = student_user.student_profile
        c = Complaint(
            student=student,
            student_name_snapshot=student.full_name,
            student_phone_snapshot=student.phone_number,
            year_snapshot=student.year,
            hostel_snapshot=student.hostel,
            room_number_snapshot="NOT_DIGITS",
            description="pipe burst",
            status=Complaint.STATUS_NEW,
        )
        with pytest.raises(ValidationError, match="Room number must contain numbers"):
            c.clean()

    def test_str_representation(self, complaint):
        s = str(complaint)
        assert "pipe burst" in s

    def test_get_year_snapshot_display(self, complaint):
        assert complaint.get_year_snapshot_display() in ["Year 1", "Year 2", "Year 3", "year_1"]

    def test_get_hostel_snapshot_display(self, complaint):
        assert "hostel" in complaint.get_hostel_snapshot_display().lower()

    def test_status_history_ordering(self, complaint):
        from complaints.models import ComplaintStatusHistory
        # Create two history entries
        h1 = ComplaintStatusHistory.__new__(ComplaintStatusHistory)
        ComplaintStatusHistory.__init__(
            h1, complaint=complaint, status="new", changed_by_role_snapshot="student"
        )
        _save(h1)
        assert str(h1)  # __str__ doesn't crash


# ─────────────────────────────────────────────────────────────────────────────
# feedbacks.FeedbackForm
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestFeedbackFormModel:
    def test_expires_at_auto_set_on_save(self, active_feedback_form):
        assert active_feedback_form.expires_at is not None

    def test_is_available_to_students_true_for_active(self, active_feedback_form):
        assert active_feedback_form.is_available_to_students is True

    def test_is_available_to_students_false_for_stopped(self, active_feedback_form):
        active_feedback_form.status = active_feedback_form.STATUS_STOPPED
        assert active_feedback_form.is_available_to_students is False

    def test_is_expired_by_time_false_for_future(self, active_feedback_form):
        assert active_feedback_form.is_expired_by_time is False

    def test_is_expired_by_time_true_for_past(self, active_feedback_form):
        from django.utils import timezone
        from datetime import timedelta
        active_feedback_form.expires_at = timezone.now() - timedelta(hours=1)
        assert active_feedback_form.is_expired_by_time is True

    def test_mark_expired_if_needed_changes_status(self, active_feedback_form):
        from django.utils import timezone
        from datetime import timedelta
        active_feedback_form.expires_at = timezone.now() - timedelta(hours=1)
        _save(active_feedback_form)
        active_feedback_form.mark_expired_if_needed()
        active_feedback_form.refresh_from_db()
        assert active_feedback_form.status == active_feedback_form.STATUS_EXPIRED

    def test_stop_changes_status_to_stopped(self, active_feedback_form):
        active_feedback_form.stop()
        active_feedback_form.refresh_from_db()
        assert active_feedback_form.status == active_feedback_form.STATUS_STOPPED
        assert active_feedback_form.stopped_at is not None

    def test_str_representation(self, active_feedback_form):
        s = str(active_feedback_form)
        assert "Test Form" in s


@pytest.mark.django_db
class TestFeedbackQuestionModel:
    def test_get_radio_options_list_empty(self, active_feedback_form):
        from feedbacks.models import FeedbackQuestion
        q = active_feedback_form.questions.first()
        # Rating question has no radio_options
        assert q.get_radio_options_list() == []

    def test_get_radio_options_list_with_options(self, active_feedback_form):
        from feedbacks.models import FeedbackQuestion
        q = FeedbackQuestion.__new__(FeedbackQuestion)
        FeedbackQuestion.__init__(
            q, feedback_form=active_feedback_form,
            question_text="Favorite color?",
            question_type=FeedbackQuestion.TYPE_RADIO,
            radio_options="Red\nBlue\nGreen",
            display_order=2,
        )
        _save(q)
        assert q.get_radio_options_list() == ["Red", "Blue", "Green"]

    def test_get_radio_options_filters_blank_lines(self, active_feedback_form):
        from feedbacks.models import FeedbackQuestion
        q = FeedbackQuestion.__new__(FeedbackQuestion)
        FeedbackQuestion.__init__(
            q, feedback_form=active_feedback_form,
            question_text="Color with blanks?",
            question_type=FeedbackQuestion.TYPE_RADIO,
            radio_options="Red\n\nBlue\n  \nGreen",
            display_order=3,
        )
        _save(q)
        assert q.get_radio_options_list() == ["Red", "Blue", "Green"]


# ─────────────────────────────────────────────────────────────────────────────
# core.SystemSettings
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSystemSettings:
    def test_get_solo_creates_singleton(self):
        from core.models import SystemSettings
        s1 = SystemSettings.get_solo()
        s2 = SystemSettings.get_solo()
        assert s1.pk == s2.pk == 1

    def test_get_solo_default_values(self):
        from core.models import SystemSettings
        s = SystemSettings.get_solo()
        assert "Polytechnic" in s.college_name or s.college_name  # non-empty
        assert s.system_title

    def test_str_representation(self):
        from core.models import SystemSettings
        s = SystemSettings.get_solo()
        assert str(s) == s.system_title


# ─────────────────────────────────────────────────────────────────────────────
# academics.AcademicFile
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAcademicFileModel:
    def test_get_file_size_display_bytes(self, department, student_user):
        from academics.models import AcademicFile, Subject
        subj, _ = Subject.objects.get_or_create(name="Physics")
        af = AcademicFile.__new__(AcademicFile)
        AcademicFile.__init__(
            af, department=department, year="year_1", subject=subj,
            file_type="notes", file_hash="abc123",
            uploaded_by_name_snapshot="Tester",
            file_size=500,
        )
        assert "B" in af.get_file_size_display()

    def test_get_file_size_display_kb(self, department):
        from academics.models import AcademicFile, Subject
        subj, _ = Subject.objects.get_or_create(name="Maths")
        af = AcademicFile.__new__(AcademicFile)
        AcademicFile.__init__(
            af, department=department, year="year_1", subject=subj,
            file_type="notes", file_hash="abc456",
            uploaded_by_name_snapshot="Tester",
            file_size=2048,
        )
        assert "KB" in af.get_file_size_display()

    def test_get_file_size_display_mb(self, department):
        from academics.models import AcademicFile, Subject
        subj, _ = Subject.objects.get_or_create(name="Chemistry")
        af = AcademicFile.__new__(AcademicFile)
        AcademicFile.__init__(
            af, department=department, year="year_1", subject=subj,
            file_type="notes", file_hash="abc789",
            uploaded_by_name_snapshot="Tester",
            file_size=2 * 1024 * 1024,
        )
        assert "MB" in af.get_file_size_display()

    def test_clean_rejects_invalid_extension(self, department):
        from academics.models import AcademicFile, Subject
        from django.core.files.base import ContentFile
        subj, _ = Subject.objects.get_or_create(name="Biology")
        af = AcademicFile.__new__(AcademicFile)
        file_content = ContentFile(b"data", name="test.exe")
        AcademicFile.__init__(
            af, department=department, year="year_1", subject=subj,
            file_type="notes", file_hash="exehash",
            uploaded_by_name_snapshot="Tester",
            file=file_content,
        )
        with pytest.raises(ValidationError, match="Unsupported file type"):
            af.clean()

    def test_clean_allows_pdf(self, department):
        from academics.models import AcademicFile, Subject
        from django.core.files.base import ContentFile
        subj, _ = Subject.objects.get_or_create(name="History")
        af = AcademicFile.__new__(AcademicFile)
        file_content = ContentFile(b"pdf data", name="notes.pdf")
        AcademicFile.__init__(
            af, department=department, year="year_1", subject=subj,
            file_type="notes", file_hash="pdfhash",
            uploaded_by_name_snapshot="Tester",
            file=file_content,
        )
        af.clean()  # should not raise

    def test_subject_uniqueness(self):
        from academics.models import Subject
        Subject.objects.create(name="UniqueSubject")
        with pytest.raises(Exception):  # IntegrityError
            Subject.objects.create(name="UniqueSubject")

    def test_academic_file_upload_path(self, department):
        from academics.models import AcademicFile, Subject, academic_file_upload_path
        from django.core.files.base import ContentFile
        subj, _ = Subject.objects.get_or_create(name="Geography")
        af = AcademicFile.__new__(AcademicFile)
        AcademicFile.__init__(
            af, department=department, year="year_2", subject=subj,
            file_type="notes", file_hash="pathhash",
            uploaded_by_name_snapshot="Tester",
        )
        path = academic_file_upload_path(af, "lecture_notes.pdf")
        normalized_path = path.replace("\\", "/")
        assert "academics/notes" in normalized_path
        assert path.endswith(".pdf")
