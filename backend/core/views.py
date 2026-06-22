from django.contrib import messages
import tempfile
from django.contrib.auth import get_user_model, logout
from django.http import FileResponse, Http404
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from students.models import Student
from complaints.models import Complaint
from .utils import create_mysql_backup, restore_mysql_backup
from accounts.decorators import student_required, clerk_required, admin_required
from .forms import SystemSettingsForm, AdminProfileForm, AdminPasswordChangeForm
from .models import BackupRecord, SystemSettings
import os
User = get_user_model()


@student_required
@require_http_methods(["GET"])
def student_dashboard(request):
    return render(request, "student/dashboard.html")



@clerk_required
@require_http_methods(["GET"])
def clerk_dashboard_view(request):
    clerk = getattr(request.user, "clerk_profile", None)
    assigned_hostel = clerk.assigned_hostel if clerk else None

    complaints_queryset = Complaint.objects.all()
    if assigned_hostel:
        complaints_queryset = complaints_queryset.filter(hostel_snapshot=assigned_hostel)

    context = {
        "new_count": complaints_queryset.filter(status="new").count(),
        "in_progress_count": complaints_queryset.filter(status="in_progress").count(),
        "completed_count": complaints_queryset.filter(status="completed").count(),
        "solved_count": complaints_queryset.filter(status="solved").count(),
        "unsolved_count": complaints_queryset.filter(status="unsolved").count(),
    }

    return render(request, "clerk/dashboard.html", context)

@admin_required
@require_http_methods(["GET"])
def admin_dashboard(request):
    from academics.models import AcademicFile
    from clerks.models import Clerk

    new_count = Complaint.objects.filter(status="new").count()
    in_progress_count = Complaint.objects.filter(status="in_progress").count()
    completed_count = Complaint.objects.filter(status="completed").count()
    unsolved_count = Complaint.objects.filter(status="unsolved").count()
    solved_count = Complaint.objects.filter(status="solved").count()

    context = {
        "total_students": Student.objects.count(),
        "new_count": new_count,
        "in_progress_count": in_progress_count,
        "completed_count": completed_count,
        "unsolved_count": unsolved_count,
        "solved_count": solved_count,
        "total_complaints": new_count + in_progress_count + completed_count + unsolved_count + solved_count,
        "total_files": AcademicFile.objects.count(),
        "total_clerks": Clerk.objects.count(),
        "locked_accounts_count": User.objects.filter(is_locked=True).count(),
    }
    return render(request, "admin_panel/dashboard.html", context)

@admin_required
@require_http_methods(["GET"])
def locked_accounts_list_view(request):
    locked_users = User.objects.filter(is_locked=True).order_by("role", "username", "phone_number")
    return render(
        request,
        "admin_panel/locked_accounts/locked_accounts_list.html",
        {"locked_users": locked_users},
    )


@admin_required
@require_http_methods(["POST"])
def unlock_account_view(request, pk):
    user = get_object_or_404(User, pk=pk, is_locked=True)
    user.unlock_account()
    messages.success(request, "Account unlocked successfully.")
    return redirect("locked_accounts_list")


@admin_required
@require_http_methods(["GET", "POST"])
def system_settings_view(request):
    settings_obj = SystemSettings.get_solo()
    form = SystemSettingsForm(request.POST or None, request.FILES or None, instance=settings_obj)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "System settings updated successfully.")
        return redirect("system_settings")

    return render(
        request,
        "admin_panel/settings/system_settings.html",
        {"form": form, "settings_obj": settings_obj},
    )


@admin_required
@require_http_methods(["GET", "POST"])
def admin_profile_view(request):
    form = AdminProfileForm(
        request.POST or None,
        initial={"username": request.user.username},
    )

    if request.method == "POST" and form.is_valid():
        new_username = form.cleaned_data["username"].strip()

        existing = User.objects.filter(username=new_username).exclude(pk=request.user.pk).first()
        if existing:
            form.add_error("username", "Username already exists.")
        else:
            request.user.username = new_username
            request.user.save(update_fields=["username"])
            messages.success(request, "Admin profile updated successfully.")
            return redirect("admin_profile")

    return render(
        request,
        "admin_panel/profile/admin_profile.html",
        {"form": form},
    )


@admin_required
@require_http_methods(["GET", "POST"])
def admin_change_password_view(request):
    form = AdminPasswordChangeForm(request.user, request.POST or None)

    if request.method == "POST" and form.is_valid():
        new_password = form.cleaned_data["new_password"]
        request.user.set_password(new_password)
        request.user.save()
        logout(request)
        messages.success(request, "Password changed successfully. Please login again.")
        return redirect("login")

    return render(
        request,
        "admin_panel/profile/change_password.html",
        {"form": form},
    )


