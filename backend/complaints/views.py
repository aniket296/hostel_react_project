from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
import csv
from datetime import datetime
from django.http import HttpResponse, Http404
from accounts.decorators import student_required, clerk_required, admin_required
from .forms import ComplaintCreateForm, AssignWorkerForm
from .models import Complaint
from .services import (
    assign_worker_and_start,
    create_student_complaint,
    mark_completed,
    mark_solved,
    mark_unsolved,
    reopen_unsolved,
)




def _get_supported_staff_statuses():
    return {
        Complaint.STATUS_NEW,
        Complaint.STATUS_IN_PROGRESS,
        Complaint.STATUS_COMPLETED,
        Complaint.STATUS_UNSOLVED,
    }



def _parse_exact_date(date_string):
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except ValueError:
        return None


def _get_clerk_hostel(user):
    clerk_profile = getattr(user, "clerk_profile", None)
    return clerk_profile.assigned_hostel if clerk_profile else None


def _get_clerk_action_queryset(user):
    clerk_hostel = _get_clerk_hostel(user)
    if not clerk_hostel:
        return Complaint.objects.none()
    return Complaint.objects.filter(
        hostel_snapshot=clerk_hostel,
        status__in=[
            Complaint.STATUS_NEW,
            Complaint.STATUS_IN_PROGRESS,
            Complaint.STATUS_UNSOLVED,
        ],
    ).order_by("-created_at")


def _apply_clerk_action_filters(queryset, request):
    search = request.GET.get("search", "").strip()
    selected_status = request.GET.get("status", "").strip()

    if search:
        queryset = queryset.filter(
            Q(id__icontains=search)
            | Q(description__icontains=search)
            | Q(room_number_snapshot__icontains=search)
        )

    if selected_status in [
        Complaint.STATUS_NEW,
        Complaint.STATUS_IN_PROGRESS,
        Complaint.STATUS_UNSOLVED,
    ]:
        queryset = queryset.filter(status=selected_status)

    return queryset, search, selected_status


def _get_clerk_report_queryset(user):
    clerk_hostel = _get_clerk_hostel(user)
    if not clerk_hostel:
        return Complaint.objects.none()
    return Complaint.objects.filter(hostel_snapshot=clerk_hostel).order_by("-created_at")

def _get_hostel_filtered_queryset_for_staff(user):
    queryset = Complaint.objects.all().prefetch_related("status_history").select_related("student")

    if user.role == "clerk":
        clerk_profile = getattr(user, "clerk_profile", None)
        if not clerk_profile:
            return Complaint.objects.none()
        queryset = queryset.filter(hostel_snapshot=clerk_profile.assigned_hostel)

    return queryset


@student_required
@require_http_methods(["GET"])
def student_complaint_list_view(request):
    student = getattr(request.user, "student_profile", None)
    if not student:
        return redirect("login")

    queryset = Complaint.objects.filter(student=student).prefetch_related("status_history").order_by("-created_at")

    status = request.GET.get("status", "").strip()
    if status:
        queryset = queryset.filter(status=status)

    paginator = Paginator(queryset, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "student/complaints/complaint_list.html",
        {
            "complaints": page_obj.object_list,
            "page_obj": page_obj,
            "selected_status": status,
            "total_count": queryset.count(),
        },
    )


@student_required
@require_http_methods(["GET", "POST"])
def student_complaint_create_view(request):
    student = getattr(request.user, "student_profile", None)
    if not student:
        return redirect("login")

    form = ComplaintCreateForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        description = form.cleaned_data["description"]
        create_student_complaint(student, description)
        messages.success(request, "Complaint submitted successfully.")
        return redirect("student_complaint_list")

    return render(
        request,
        "student/complaints/complaint_form.html",
        {
            "form": form,
            "student": student,
        },
    )


@student_required
@require_http_methods(["GET"])
def student_complaint_detail_view(request, pk):
    student = getattr(request.user, "student_profile", None)
    complaint = get_object_or_404(
        Complaint.objects.prefetch_related("status_history"),
        pk=pk,
        student=student,
    )

    return render(
        request,
        "student/complaints/complaint_detail.html",
        {"complaint": complaint},
    )


