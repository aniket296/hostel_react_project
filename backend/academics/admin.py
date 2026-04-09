from django.contrib import admin
from .models import Subject, AcademicFile


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(AcademicFile)
class AcademicFileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "subject",
        "department",
        "year",
        "file_type",
        "uploaded_by_name_snapshot",
        "file_size",
        "created_at",
    )
    list_filter = ("department", "year", "file_type")
    search_fields = ("subject__name", "uploaded_by_name_snapshot")
    ordering = ("subject__name",)