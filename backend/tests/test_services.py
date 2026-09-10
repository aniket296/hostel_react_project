"""
tests/test_services.py — Unit and integration tests for service layers.

Covers:
  - complaints.services:
      create_student_complaint, create_status_history, assign_worker_and_start,
      mark_completed, mark_solved, mark_unsolved, reopen_unsolved
  - feedbacks.services:
      expire_feedback_forms_if_needed, validate_single_active_form_per_hostel,
      create_feedback_form_with_questions (rating, radio, text), delete_feedback_form,
      get_active_feedback_form_for_hostel, has_student_submitted_feedback,
      submit_feedback_form (validations, answers, duplicate protection),
      get_all_feedback_forms, stop_feedback_form,
      build_feedback_form_question_stats, build_feedback_analysis,
      export_feedback_analysis_csv
  - students.import_export:
      normalize_text, normalize_year, normalize_gender, derive_hostel_from_gender,
      get_or_create_department_by_name, parse_csv_file, parse_xlsx_file,
      validate_columns, validate_import_row
  - core.utils:
      _get_mysql_env, _build_mysql_connection_args, create_mysql_backup, restore_mysql_backup
"""
import io
from datetime import timedelta
from unittest.mock import patch, MagicMock
import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from openpyxl import Workbook

from complaints.models import Complaint, ComplaintStatusHistory
from complaints.services import (
    create_status_history, create_student_complaint,
    assign_worker_and_start, mark_completed, mark_solved,
    mark_unsolved, reopen_unsolved,
)
from feedbacks.models import FeedbackForm, FeedbackQuestion, FeedbackSubmission, FeedbackAnswer
from feedbacks.services import (
    expire_feedback_forms_if_needed, validate_single_active_form_per_hostel,
    create_feedback_form_with_questions, delete_feedback_form,
    get_active_feedback_form_for_hostel, has_student_submitted_feedback,
    submit_feedback_form, get_all_feedback_forms, stop_feedback_form,
    build_feedback_form_question_stats, build_feedback_analysis,
    export_feedback_analysis_csv,
)
from students.import_export import (
    normalize_text, normalize_year, normalize_gender, derive_hostel_from_gender,
    get_or_create_department_by_name, parse_csv_file, parse_xlsx_file,
    validate_columns, validate_import_row,
)
from core.utils import _get_mysql_env, _build_mysql_connection_args, create_mysql_backup, restore_mysql_backup

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# complaints.services
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestComplaintServices:
    def test_create_student_complaint(self, student_user):
        student = student_user.student_profile
        complaint = create_student_complaint(student=student, description="Tap broken")
        assert complaint.id is not None
        assert complaint.status == Complaint.STATUS_NEW
        assert complaint.student == student
        assert complaint.student_name_snapshot == student.full_name
        assert complaint.student_phone_snapshot == student.phone_number
        assert complaint.status_history.count() == 1
        history = complaint.status_history.first()
        assert history.status == Complaint.STATUS_NEW
        assert history.changed_by_user == student_user

    def test_assign_worker_and_start(self, complaint, clerk_user):
        assign_worker_and_start(complaint, worker_name="John Plumber", changed_by_user=clerk_user)
        complaint.refresh_from_db()
        assert complaint.status == Complaint.STATUS_IN_PROGRESS
        assert complaint.worker_name == "John Plumber"
        last_history = complaint.status_history.last()
        assert last_history.status == Complaint.STATUS_IN_PROGRESS
        assert last_history.changed_by_user == clerk_user

    def test_mark_completed(self, complaint, clerk_user):
        mark_completed(complaint, changed_by_user=clerk_user)
        complaint.refresh_from_db()
        assert complaint.status == Complaint.STATUS_COMPLETED
        assert complaint.completed_at is not None

    def test_mark_solved(self, complaint, student_user):
        mark_solved(complaint, changed_by_user=student_user)
        complaint.refresh_from_db()
        assert complaint.status == Complaint.STATUS_SOLVED
        assert complaint.solved_at is not None

    def test_mark_unsolved(self, complaint, student_user):
        mark_unsolved(complaint, changed_by_user=student_user)
        complaint.refresh_from_db()
        assert complaint.status == Complaint.STATUS_UNSOLVED
        assert complaint.unsolved_at is not None

    def test_reopen_unsolved_without_new_worker(self, complaint, clerk_user):
        mark_unsolved(complaint, changed_by_user=clerk_user)
        reopen_unsolved(complaint, changed_by_user=clerk_user)
        complaint.refresh_from_db()
        assert complaint.status == Complaint.STATUS_IN_PROGRESS
        assert complaint.unsolved_at is None

    def test_reopen_unsolved_with_new_worker(self, complaint, clerk_user):
        reopen_unsolved(complaint, changed_by_user=clerk_user, new_worker_name="New Plumber")
        complaint.refresh_from_db()
        assert complaint.status == Complaint.STATUS_IN_PROGRESS
        assert complaint.worker_name == "New Plumber"
        assert complaint.unsolved_at is None


