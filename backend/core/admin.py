from django.contrib import admin
from .models import SystemSettings, BackupRecord


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "college_name", "system_title", "maintenance_mode", "updated_at")


@admin.register(BackupRecord)
class BackupRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "backup_file", "created_by_user", "created_at", "notes")
    ordering = ("-created_at",)