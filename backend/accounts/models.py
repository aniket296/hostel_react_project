from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError


class User(AbstractUser):
    ROLE_STUDENT = "student"
    ROLE_CLERK = "clerk"
    ROLE_ADMIN = "admin"

    ROLE_CHOICES = [
        (ROLE_STUDENT, "Student"),
        (ROLE_CLERK, "Clerk"),
        (ROLE_ADMIN, "Admin"),
    ]

    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES,default=ROLE_ADMIN)
    is_locked = models.BooleanField(default=False)
    failed_login_attempts = models.PositiveIntegerField(default=0)

    def clean(self):
        super().clean()

        if self.role == self.ROLE_STUDENT:
            if not self.phone_number:
                raise ValidationError("Student must have a phone number.")

        if self.role in [self.ROLE_CLERK, self.ROLE_ADMIN]:
            if not self.username:
                raise ValidationError("Clerk/Admin must have a username.")

        if self.role == self.ROLE_ADMIN:
            qs = User.objects.filter(role=self.ROLE_ADMIN)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("Only one admin account is allowed.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_display_name()

    def get_display_name(self):
        if self.role == self.ROLE_STUDENT:
            return self.phone_number or "Student"
        return self.username or "User"

    def is_student(self):
        return self.role == self.ROLE_STUDENT

    def is_clerk(self):
        return self.role == self.ROLE_CLERK

    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def lock_account(self):
        self.is_locked = True
        self.save(update_fields=["is_locked"])

    def unlock_account(self):
        self.is_locked = False
        self.failed_login_attempts = 0
        self.save(update_fields=["is_locked", "failed_login_attempts"])

    def reset_login_attempts(self):
        self.failed_login_attempts = 0
        self.save(update_fields=["failed_login_attempts"])