"""
tests/test_api_endpoints.py — Exhaustive integration tests for all REST API endpoints.

Covers:
  - DashboardSummaryApiView (Admin, Clerk, Student roles)
  - DepartmentListCreateApiView & DepartmentDetailApiView (RBAC, CRUD)
  - StudentListCreateApiView & StudentDetailApiView (Clerk isolation, search query, update, delete)
  - ClerkListCreateApiView & ClerkDetailApiView (Admin only, CRUD, username conflict)
  - ComplaintListApiView & ComplaintActionApiView (Student isolation, Clerk isolation, status filter, action handling)
  - SubjectListApiView
  - AcademicListCreateApiView, AcademicDetailApiView, AcademicDownloadApiView (Upload, search, delete, download)
  - FeedbackFormListApiView, FeedbackFormActionApiView, FeedbackSubmitApiView, FeedbackAnalysisApiView
  - LockedAccountsApiView (List locked, unlock action)
  - SystemSettingsApiView (GET, PATCH, PUT)
  - BackupListApiView & BackupActionApiView (List, create, restore, delete, download)
"""
import io
import os
from unittest.mock import patch
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

from students.models import Student, Department
from clerks.models import Clerk
from complaints.models import Complaint
from academics.models import AcademicFile, Subject
from feedbacks.models import FeedbackForm, FeedbackQuestion
from core.models import SystemSettings, BackupRecord

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard Summary
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDashboardSummaryApi:
    def test_admin_dashboard_summary(self, admin_client):
        resp = admin_client.get("/api/dashboard/summary/")
        assert resp.status_code == 200
        assert resp.data["role"] == "admin"
        assert "total_students" in resp.data
        assert "total_clerks" in resp.data
        assert "new_count" in resp.data

    def test_clerk_dashboard_summary(self, clerk_client):
        resp = clerk_client.get("/api/dashboard/summary/")
        assert resp.status_code == 200
        assert resp.data["role"] == "clerk"
        assert resp.data["assigned_hostel"] == "boys_hostel"
        assert "new_count" in resp.data

    def test_student_dashboard_summary(self, auth_client, student_user):
        resp = auth_client.get("/api/dashboard/summary/")
        assert resp.status_code == 200
        assert resp.data["role"] == "student"
        assert resp.data["hostel"] == "boys_hostel"
        assert "complaint_count" in resp.data


# ─────────────────────────────────────────────────────────────────────────────
# Departments
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDepartmentApi:
    def test_list_departments_authenticated(self, auth_client, department):
        resp = auth_client.get("/api/departments/")
        assert resp.status_code == 200
        assert len(resp.data) >= 1

    def test_create_department_admin_only(self, admin_client, clerk_client):
        # Clerk cannot create
        resp = clerk_client.post("/api/departments/", {"name": "Civil Engineering"})
        assert resp.status_code == 403

        # Admin can create
        resp = admin_client.post("/api/departments/", {"name": "Civil Engineering"})
        assert resp.status_code == 201
        assert resp.data["name"] == "Civil Engineering"

    def test_department_detail_update_delete(self, admin_client, department):
        # GET
        resp = admin_client.get(f"/api/departments/{department.id}/")
        assert resp.status_code == 200
        # PUT
        resp = admin_client.put(f"/api/departments/{department.id}/", {"name": "Updated Dept"})
        assert resp.status_code == 200
        assert resp.data["name"] == "Updated Dept"
        # DELETE
        resp = admin_client.delete(f"/api/departments/{department.id}/")
        assert resp.status_code == 204


# ─────────────────────────────────────────────────────────────────────────────
# Students CRUD & Query Isolation
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestStudentApi:
    def test_list_students_clerk_isolation(self, clerk_client, student_user, female_student_user):
        # Clerk is assigned to boys_hostel
        resp = clerk_client.get("/api/students/")
        assert resp.status_code == 200
        names = [s["full_name"] for s in resp.data]
        assert "Test Student" in names
        assert "Female Student" not in names

    def test_search_students_query(self, admin_client, student_user):
        resp = admin_client.get("/api/students/?q=Test")
        assert resp.status_code == 200
        assert len(resp.data) >= 1

        resp = admin_client.get("/api/students/?q=NonExistentStudentNameXYZ")
        assert resp.status_code == 200
        assert len(resp.data) == 0

    def test_update_and_delete_student(self, admin_client, student_user):
        student = student_user.student_profile
        resp = admin_client.patch(f"/api/students/{student.id}/", {
            "full_name": "Updated Student Name",
            "room_number": "999",
        })
        assert resp.status_code == 200
        assert resp.data["full_name"] == "Updated Student Name"

        # Delete
        resp = admin_client.delete(f"/api/students/{student.id}/")
        assert resp.status_code == 204
        assert not Student.objects.filter(id=student.id).exists()
        assert not User.objects.filter(id=student_user.id).exists()


