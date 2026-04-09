from django.contrib import admin
from .models import Department, Student


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "phone_number",
        "department",
        "year",
        "gender",
        "hostel",
        "room_number",
    )
    list_filter = ("year", "gender", "hostel", "department")
    search_fields = ("full_name", "phone_number", "room_number")
    ordering = ("full_name",)