@student_required
@require_http_methods(["POST"])
def student_mark_solved_view(request, pk):
    student = getattr(request.user, "student_profile", None)
    complaint = get_object_or_404(Complaint, pk=pk, student=student)

    if complaint.status != Complaint.STATUS_COMPLETED:
        messages.error(request, "Only completed complaints can be marked as solved.")
        return redirect("student_complaint_list")

    mark_solved(complaint, request.user)
    messages.success(request, "Complaint marked as solved.")
    return redirect("student_complaint_list")


@student_required
@require_http_methods(["POST"])
def student_mark_unsolved_view(request, pk):
    student = getattr(request.user, "student_profile", None)
    complaint = get_object_or_404(Complaint, pk=pk, student=student)

    if complaint.status != Complaint.STATUS_COMPLETED:
        messages.error(request, "Only completed complaints can be marked as unsolved.")
        return redirect("student_complaint_list")

    mark_unsolved(complaint, request.user)
    messages.success(request, "Complaint marked as unsolved.")
    return redirect("student_complaint_list")


@require_http_methods(["GET"])
def complaint_list_by_status_view(request, status):
    if not request.user.is_authenticated or request.user.role not in ["clerk", "admin"]:
        return redirect("login")

    if status not in _get_supported_staff_statuses():
        raise Http404("Invalid complaint status.")

    queryset = _get_hostel_filtered_queryset_for_staff(request.user)

    queryset = queryset.filter(status=status)
    hostel = request.GET.get("hostel", "").strip()
    if request.user.role == "admin" and hostel:
        queryset = queryset.filter(hostel_snapshot=hostel)
    search = request.GET.get("search", "").strip()
    if search:
        queryset = queryset.filter(
            Q(description__icontains=search) |
            Q(student_name_snapshot__icontains=search) |
            Q(student_phone_snapshot__icontains=search) |
            Q(worker_name__icontains=search) |
            Q(room_number_snapshot__icontains=search)
        )

    paginator = Paginator(queryset.order_by("-created_at"), 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    template_name = (
        f"clerk/complaints/{status}_list.html"
        if request.user.role == "clerk"
        else f"admin_panel/complaints/{status}_list.html"
    )

    return render(
        request,
        template_name,
        {
            "selected_hostel": hostel,
            "complaints": page_obj.object_list,
            "page_obj": page_obj,
            "status": status,
            "search": search,
            "assign_form": AssignWorkerForm(),
        },
    )


@require_http_methods(["GET"])
def complaint_detail_view(request, pk):
    if not request.user.is_authenticated or request.user.role not in ["clerk", "admin"]:
        return redirect("login")

    queryset = _get_hostel_filtered_queryset_for_staff(request.user)
    complaint = get_object_or_404(queryset.prefetch_related("status_history"), pk=pk)

    template_name = (
        "clerk/complaints/complaint_detail.html"
        if request.user.role == "clerk"
        else "admin_panel/complaints/complaint_detail.html"
    )

    return render(
        request,
        template_name,
        {
            "complaint": complaint,
            "assign_form": AssignWorkerForm(),
        },
    )


@require_http_methods(["POST"])
def assign_worker_view(request, pk):
    if not request.user.is_authenticated or request.user.role not in ["clerk", "admin"]:
        return redirect("login")

    queryset = _get_hostel_filtered_queryset_for_staff(request.user)
    complaint = get_object_or_404(queryset, pk=pk)

    if complaint.status not in [Complaint.STATUS_NEW, Complaint.STATUS_UNSOLVED]:
        messages.error(request, "Worker can only be assigned to new or unsolved complaints.")
        return redirect(request.META.get("HTTP_REFERER", "admin_dashboard"))

    form = AssignWorkerForm(request.POST)
    if form.is_valid():
        worker_name = form.cleaned_data["worker_name"]
        if complaint.status == Complaint.STATUS_UNSOLVED:
            reopen_unsolved(complaint, worker_name, request.user)
            messages.success(request, "Complaint reopened and worker assigned.")
        else:
            assign_worker_and_start(complaint, worker_name, request.user)
            messages.success(request, "Worker assigned successfully.")
    else:
        messages.error(request, "Please enter a valid worker name.")

    fallback = "clerk_dashboard" if request.user.role == "clerk" else "admin_dashboard"
    return redirect(request.META.get("HTTP_REFERER", fallback))


@require_http_methods(["POST"])
def mark_completed_view(request, pk):
    if not request.user.is_authenticated or request.user.role not in ["clerk", "admin"]:
        return redirect("login")

    queryset = _get_hostel_filtered_queryset_for_staff(request.user)
    complaint = get_object_or_404(queryset, pk=pk)

    if complaint.status not in [Complaint.STATUS_NEW, Complaint.STATUS_IN_PROGRESS]:
        messages.error(request, "Only new or in-progress complaints can be marked completed.")
        return redirect(request.META.get("HTTP_REFERER", "admin_dashboard"))

    mark_completed(complaint, request.user)
    messages.success(request, "Complaint marked as completed.")
    fallback = "clerk_dashboard" if request.user.role == "clerk" else "admin_dashboard"
    return redirect(request.META.get("HTTP_REFERER", fallback))

@require_http_methods(["GET"])
def complaint_export_view(request):
    if not request.user.is_authenticated or request.user.role not in ["clerk", "admin"]:
        return redirect("login")

    queryset = _get_hostel_filtered_queryset_for_staff(request.user)
    hostel = request.GET.get("hostel", "").strip()
    if request.user.role == "admin" and hostel:
        queryset = queryset.filter(hostel_snapshot=hostel)
    status = request.GET.get("status", "").strip()
    search = request.GET.get("search", "").strip()

    if status:
        queryset = queryset.filter(status=status)

    if search:
        queryset = queryset.filter(
            Q(description__icontains=search) |
            Q(student_name_snapshot__icontains=search) |
            Q(student_phone_snapshot__icontains=search) |
            Q(worker_name__icontains=search) |
            Q(room_number_snapshot__icontains=search)
        )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="complaints_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "id",
        "description",
        "student_name",
        "student_phone",
        "department",
        "year",
        "hostel",
        "room_number",
        "worker_name",
        "status",
        "created_at",
        "completed_at",
        "solved_at",
        "unsolved_at",
    ])

    for complaint in queryset.order_by("-created_at"):
        writer.writerow([
            complaint.id,
            complaint.description,
            complaint.student_name_snapshot,
            complaint.student_phone_snapshot,
            complaint.department_name_snapshot,
            complaint.get_year_snapshot_display(),
            complaint.get_hostel_snapshot_display(),
            complaint.room_number_snapshot,
            complaint.worker_name,
            complaint.get_status_display(),
            complaint.created_at,
            complaint.completed_at,
            complaint.solved_at,
            complaint.unsolved_at,
        ])

    return response



