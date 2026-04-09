from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from students.models import Student


class Complaint(models.Model):
    STATUS_NEW = "new"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_SOLVED = "solved"
    STATUS_UNSOLVED = "unsolved"

    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_SOLVED, "Solved"),
        (STATUS_UNSOLVED, "Unsolved"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints",
    )

    student_name_snapshot = models.CharField(max_length=200)
    student_phone_snapshot = models.CharField(max_length=15)
    department_name_snapshot = models.CharField(max_length=150, blank=True)
    year_snapshot = models.CharField(max_length=20)
    hostel_snapshot = models.CharField(max_length=20)
    room_number_snapshot = models.CharField(max_length=20)

    description = models.CharField(max_length=100)
    worker_name = models.CharField(max_length=200, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    solved_at = models.DateTimeField(null=True, blank=True)
    unsolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        super().clean()

        if self.description:
            word_count = len(self.description.strip().split())
            if word_count > 6:
                raise ValidationError({"description": "Complaint description cannot exceed 6 words."})

        if self.room_number_snapshot and not self.room_number_snapshot.isdigit():
            raise ValidationError({"room_number_snapshot": "Room number must contain numbers only."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_year_snapshot_display(self):
        return dict(Student.YEAR_CHOICES).get(self.year_snapshot, self.year_snapshot)

    def get_hostel_snapshot_display(self):
        return dict(Student.HOSTEL_CHOICES).get(self.hostel_snapshot, self.hostel_snapshot)

    def __str__(self):
        return f"{self.description} - {self.get_status_display()}"


class ComplaintStatusHistory(models.Model):
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    status = models.CharField(max_length=20, choices=Complaint.STATUS_CHOICES)
    changed_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    changed_by_role_snapshot = models.CharField(max_length=20, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.complaint_id} - {self.status}"