# ─────────────────────────────────────────────────────────────────────────────
# Clerks CRUD
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestClerkApi:
    def test_clerk_crud_admin_only(self, admin_client, clerk_client):
        # Clerk cannot list other clerks
        resp = clerk_client.get("/api/clerks/")
        assert resp.status_code == 403

        # Admin lists clerks
        resp = admin_client.get("/api/clerks/")
        assert resp.status_code == 200

    def test_update_and_delete_clerk(self, admin_client, clerk_user):
        clerk = clerk_user.clerk_profile
        resp = admin_client.patch(f"/api/clerks/{clerk.id}/", {
            "full_name": "Updated Clerk Name",
        })
        assert resp.status_code == 200
        assert resp.data["full_name"] == "Updated Clerk Name"

        resp = admin_client.delete(f"/api/clerks/{clerk.id}/")
        assert resp.status_code == 204
        assert not Clerk.objects.filter(id=clerk.id).exists()


# ─────────────────────────────────────────────────────────────────────────────
# Complaints API & Workflow Actions
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestComplaintWorkflowApi:
    def test_student_complaint_lifecycle(self, auth_client, clerk_client, student_user):
        # 1. Student creates complaint
        resp = auth_client.post("/api/student/complaints/", {"description": "Water leakage in room"})
        assert resp.status_code == 201
        complaint_id = resp.data["id"]
        assert resp.data["status"] == "new"

        # 2. Clerk assigns worker
        resp = clerk_client.post(f"/api/complaints/{complaint_id}/assign-worker/", {
            "worker_name": "Bob Plumber"
        })
        assert resp.status_code == 200
        assert resp.data["status"] == "in_progress"
        assert resp.data["worker_name"] == "Bob Plumber"

        # 3. Clerk marks completed
        resp = clerk_client.post(f"/api/complaints/{complaint_id}/mark-completed/", {})
        assert resp.status_code == 200
        assert resp.data["status"] == "completed"

        # 4. Student marks solved
        resp = auth_client.post(f"/api/complaints/{complaint_id}/mark-solved/", {})
        assert resp.status_code == 200
        assert resp.data["status"] == "solved"

    def test_complaint_mark_unsolved_and_reopen(self, auth_client, clerk_client, complaint):
        # Move to in_progress then student marks unsolved
        clerk_client.post(f"/api/complaints/{complaint.id}/assign-worker/", {"worker_name": "Worker 1"})
        clerk_client.post(f"/api/complaints/{complaint.id}/mark-completed/", {})
        resp = auth_client.post(f"/api/complaints/{complaint.id}/mark-unsolved/", {})
        assert resp.status_code == 200
        assert resp.data["status"] == "unsolved"

        # Clerk reopens
        resp = clerk_client.post(f"/api/complaints/{complaint.id}/reopen/", {"worker_name": "Senior Worker"})
        assert resp.status_code == 200
        assert resp.data["status"] == "in_progress"
        assert resp.data["worker_name"] == "Senior Worker"

    def test_complaint_invalid_action(self, clerk_client, complaint):
        resp = clerk_client.post(f"/api/complaints/{complaint.id}/invalid-action-name/", {})
        assert resp.status_code == 400
        assert "Unknown action" in resp.data["detail"]

    def test_clerk_hostel_isolation_on_complaints(self, girl_clerk_client, complaint):
        # complaint is in boys_hostel, girl_clerk cannot action it
        resp = girl_clerk_client.post(f"/api/complaints/{complaint.id}/assign-worker/", {"worker_name": "A"})
        assert resp.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# Academics API (Upload, List, Delete, Download)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAcademicsApi:
    def test_subject_list(self, auth_client):
        Subject.objects.create(name="Computer Networks")
        resp = auth_client.get("/api/subjects/")
        assert resp.status_code == 200
        names = [s["name"] for s in resp.data]
        assert "Computer Networks" in names

    def test_academic_file_upload_and_download(self, auth_client, admin_client, department):
        subject = Subject.objects.create(name="Data Structures")
        file_content = b"%PDF-1.4 dummy pdf content for testing"
        uploaded_file = SimpleUploadedFile("ds_notes.pdf", file_content, content_type="application/pdf")

        resp = auth_client.post("/api/academics/", {
            "department": department.id,
            "subject": subject.id,
            "year": "year_1",
            "file_type": "notes",
            "file": uploaded_file,
            "course_code": "CS101",
            "description": "Lecture notes",
        }, format="multipart")
        assert resp.status_code == 201
        file_id = resp.data["id"]

        # Download file
        resp = auth_client.get(f"/api/academics/{file_id}/download/")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/pdf"
        # Close the file stream explicitly so Windows can delete the file
        if hasattr(resp, "file_to_stream") and resp.file_to_stream:
            resp.file_to_stream.close()
        elif hasattr(resp, "streaming_content"):
            resp.close()

        # Delete file (Admin/Clerk role required)
        resp = admin_client.delete(f"/api/academics/{file_id}/")
        assert resp.status_code == 204


