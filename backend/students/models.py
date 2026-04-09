from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=150, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Student(models.Model):
    YEAR_1 = "year_1"
    YEAR_2 = "year_2"
    YEAR_3 = "year_3"

    YEAR_CHOICES = [
        (YEAR_1, "Year 1"),
        (YEAR_2, "Year 2"),
        (YEAR_3, "Year 3"),
    ]

    GENDER_MALE = "male"
    GENDER_FEMALE = "female"

    GENDER_CHOICES = [
        (GENDER_MALE, "Male"),
        (GENDER_FEMALE, "Female"),
    ]

    HOSTEL_BOYS = "boys_hostel"
    HOSTEL_GIRLS = "girls_hostel"

    HOSTEL_CHOICES = [
        (HOSTEL_BOYS, "Boys Hostel"),
        (HOSTEL_GIRLS, "Girls Hostel"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile"
    )
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15, unique=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students"
    )
    year = models.CharField(max_length=20, choices=YEAR_CHOICES)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    hostel = models.CharField(max_length=20, choices=HOSTEL_CHOICES, editable=False)
    room_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name"]

    def clean(self):
        super().clean()

        if self.room_number and not self.room_number.isdigit():
            raise ValidationError({"room_number": "Room number must contain numbers only."})

        if self.gender == self.GENDER_MALE:
            self.hostel = self.HOSTEL_BOYS
        elif self.gender == self.GENDER_FEMALE:
            self.hostel = self.HOSTEL_GIRLS

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.gender == self.GENDER_MALE:
            self.hostel = self.HOSTEL_BOYS
        elif self.gender == self.GENDER_FEMALE:
            self.hostel = self.HOSTEL_GIRLS
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"

    def get_hostel_display_name(self):
        return dict(self.HOSTEL_CHOICES).get(self.hostel, self.hostel)
    
class StudentImportJob(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="student_import_jobs",
    )
    file_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    total_rows = models.PositiveIntegerField(default=0)
    processed_rows = models.PositiveIntegerField(default=0)
    created_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)

    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Import Job #{self.pk} - {self.status}"