@admin_required
@require_http_methods(["GET"])
def admin_complaint_history_view(request):
    queryset = Complaint.objects.all().order_by("-created_at")

    search = request.GET.get("search", "").strip()
    selected_status = request.GET.get("status", "").strip()
    selected_hostel = request.GET.get("hostel", "").strip()

    if search:
        queryset = queryset.filter(
            Q(description__icontains=search) |
            Q(student_name_snapshot__icontains=search) |
            Q(student_phone_snapshot__icontains=search) |
            Q(worker_name__icontains=search) |
            Q(room_number_snapshot__icontains=search)
        )

    if selected_status:
        queryset = queryset.filter(status=selected_status)

    if selected_hostel:
        queryset = queryset.filter(hostel_snapshot=selected_hostel)

    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "admin_panel/complaints/history_list.html",
        {
            "complaints": page_obj.object_list,
            "page_obj": page_obj,
            "search": search,
            "selected_status": selected_status,
            "selected_hostel": selected_hostel,
        },
    )
    
@clerk_required
@require_http_methods(["GET"])
def clerk_complaint_history_view(request):
    clerk_profile = getattr(request.user, "clerk_profile", None)
    if not clerk_profile:
        messages.error(request, "Clerk profile not found.")
        return redirect("clerk_dashboard")

    queryset = Complaint.objects.filter(
        hostel_snapshot=clerk_profile.assigned_hostel
    ).order_by("-created_at")

    search = request.GET.get("search", "").strip()
    selected_status = request.GET.get("status", "").strip()

    if search:
        queryset = queryset.filter(
            Q(description__icontains=search) |
            Q(student_name_snapshot__icontains=search) |
            Q(student_phone_snapshot__icontains=search) |
            Q(worker_name__icontains=search) |
            Q(room_number_snapshot__icontains=search)
        )

    if selected_status:
        queryset = queryset.filter(status=selected_status)

    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "clerk/complaints/history_list.html",
        {
            "complaints": page_obj.object_list,
            "page_obj": page_obj,
            "search": search,
            "selected_status": selected_status,
            "clerk_hostel": clerk_profile.assigned_hostel,
        },
    )
    

