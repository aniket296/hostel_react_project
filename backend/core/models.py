import os

from django.conf import settings
from django.db import models


def system_logo_upload_path(instance, filename):
    return f"system/logos/{filename}"


def system_header_upload_path(instance, filename):
    return f"system/headers/{filename}"


def backup_file_upload_path(instance, filename):
    return f"backups/{filename}"


class SystemSettings(models.Model):
    college_name = models.CharField(max_length=255, default="Government Polytechnic Nagpur")
    college_logo = models.ImageField(upload_to=system_logo_upload_path, blank=True, null=True)
    header_photo = models.ImageField(upload_to=system_header_upload_path, blank=True, null=True)
    system_title = models.CharField(max_length=255, default="Hostel Management System")
    maintenance_mode = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.system_title

    def save(self, *args, **kwargs):
        old_logo_name = None
        old_logo_storage = None
        old_header_name = None
        old_header_storage = None

        if self.pk:
            try:
                old_instance = SystemSettings.objects.get(pk=self.pk)
                if old_instance.college_logo and (
                    not self.college_logo or old_instance.college_logo.name != self.college_logo.name
                ):
                    old_logo_name = old_instance.college_logo.name
                    old_logo_storage = old_instance.college_logo.storage
                if old_instance.header_photo and (
                    not self.header_photo or old_instance.header_photo.name != self.header_photo.name
                ):
                    old_header_name = old_instance.header_photo.name
                    old_header_storage = old_instance.header_photo.storage
            except SystemSettings.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        if old_logo_storage and old_logo_name and old_logo_storage.exists(old_logo_name):
            old_logo_storage.delete(old_logo_name)
        if old_header_storage and old_header_name and old_header_storage.exists(old_header_name):
            old_header_storage.delete(old_header_name)

    def delete(self, *args, **kwargs):
        logo_storage = self.college_logo.storage if self.college_logo else None
        logo_name = self.college_logo.name if self.college_logo else None
        header_storage = self.header_photo.storage if self.header_photo else None
        header_name = self.header_photo.name if self.header_photo else None

        super().delete(*args, **kwargs)

        if logo_storage and logo_name and logo_storage.exists(logo_name):
            logo_storage.delete(logo_name)
        if header_storage and header_name and header_storage.exists(header_name):
            header_storage.delete(header_name)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                "college_name": "Government Polytechnic Nagpur",
                "system_title": "Hostel Management System",
            },
        )
        return obj


class BackupRecord(models.Model):
    backup_file = models.FileField(upload_to=backup_file_upload_path)
    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Backup {self.id} - {self.created_at}"

    def delete(self, *args, **kwargs):
        file_storage = self.backup_file.storage if self.backup_file else None
        file_name = self.backup_file.name if self.backup_file else None

        super().delete(*args, **kwargs)

        if file_storage and file_name and file_storage.exists(file_name):
            file_storage.delete(file_name)