# ─────────────────────────────────────────────────────────────────────────────
# feedbacks.services
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestFeedbackServices:
    def test_expire_feedback_forms_if_needed(self, admin_user):
        form = FeedbackForm.objects.create(
            name="Expiring Form",
            hostel=FeedbackForm.HOSTEL_GIRLS,
            duration_hours=12,
            status=FeedbackForm.STATUS_ACTIVE,
            created_by=admin_user,
        )
        form.expires_at = timezone.now() - timedelta(hours=1)
        form.save(update_fields=["expires_at"])

        expire_feedback_forms_if_needed()
        form.refresh_from_db()
        assert form.status == FeedbackForm.STATUS_EXPIRED

    def test_validate_single_active_form_per_hostel(self, active_feedback_form):
        # Boys hostel already has active form
        assert validate_single_active_form_per_hostel(FeedbackForm.HOSTEL_BOYS) is False
        # Girls hostel does not have active form
        assert validate_single_active_form_per_hostel(FeedbackForm.HOSTEL_GIRLS) is True

    def test_create_feedback_form_with_questions_success(self, admin_user):
        questions = [
            {"text": "Cleanliness rating", "type": "rating", "options": ""},
            {"text": "Meal quality", "type": "radio", "options": "Good\nAverage\nPoor"},
            {"text": "General comments", "type": "textarea", "options": ""},
        ]
        form = create_feedback_form_with_questions(
            admin_user=admin_user,
            name="Girls Weekly Review",
            hostel=FeedbackForm.HOSTEL_GIRLS,
            duration_hours=24,
            questions=questions,
        )
        assert form.id is not None
        assert form.questions.count() == 3
        q_radio = form.questions.get(question_type="radio")
        assert q_radio.get_radio_options_list() == ["Good", "Average", "Poor"]

    def test_create_feedback_form_duplicate_active_raises_value_error(self, admin_user, active_feedback_form):
        questions = [{"text": "Rate mess", "type": "rating"}]
        with pytest.raises(ValueError, match="already exists"):
            create_feedback_form_with_questions(
                admin_user=admin_user,
                name="Duplicate Boys Form",
                hostel=FeedbackForm.HOSTEL_BOYS,
                duration_hours=24,
                questions=questions,
            )

    def test_create_feedback_form_empty_questions_raises_value_error(self, admin_user):
        with pytest.raises(ValueError, match="At least one question is required"):
            create_feedback_form_with_questions(
                admin_user=admin_user,
                name="Empty Form",
                hostel=FeedbackForm.HOSTEL_GIRLS,
                duration_hours=24,
                questions=[],
            )

    def test_create_feedback_form_invalid_type_raises_value_error(self, admin_user):
        questions = [{"text": "Rate mess", "type": "invalid_type_here"}]
        with pytest.raises(ValueError, match="Invalid feedback question type"):
            create_feedback_form_with_questions(
                admin_user=admin_user,
                name="Bad Type Form",
                hostel=FeedbackForm.HOSTEL_GIRLS,
                duration_hours=24,
                questions=questions,
            )

    def test_create_feedback_form_radio_no_options_raises_value_error(self, admin_user):
        questions = [{"text": "Pick one", "type": "radio", "options": ""}]
        with pytest.raises(ValueError, match="must include at least one option"):
            create_feedback_form_with_questions(
                admin_user=admin_user,
                name="Bad Radio Form",
                hostel=FeedbackForm.HOSTEL_GIRLS,
                duration_hours=24,
                questions=questions,
            )

    def test_get_active_feedback_form_for_hostel(self, active_feedback_form):
        active = get_active_feedback_form_for_hostel(FeedbackForm.HOSTEL_BOYS)
        assert active == active_feedback_form
        assert get_active_feedback_form_for_hostel(FeedbackForm.HOSTEL_GIRLS) is None

    def test_has_student_submitted_feedback(self, active_feedback_form, student_user):
        student = student_user.student_profile
        assert has_student_submitted_feedback(active_feedback_form, student) is False
        FeedbackSubmission.objects.create(feedback_form=active_feedback_form, student=student)
        assert has_student_submitted_feedback(active_feedback_form, student) is True

    def test_submit_feedback_form_success(self, active_feedback_form, student_user):
        student = student_user.student_profile
        q = active_feedback_form.questions.first()
        submission = submit_feedback_form(
            feedback_form=active_feedback_form,
            student=student,
            answers_by_question_id={str(q.id): "5"},
        )
        assert submission.id is not None
        assert submission.answers.count() == 1
        ans = submission.answers.first()
        assert ans.answer_value == "5"

    def test_submit_feedback_form_not_available_raises(self, active_feedback_form, student_user):
        student = student_user.student_profile
        active_feedback_form.status = FeedbackForm.STATUS_STOPPED
        active_feedback_form.save(update_fields=["status"])
        with pytest.raises(ValueError, match="no longer active"):
            submit_feedback_form(
                feedback_form=active_feedback_form,
                student=student,
                answers_by_question_id={},
            )

    def test_submit_feedback_form_duplicate_raises(self, active_feedback_form, student_user):
        student = student_user.student_profile
        q = active_feedback_form.questions.first()
        submit_feedback_form(
            feedback_form=active_feedback_form,
            student=student,
            answers_by_question_id={str(q.id): "4"},
        )
        with pytest.raises(ValueError, match="already submitted"):
            submit_feedback_form(
                feedback_form=active_feedback_form,
                student=student,
                answers_by_question_id={str(q.id): "5"},
            )

    def test_submit_feedback_form_missing_answer_raises(self, active_feedback_form, student_user):
        student = student_user.student_profile
        with pytest.raises(ValueError, match="answer all questions"):
            submit_feedback_form(
                feedback_form=active_feedback_form,
                student=student,
                answers_by_question_id={},
            )

    def test_submit_feedback_form_invalid_rating_value_raises(self, active_feedback_form, student_user):
        student = student_user.student_profile
        q = active_feedback_form.questions.first()
        with pytest.raises(ValueError, match="Invalid rating value"):
            submit_feedback_form(
                feedback_form=active_feedback_form,
                student=student,
                answers_by_question_id={str(q.id): "99"},
            )

    def test_stop_feedback_form(self, active_feedback_form):
        stopped = stop_feedback_form(active_feedback_form)
        assert stopped.status == FeedbackForm.STATUS_STOPPED
        with pytest.raises(ValueError, match="Only active"):
            stop_feedback_form(stopped)

    def test_delete_feedback_form(self, active_feedback_form):
        form_id = active_feedback_form.id
        delete_feedback_form(active_feedback_form)
        assert not FeedbackForm.objects.filter(id=form_id).exists()

    def test_build_feedback_analysis_and_export_csv(self, active_feedback_form, student_user):
        student = student_user.student_profile
        q = active_feedback_form.questions.first()
        submit_feedback_form(
            feedback_form=active_feedback_form,
            student=student,
            answers_by_question_id={str(q.id): "4"},
        )
        analysis = build_feedback_analysis(active_feedback_form)
        assert "question_stats" in analysis
        assert "overall_analysis" in analysis
        assert len(analysis["student_rows"]) == 1
        assert analysis["student_rows"][0]["student_name"] == student.full_name

        csv_content = export_feedback_analysis_csv(active_feedback_form)
        assert isinstance(csv_content, str)
        assert student.full_name in csv_content