@clerk_required
@require_http_methods(["GET"])
def clerk_actions_complaint_list_view(request):
    queryset = _get_clerk_action_queryset(request.user)
    queryset, search, selected_status = _apply_clerk_action_filters(queryset, request)
    complaints = queryset
    return render(
        request,
        "clerk/complaints/actions_complaint_list.html",
        {
            "complaints": complaints,
            "search": search,
            "selected_status": selected_status,
        },
    )


@clerk_required
@require_http_methods(["POST"])
def clerk_actions_bulk_mark_completed_view(request):
    selected_ids = request.POST.getlist("complaint_ids")

    if not selected_ids:
        messages.error(request, "Please select at least one complaint.")
        return redirect("clerk_actions_complaints")

    queryset = _get_clerk_action_queryset(request.user).filter(pk__in=selected_ids)

    completed_count = 0
    skipped_count = 0

    for complaint in queryset:
        if complaint.status in [Complaint.STATUS_NEW, Complaint.STATUS_IN_PROGRESS]:
            mark_completed(complaint, request.user)
            completed_count += 1
        else:
            skipped_count += 1

    if completed_count:
        messages.success(request, f"{completed_count} complaint(s) marked as completed.")
    if skipped_count:
        messages.warning(request, f"{skipped_count} selected complaint(s) were skipped because only new or in-progress complaints can be marked completed.")
    if not completed_count and not skipped_count:
        messages.error(request, "No valid complaints were selected.")

    return redirect("clerk_actions_complaints")


@clerk_required
@require_http_methods(["GET"])
def clerk_actions_complaint_export_view(request):
    queryset = _get_clerk_action_queryset(request.user)
    queryset, search, selected_status = _apply_clerk_action_filters(queryset, request)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="clerk_complaints_list.csv"'

    writer = csv.writer(response)
    writer.writerow(["complaint_id", "description", "room_number", "status"])

    for complaint in queryset:
        writer.writerow([
            complaint.id,
            complaint.description,
            complaint.room_number_snapshot,
            complaint.get_status_display(),
        ])

    return response


@clerk_required
@require_http_methods(["GET"])
def clerk_actions_report_view(request):
    selected_date = request.GET.get("date", "").strip()
    parsed_date = _parse_exact_date(selected_date)

    queryset = _get_clerk_report_queryset(request.user)
    if selected_date and not parsed_date:
        messages.error(request, "Please select a valid date.")
    elif parsed_date:
        queryset = queryset.filter(created_at__date=parsed_date)

    return render(
        request,
        "clerk/complaints/actions_report.html",
        {
            "complaints": queryset,
            "selected_date": selected_date,
        },
    )


@clerk_required
@require_http_methods(["GET"])
def clerk_actions_report_export_view(request):
    selected_date = request.GET.get("date", "").strip()
    parsed_date = _parse_exact_date(selected_date)

    queryset = _get_clerk_report_queryset(request.user)
    if parsed_date:
        queryset = queryset.filter(created_at__date=parsed_date)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="clerk_complaint_report.csv"'

    writer = csv.writer(response)
    writer.writerow(["complaint_id", "description", "room_number", "status", "date"])

    for complaint in queryset:
        writer.writerow([
            complaint.id,
            complaint.description,
            complaint.room_number_snapshot,
            complaint.get_status_display(),
            complaint.created_at.strftime("%Y-%m-%d"),
        ])

    return response


@student_required
@require_http_methods(["GET"])
def student_complaint_home_view(request):
    return render(request, "student/complaints/complaint_home.html")