@admin_required
@require_http_methods(["GET"])
def backup_list_view(request):
    backups = BackupRecord.objects.select_related("created_by_user").all()
    return render(
        request,
        "admin_panel/backups/backup_list.html",
        {"backups": backups},
    )

@admin_required
@require_http_methods(["POST"])
def backup_create_view(request):
    temp_path = None
    try:
        temp_path, file_name = create_mysql_backup()

        with open(temp_path, "rb") as backup_file:
            backup_record = BackupRecord(created_by_user=request.user)
            backup_record.backup_file.save(file_name, backup_file, save=True)

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

        messages.success(request, "Database backup created successfully.")
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        messages.error(request, f"Backup failed: {str(e)}")

    return redirect("backup_list")

@admin_required
@require_http_methods(["GET"])
def backup_download_view(request, pk):
    backup = get_object_or_404(BackupRecord, pk=pk)
    if not backup.backup_file or not default_storage.exists(backup.backup_file.name):
        raise Http404("Backup file not found.")

    return FileResponse(
        backup.backup_file.open("rb"),
        as_attachment=True,
        filename=backup.backup_file.name.split("/")[-1],
    )
    
@admin_required
@require_http_methods(["POST"])
def backup_delete_view(request, pk):
    backup = get_object_or_404(BackupRecord, pk=pk)
    backup.delete()
    messages.success(request, "Backup record deleted successfully.")
    return redirect("backup_list")

@admin_required
@require_http_methods(["POST"])
def backup_restore_view(request, pk):
    backup = get_object_or_404(BackupRecord, pk=pk)

    if not backup.backup_file or not default_storage.exists(backup.backup_file.name):
        messages.error(request, "Restore failed: backup file not found in storage.")
        return redirect("backup_list")

    temp_file_path = None
    try:
        with backup.backup_file.open("rb") as stored_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".sql") as temp_file:
                temp_file.write(stored_file.read())
                temp_file_path = temp_file.name

        restore_mysql_backup(temp_file_path)
        messages.success(request, "Database restored successfully from backup.")
    except Exception as e:
        messages.error(request, f"Restore failed: {str(e)}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    return redirect("backup_list")
@admin_required
@require_http_methods(["GET"])
def admin_boys_hostel_dashboard(request):
    hostel = "boys_hostel"

    new_count = Complaint.objects.filter(hostel_snapshot=hostel, status="new").count()
    in_progress_count = Complaint.objects.filter(hostel_snapshot=hostel, status="in_progress").count()
    completed_count = Complaint.objects.filter(hostel_snapshot=hostel, status="completed").count()
    unsolved_count = Complaint.objects.filter(hostel_snapshot=hostel, status="unsolved").count()
    solved_count = Complaint.objects.filter(hostel_snapshot=hostel, status="solved").count()

    context = {
        "hostel_label": "Boys Hostel",
        "hostel_value": hostel,
        "student_count": Student.objects.filter(hostel=hostel).count(),
        "new_count": new_count,
        "in_progress_count": in_progress_count,
        "completed_count": completed_count,
        "unsolved_count": unsolved_count,
        "solved_count": solved_count,
        "total_complaints": new_count + in_progress_count + completed_count + unsolved_count + solved_count,
    }
    return render(request, "admin_panel/hostels/hostel_dashboard.html", context)
@admin_required
@require_http_methods(["GET"])
def admin_girls_hostel_dashboard(request):
    hostel = "girls_hostel"

    new_count = Complaint.objects.filter(hostel_snapshot=hostel, status="new").count()
    in_progress_count = Complaint.objects.filter(hostel_snapshot=hostel, status="in_progress").count()
    completed_count = Complaint.objects.filter(hostel_snapshot=hostel, status="completed").count()
    unsolved_count = Complaint.objects.filter(hostel_snapshot=hostel, status="unsolved").count()
    solved_count = Complaint.objects.filter(hostel_snapshot=hostel, status="solved").count()

    context = {
        "hostel_label": "Girls Hostel",
        "hostel_value": hostel,
        "student_count": Student.objects.filter(hostel=hostel).count(),
        "new_count": new_count,
        "in_progress_count": in_progress_count,
        "completed_count": completed_count,
        "unsolved_count": unsolved_count,
        "solved_count": solved_count,
        "total_complaints": new_count + in_progress_count + completed_count + unsolved_count + solved_count,
    }
    return render(request, "admin_panel/hostels/hostel_dashboard.html", context)

def get_complaint_status_counts(queryset):
    return {
        "new_count": queryset.filter(status="new").count(),
        "in_progress_count": queryset.filter(status="in_progress").count(),
        "completed_count": queryset.filter(status="completed").count(),
        "solved_count": queryset.filter(status="solved").count(),
        "unsolved_count": queryset.filter(status="unsolved").count(),
    }