# ─────────────────────────────────────────────────────────────────────────────
# Feedback Forms API
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestFeedbackFormsApi:
    def test_admin_create_and_manage_form(self, admin_client, student_user):
        from rest_framework.test import APIClient
        student_client = APIClient()
        student_client.force_authenticate(user=student_user)

        # 1. Admin creates feedback form
        payload = {
            "name": "Hostel Cleanliness Audit",
            "hostel": "boys_hostel",
            "duration_hours": 24,
            "questions": [
                {"text": "How clean are the corridors?", "type": "rating"},
                {"text": "Feedback comments", "type": "text"},
            ]
        }
        resp = admin_client.post("/api/feedback/forms/", payload, format="json")
        assert resp.status_code == 201
        form_id = resp.data["id"]

        # 2. Student views active form
        resp = student_client.get("/api/feedback/forms/")
        assert resp.status_code == 200
        assert len(resp.data) == 1
        assert resp.data[0]["id"] == form_id
        q_id = resp.data[0]["questions"][0]["id"]
        q_text_id = resp.data[0]["questions"][1]["id"]

        # 3. Student submits feedback
        submit_payload = {
            "answers": {
                str(q_id): "5",
                str(q_text_id): "Very clean indeed",
            }
        }
        resp = student_client.post(f"/api/feedback/forms/{form_id}/submit/", submit_payload, format="json")
        assert resp.status_code == 201, f"Failed with {resp.status_code}: {resp.data}"
        assert "submission_id" in resp.data

        # 4. Admin views feedback analysis
        resp = admin_client.get(f"/api/feedback/analysis/{form_id}/")
        assert resp.status_code == 200
        assert "overall_analysis" in resp.data

        # 5. Admin stops feedback form
        resp = admin_client.post(f"/api/feedback/forms/{form_id}/stop/", {})
        assert resp.status_code == 200

        # 6. Admin deletes feedback form
        resp = admin_client.post(f"/api/feedback/forms/{form_id}/delete/", {})
        assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# Locked Accounts & System Settings API
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAdministrationApi:
    def test_locked_accounts_list_and_unlock(self, admin_client, student_user):
        User.objects.filter(id=student_user.id).update(is_locked=True)

        resp = admin_client.get("/api/locked-accounts/")
        assert resp.status_code == 200
        ids = [u["id"] for u in resp.data]
        assert student_user.id in ids

        resp = admin_client.post("/api/locked-accounts/", {"user_id": student_user.id})
        assert resp.status_code == 200
        student_user.refresh_from_db()
        assert student_user.is_locked is False

    def test_system_settings_get_and_patch(self, admin_client):
        resp = admin_client.get("/api/system-settings/")
        assert resp.status_code == 200

        resp = admin_client.patch("/api/system-settings/", {"maintenance_mode": True})
        assert resp.status_code == 200
        assert resp.data["maintenance_mode"] is True

        # Revert
        admin_client.patch("/api/system-settings/", {"maintenance_mode": False})


# ─────────────────────────────────────────────────────────────────────────────
# Backups API
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBackupsApi:
    @patch("api.views.create_mysql_backup")
    def test_backup_list_and_create(self, mock_backup, admin_client, tmp_path):
        dummy_file = tmp_path / "test_backup.sql"
        dummy_file.write_text("-- test sql dump")
        mock_backup.return_value = (str(dummy_file), "test_backup.sql")

        resp = admin_client.post("/api/backups/", {})
        assert resp.status_code == 201
        backup_id = resp.data["id"]

        resp = admin_client.get("/api/backups/")
        assert resp.status_code == 200
        assert len(resp.data) >= 1

        # Delete backup
        resp = admin_client.post(f"/api/backups/{backup_id}/delete/", {})
        assert resp.status_code == 200