# ─────────────────────────────────────────────────────────────────────────────
# students.import_export
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestImportExportServices:
    def test_normalize_helpers(self):
        assert normalize_text("  Hello World  ") == "Hello World"
        assert normalize_text(None) == ""
        assert normalize_year("Year 1") == "year_1"
        assert normalize_gender("  MALE  ") == "male"
        assert derive_hostel_from_gender("male") == "boys_hostel"
        assert derive_hostel_from_gender("female") == "girls_hostel"
        assert derive_hostel_from_gender("other") is None

    def test_get_or_create_department_by_name(self):
        dept = get_or_create_department_by_name("Electrical Engineering")
        assert dept.name == "Electrical Engineering"
        unassigned = get_or_create_department_by_name("")
        assert unassigned.name == "Unassigned Department"

    def test_parse_csv_file_valid(self):
        csv_data = "full_name,phone_number,department,year,gender,room_number,password\nJohn,9876543210,IT,year_1,male,101,pass123\n"
        f = io.BytesIO(csv_data.encode("utf-8"))
        rows = parse_csv_file(f)
        assert len(rows) == 1
        assert rows[0]["full_name"] == "John"
        assert rows[0]["phone_number"] == "9876543210"

    def test_parse_csv_file_invalid_encoding(self):
        f = io.BytesIO(b"\xff\xfe\x00\x00")
        with pytest.raises(ValueError, match="Could not decode CSV file"):
            parse_csv_file(f)

    def test_parse_xlsx_file_valid(self):
        wb = Workbook()
        ws = wb.active
        ws.append(["full_name", "phone_number", "department", "year", "gender", "room_number", "password"])
        ws.append(["Jane", "9876543211", "CSE", "year_2", "female", "202", "pass456"])
        f = io.BytesIO()
        wb.save(f)
        f.seek(0)
        rows = parse_xlsx_file(f)
        assert len(rows) == 1
        assert rows[0]["full_name"] == "Jane"
        assert rows[0]["room_number"] == "202"

    def test_validate_columns(self):
        valid_rows = [{
            "full_name": "A", "phone_number": "1", "department": "D",
            "year": "year_1", "gender": "male", "room_number": "1", "password": "p",
        }]
        is_valid, msg = validate_columns(valid_rows)
        assert is_valid is True
        assert msg == ""

        is_valid, msg = validate_columns([])
        assert is_valid is False
        assert "empty" in msg

        invalid_rows = [{"full_name": "A"}]
        is_valid, msg = validate_columns(invalid_rows)
        assert is_valid is False
        assert "Missing required columns" in msg

    def test_validate_import_row_valid(self):
        row = {
            "full_name": "Alex Smith",
            "phone_number": "9876500001",
            "department": "IT",
            "year": "year_1",
            "gender": "male",
            "room_number": "105",
            "password": "AlexPass123!",
        }
        validated = validate_import_row(row)
        assert validated["full_name"] == "Alex Smith"
        assert validated["phone_number"] == "9876500001"
        assert validated["year"] == "year_1"
        assert validated["gender"] == "male"
        assert validated["department"].name == "IT"

    def test_validate_import_row_errors(self):
        base_row = {
            "full_name": "Alex", "phone_number": "9876500001",
            "department": "IT", "year": "year_1", "gender": "male",
            "room_number": "105", "password": "pass",
        }
        # Missing full_name
        r = dict(base_row, full_name="")
        with pytest.raises(ValueError, match="Full name is required"):
            validate_import_row(r)
        # Missing phone
        r = dict(base_row, phone_number="")
        with pytest.raises(ValueError, match="Phone number is required"):
            validate_import_row(r)
        # Invalid year
        r = dict(base_row, year="year_9")
        with pytest.raises(ValueError, match="Invalid year"):
            validate_import_row(r)
        # Invalid gender
        r = dict(base_row, gender="alien")
        with pytest.raises(ValueError, match="Invalid gender"):
            validate_import_row(r)
        # Non-digit room
        r = dict(base_row, room_number="Room-A")
        with pytest.raises(ValueError, match="numbers only"):
            validate_import_row(r)


# ─────────────────────────────────────────────────────────────────────────────
# core.utils
# ─────────────────────────────────────────────────────────────────────────────

class TestCoreUtils:
    def test_get_mysql_env_and_build_args(self):
        env = _get_mysql_env()
        assert isinstance(env, dict)
        args = _build_mysql_connection_args()
        assert isinstance(args, list)

    @patch("subprocess.run")
    def test_create_mysql_backup_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        temp_path, filename = create_mysql_backup()
        assert filename.startswith("hostel_backup_")
        assert filename.endswith(".sql")

    @patch("subprocess.run")
    def test_create_mysql_backup_failure_raises(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "mysqldump: access denied"
        mock_run.return_value = mock_result
        with pytest.raises(RuntimeError, match="access denied"):
            create_mysql_backup()

    @patch("subprocess.run")
    def test_restore_mysql_backup_success(self, mock_run, tmp_path):
        dummy_sql = tmp_path / "test.sql"
        dummy_sql.write_text("SELECT 1;")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        restore_mysql_backup(str(dummy_sql))
        mock_run.assert_called_once()

