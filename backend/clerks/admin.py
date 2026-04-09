from django.contrib import admin
from .models import Clerk


@admin.register(Clerk)
class ClerkAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "phone_number", "assigned_hostel")
    list_filter = ("assigned_hostel",)
    search_fields = ("full_name", "phone_number")
    ordering = ("full_name",)