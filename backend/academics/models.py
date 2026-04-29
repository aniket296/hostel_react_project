import hashlib
import os
import uuid

from django.core.exceptions import ValidationError
from django.db import models

from students.models import Department, Student


def academic_file_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    subject_slug = instance.subject.name.strip().lower().replace(" ", "_")
    year_slug = instance.year.replace("year_", "y")
    type_slug = instance.file_type
    unique_id = uuid.uuid4().hex[:8]
    new_name = f"{subject_slug}_{year_slug}_{type_slug}_{unique_id}{ext}"
    return os.path.join("academics", type_slug, new_name)


class Subject(models.Model):
    name = models.CharField(max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class AcademicFile(models.Model):
    YEAR_1 = "year_1"
    YEAR_2 = "year_2"
    YEAR_3 = "year_3"

    YEAR_CHOICES = [
        (YEAR_1, "Year 1"),
        (YEAR_2, "Year 2"),
        (YEAR_3, "Year 3"),
    ]

    TYPE_CURRICULUM = "curriculum"
    TYPE_NOTES = "notes"
    TYPE_PYQ_PT = "pyq_pt"
    TYPE_PYQ_SEMESTER = "pyq_semester"
    TYPE_QUESTION_BANK = "question_bank"

    FILE_TYPE_CHOICES = [
        (TYPE_PYQ_PT, "PYQ PT"),
        (TYPE_PYQ_SEMESTER, "PYQ Semester"),
        (TYPE_NOTES, "Notes"),
        (TYPE_QUESTION_BANK, "Question Bank"),
        (TYPE_CURRICULUM, "Curriculum"),
    ]

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="academic_files",
    )
    year = models.CharField(max_length=20, choices=YEAR_CHOICES)
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="academic_files",
    )
    course_code = models.CharField(max_length=50, blank=True, default="")
    description = models.TextField(blank=True, default="")
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    file = models.FileField(upload_to=academic_file_upload_path)

    original_file_name = models.CharField(max_length=255, blank=True)
    stored_file_name = models.CharField(max_length=255, blank=True)
    file_extension = models.CharField(max_length=20, blank=True)
    file_size = models.BigIntegerField(default=0)
    file_hash = models.CharField(max_length=64, unique=True)

    uploaded_by_student = models.ForeignKey(
        Student,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_academic_files",
    )
    uploaded_by_name_snapshot = models.CharField(max_length=200)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["subject__name"]

    def __str__(self):
        return f"{self.subject} - {self.get_file_type_display()}"

    def clean(self):
        super().clean()
        allowed_extensions = {".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg", ".ppt", ".pptx"}

        if self.file:
            ext = os.path.splitext(self.file.name)[1].lower()
            if ext not in allowed_extensions:
                raise ValidationError({"file": "Unsupported file type."})

    def save(self, *args, **kwargs):
        old_file_name = None
        old_storage = None
        if self.pk:
            try:
                old_instance = AcademicFile.objects.get(pk=self.pk)
                if old_instance.file and self.file and old_instance.file.name != self.file.name:
                    old_file_name = old_instance.file.name
                    old_storage = old_instance.file.storage
            except AcademicFile.DoesNotExist:
                pass

        if self.file:
            self.original_file_name = getattr(self.file, "name", "")
            self.file_extension = os.path.splitext(self.file.name)[1].lower()
            self.file_size = self.file.size

            current_position = self.file.tell() if hasattr(self.file, "tell") else None
            file_bytes = self.file.read()
            computed_hash = hashlib.sha256(file_bytes).hexdigest()
            if hasattr(self.file, "seek"):
                self.file.seek(0 if current_position is None else current_position)

            existing = AcademicFile.objects.filter(file_hash=computed_hash)
            if self.pk:
                existing = existing.exclude(pk=self.pk)

            if existing.exists():
                raise ValidationError("Duplicate file detected. Upload blocked.")

            self.file_hash = computed_hash

        self.full_clean()

        super().save(*args, **kwargs)

        if old_storage and old_file_name and old_storage.exists(old_file_name):
            old_storage.delete(old_file_name)

        if self.file:
            self.stored_file_name = os.path.basename(self.file.name)
            super().save(update_fields=["stored_file_name"])

    def delete(self, *args, **kwargs):
        storage = self.file.storage if self.file else None
        file_name = self.file.name if self.file else None

        super().delete(*args, **kwargs)

        if storage and file_name and storage.exists(file_name):
            storage.delete(file_name)

    def get_file_size_display(self):
        size = self.file_size or 0

        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"