from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "id",
        "username",
        "phone_number",
        "role",
        "is_active",
        "is_locked",
        "failed_login_attempts",
    )
    list_filter = ("role", "is_active", "is_locked")
    search_fields = ("username", "phone_number")
    ordering = ("id",)

    fieldsets = UserAdmin.fieldsets + (
        (
            "Custom Fields",
            {
                "fields": (
                    "phone_number",
                    "role",
                    "is_locked",
                    "failed_login_attempts",
                )
            },
        ),
    )