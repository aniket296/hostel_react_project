import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from accounts.decorators import student_required
from students.models import Department
from .forms import AcademicUploadForm, AcademicEditForm
from .models import AcademicFile
from .utils import get_or_create_subject_by_name


def _filtered_academic_queryset(request):
    queryset = AcademicFile.objects.select_related(
        "department",
        "subject",
        "uploaded_by_student",
    ).order_by("subject__name")

    search = request.GET.get("search", "").strip()
    department = request.GET.get("department", "").strip()
    year = request.GET.get("year", "").strip()
    file_type = request.GET.get("file_type", "").strip()

    if search:
        queryset = queryset.filter(
            Q(subject__name__icontains=search) |
            Q(course_code__icontains=search)
        )

    if department:
        queryset = queryset.filter(department_id=department)

    if year:
        queryset = queryset.filter(year=year)

    if file_type:
        queryset = queryset.filter(file_type=file_type)

    return queryset

@student_required
@require_http_methods(["GET"])
def student_academics_list_view(request):
    queryset = _filtered_academic_queryset(request)
    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "student/academics/academics_list.html",
        {
            "files": page_obj.object_list,
            "page_obj": page_obj,
            "search": request.GET.get("search", ""),
            "selected_department": request.GET.get("department", ""),
            "selected_year": request.GET.get("year", ""),
            "selected_file_type": request.GET.get("file_type", ""),
            "departments": Department.objects.all().order_by("name"),
        },
    )


@student_required
@require_http_methods(["GET", "POST"])
def student_academic_upload_view(request):
    student = getattr(request.user, "student_profile", None)
    if not student:
        messages.error(request, "Student profile not found.")
        return redirect("student_dashboard")

    form = AcademicUploadForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        subject_name = form.cleaned_data["subject_name"].strip()
        course_code = form.cleaned_data["course_code"].strip()
        subject = get_or_create_subject_by_name(subject_name)

        academic_file = form.save(commit=False)
        academic_file.subject = subject
        academic_file.course_code = course_code
        academic_file.uploaded_by_student = student
        academic_file.uploaded_by_name_snapshot = student.full_name

        try:
            academic_file.save()
            messages.success(request, "File uploaded successfully.")
            return redirect("student_academics_list")
        except IntegrityError:
            messages.error(request, "Duplicate file detected. Upload blocked.")
        except ValidationError as e:
            if hasattr(e, "message_dict"):
                for field, errors in e.message_dict.items():
                    if field in form.fields:
                        for error in errors:
                            form.add_error(field, error)
                    else:
                        for error in errors:
                            form.add_error(None, error)
            else:
                for error in e.messages:
                    form.add_error(None, error)

    return render(
        request,
        "student/academics/upload_file.html",
        {"form": form},
    )


@login_required
@require_http_methods(["GET"])
def academic_download_view(request, pk):
    file_obj = get_object_or_404(AcademicFile, pk=pk)

    if not file_obj.file or not file_obj.file.storage.exists(file_obj.file.name):
        raise Http404("File not found.")

    return FileResponse(
        file_obj.file.open("rb"),
        as_attachment=True,
        filename=os.path.basename(file_obj.file.name),
    )


@require_http_methods(["GET"])
def staff_academics_list_view(request):
    if not request.user.is_authenticated or request.user.role not in ["clerk", "admin"]:
        return redirect("login")

    queryset = _filtered_academic_queryset(request)
    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    template_name = (
        "clerk/academics/academics_list.html"
        if request.user.role == "clerk"
        else "admin_panel/academics/academics_list.html"
    )

    return render(
        request,
        template_name,
        {
            "files": page_obj.object_list,
            "page_obj": page_obj,
            "search": request.GET.get("search", ""),
            "selected_department": request.GET.get("department", ""),
            "selected_year": request.GET.get("year", ""),
            "selected_file_type": request.GET.get("file_type", ""),
            "departments": Department.objects.all().order_by("name"),
        },
    )


@require_http_methods(["GET", "POST"])
def academic_edit_view(request, pk):
    if not request.user.is_authenticated or request.user.role not in ["clerk", "admin"]:
        return redirect("login")

    file_obj = get_object_or_404(AcademicFile, pk=pk)
    initial = {
    "subject_name": file_obj.subject.name,
    "course_code": file_obj.course_code,
}
    form = AcademicEditForm(
        request.POST or None,
        request.FILES or None,
        instance=file_obj,
        initial=initial,
    )

    if request.method == "POST" and form.is_valid():
        subject_name = form.cleaned_data["subject_name"].strip()
        course_code = form.cleaned_data["course_code"].strip()
        subject = get_or_create_subject_by_name(subject_name)

        updated_obj = form.save(commit=False)
        updated_obj.subject = subject
        updated_obj.course_code = course_code

        try:
            updated_obj.save()
            messages.success(request, "Academic file updated successfully.")
            return redirect(
                "clerk_academics_list" if request.user.role == "clerk" else "admin_academics_list"
            )
        except IntegrityError:
            messages.error(request, "Duplicate file detected. Update blocked.")
        except ValidationError as e:
            if hasattr(e, "message_dict"):
                for field, errors in e.message_dict.items():
                    if field in form.fields:
                        for error in errors:
                            form.add_error(field, error)
                    else:
                        for error in errors:
                            form.add_error(None, error)
            else:
                for error in e.messages:
                    form.add_error(None, error)

    template_name = (
        "clerk/academics/edit_file.html"
        if request.user.role == "clerk"
        else "admin_panel/academics/edit_file.html"
    )
    return render(request, template_name, {"form": form, "file_obj": file_obj})


@require_http_methods(["POST"])
def academic_delete_view(request, pk):
    if not request.user.is_authenticated or request.user.role not in ["clerk", "admin"]:
        return redirect("login")

    file_obj = get_object_or_404(AcademicFile, pk=pk)
    file_obj.delete()
    messages.success(request, "Academic file deleted successfully.")
    return redirect("clerk_academics_list" if request.user.role == "clerk" else "admin_academics_list")

@student_required
@require_http_methods(["GET"])
def student_academics_home_view(request):
    return render(request, "student/academics/academics_home.html")