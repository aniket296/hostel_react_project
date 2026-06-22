from django.utils import timezone

from .models import Complaint, ComplaintStatusHistory


def create_status_history(complaint, status, changed_by_user=None):
    ComplaintStatusHistory.objects.create(
        complaint=complaint,
        status=status,
        changed_by_user=changed_by_user,
        changed_by_role_snapshot=getattr(changed_by_user, "role", "") if changed_by_user else "",
    )


def create_student_complaint(student, description):
    complaint = Complaint.objects.create(
        student=student,
        student_name_snapshot=student.full_name,
        student_phone_snapshot=student.phone_number,
        department_name_snapshot=student.department.name if student.department else "",
        year_snapshot=student.year,
        hostel_snapshot=student.hostel,
        room_number_snapshot=student.room_number,
        description=description,
        status=Complaint.STATUS_NEW,
    )
    create_status_history(complaint, Complaint.STATUS_NEW, student.user)
    return complaint


def assign_worker_and_start(complaint, worker_name, changed_by_user):
    complaint.worker_name = worker_name
    complaint.status = Complaint.STATUS_IN_PROGRESS
    complaint.save(update_fields=["worker_name", "status", "updated_at"])
    create_status_history(complaint, Complaint.STATUS_IN_PROGRESS, changed_by_user)


def mark_completed(complaint, changed_by_user):
    complaint.status = Complaint.STATUS_COMPLETED
    complaint.completed_at = timezone.now()
    complaint.save(update_fields=["status", "completed_at", "updated_at"])
    create_status_history(complaint, Complaint.STATUS_COMPLETED, changed_by_user)


def mark_solved(complaint, changed_by_user):
    complaint.status = Complaint.STATUS_SOLVED
    complaint.solved_at = timezone.now()
    complaint.save(update_fields=["status", "solved_at", "updated_at"])
    create_status_history(complaint, Complaint.STATUS_SOLVED, changed_by_user)


def mark_unsolved(complaint, changed_by_user):
    complaint.status = Complaint.STATUS_UNSOLVED
    complaint.unsolved_at = timezone.now()
    complaint.save(update_fields=["status", "unsolved_at", "updated_at"])
    create_status_history(complaint, Complaint.STATUS_UNSOLVED, changed_by_user)


def reopen_unsolved(complaint, changed_by_user, new_worker_name=None):
    complaint.status = Complaint.STATUS_IN_PROGRESS
    complaint.unsolved_at = None
    if new_worker_name:
        complaint.worker_name = new_worker_name
        complaint.save(update_fields=["worker_name", "status", "unsolved_at", "updated_at"])
    else:
        complaint.save(update_fields=["status", "unsolved_at", "updated_at"])
    create_status_history(complaint, Complaint.STATUS_IN_PROGRESS, changed_by_user)