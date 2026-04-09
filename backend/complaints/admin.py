from django.contrib import admin
from .models import Complaint, ComplaintStatusHistory


class ComplaintStatusHistoryInline(admin.TabularInline):
    model = ComplaintStatusHistory
    extra = 0
    readonly_fields = ("status", "changed_by_user", "changed_by_role_snapshot", "timestamp")


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "description",
        "student_name_snapshot",
        "worker_name",
        "status",
        "hostel_snapshot",
        "created_at",
    )
    list_filter = ("status", "hostel_snapshot", "created_at")
    search_fields = (
        "description",
        "student_name_snapshot",
        "student_phone_snapshot",
        "worker_name",
        "room_number_snapshot",
    )
    ordering = ("-created_at",)
    inlines = [ComplaintStatusHistoryInline]


@admin.register(ComplaintStatusHistory)
class ComplaintStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "complaint", "status", "changed_by_user", "timestamp")
    list_filter = ("status", "timestamp")
    search_fields = ("complaint__description",)
    ordering = ("timestamp",)