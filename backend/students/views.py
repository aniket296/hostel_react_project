import csv
import logging
import threading

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from accounts.decorators import admin_required
from .forms import DepartmentForm, StudentCreateForm, StudentEditForm
from .import_export import (
    generate_demo_student_csv,
    parse_csv_file,
    parse_xlsx_file,
    validate_columns,
    validate_import_row,
)
from .models import Department, Student, StudentImportJob
from .utils import get_unassigned_department

logger = logging.getLogger(__name__)

User = get_user_model()


def _get_student_queryset_for_user(request):
    queryset = Student.objects.select_related("department", "user")

    if request.user.role == "clerk":
        clerk_profile = getattr(request.user, "clerk_profile", None)
        if clerk_profile:
            queryset = queryset.filter(hostel=clerk_profile.assigned_hostel)
        else:
            queryset = queryset.none()

    return queryset




def _get_clerk_assigned_hostel(request):
    clerk_profile = getattr(request.user, "clerk_profile", None)
    return clerk_profile.assigned_hostel if clerk_profile else None




def _get_allowed_gender_for_user(request):
    assigned_hostel = _get_clerk_assigned_hostel(request)
    if getattr(request.user, "role", None) != "clerk" or not assigned_hostel:
        return None
    if assigned_hostel == Student.HOSTEL_BOYS:
        return Student.GENDER_MALE
    if assigned_hostel == Student.HOSTEL_GIRLS:
        return Student.GENDER_FEMALE
    return None

def _validate_clerk_student_hostel_access(request, form):
    if getattr(request.user, "role", None) != "clerk":
        return True

    assigned_hostel = _get_clerk_assigned_hostel(request)
    gender = form.cleaned_data.get("gender")
    expected_hostel = None
    if gender == Student.GENDER_MALE:
        expected_hostel = Student.HOSTEL_BOYS
    elif gender == Student.GENDER_FEMALE:
        expected_hostel = Student.HOSTEL_GIRLS

    if assigned_hostel and expected_hostel and assigned_hostel != expected_hostel:
        hostel_label = dict(Student.HOSTEL_CHOICES).get(assigned_hostel, assigned_hostel)
        form.add_error("gender", f"You can only manage students for {hostel_label}.")
        return False

    return True

def _apply_student_filters(request, queryset):
    search = request.GET.get("search", "").strip()
    department = request.GET.get("department", "").strip()
    year = request.GET.get("year", "").strip()
    gender = request.GET.get("gender", "").strip()
    hostel = request.GET.get("hostel", "").strip()
    sort = request.GET.get("sort", "").strip()

    if search:
        queryset = queryset.filter(
            Q(full_name__icontains=search)
            | Q(phone_number__icontains=search)
            | Q(department__name__icontains=search)
            | Q(year__icontains=search)
            | Q(room_number__icontains=search)
        )

    if department:
        queryset = queryset.filter(department_id=department)

    if year:
        queryset = queryset.filter(year=year)

    if gender:
        queryset = queryset.filter(gender=gender)

    if hostel:
        queryset = queryset.filter(hostel=hostel)

    if sort == "name_desc":
        queryset = queryset.order_by("-full_name")
    else:
        queryset = queryset.order_by("full_name")

    return queryset


@require_http_methods(["GET"])
def student_list_view(request):
    if not request.user.is_authenticated or request.user.role not in ["clerk", "admin"]:
        return redirect("login")

    queryset = _get_student_queryset_for_user(request)
    queryset = _apply_student_filters(request, queryset)

    paginator = Paginator(queryset, 30)
    page_obj = paginator.get_page(request.GET.get("page"))

    page_heading = "Student Management"
    selected_hostel = request.GET.get("hostel", "").strip()

    if request.user.role == "admin":
        if selected_hostel == "boys_hostel":
            page_heading = "Boys Hostel Students"
        elif selected_hostel == "girls_hostel":
            page_heading = "Girls Hostel Students"

    context = {
        "page_obj": page_obj,
        "students": page_obj.object_list,
        "search": request.GET.get("search", ""),
        "selected_department": request.GET.get("department", ""),
        "selected_year": request.GET.get("year", ""),
        "selected_gender": request.GET.get("gender", ""),
        "selected_hostel": request.GET.get("hostel", ""),
        "selected_sort": request.GET.get("sort", ""),
        "departments": Department.objects.all().order_by("name"),
        "page_heading": page_heading,
    }

    template_name = (
        "clerk/students/student_list.html"
        if request.user.role == "clerk"
        else "admin_panel/students/student_list.html"
    )
    return render(request, template_name, context)


@require_http_methods(["GET", "POST"])
def student_add_view(request):
    if not request.user.is_authenticated or request.user.role not in ["clerk", "admin"]:
        return redirect("login")

    form = StudentCreateForm(request.POST or None, allowed_gender=_get_allowed_gender_for_user(request))

    if request.method == "POST" and form.is_valid():
        if _validate_clerk_student_hostel_access(request, form):
            password = form.cleaned_data.pop("password")
            phone_number = form.cleaned_data["phone_number"]

            if User.objects.filter(phone_number=phone_number).exists():
                form.add_error("phone_number", "A user with this phone number already exists.")
            else:
                user = User.objects.create_user(
                    username=phone_number,
                    phone_number=phone_number,
                    password=password,
                    role="student",
                    is_active=True,
                )

                student = form.save(commit=False)
                student.user = user
                student.phone_number = phone_number
                student.save()

                messages.success(request, "Student created successfully.")
                return redirect("clerk_student_list" if request.user.role == "clerk" else "admin_student_list")

    template_name = (
        "clerk/students/add_student.html"
        if request.user.role == "clerk"
        else "admin_panel/students/add_student.html"
    )
    return render(request, template_name, {"form": form})


@require_http_methods(["GET", "POST"])
def student_edit_view(request, pk):
    if not request.user.is_authenticated or request.user.role not in ["clerk", "admin"]:
        return redirect("login")

    queryset = _get_student_queryset_for_user(request)
    student = get_object_or_404(queryset, pk=pk)

    form = StudentEditForm(request.POST or None, instance=student, allowed_gender=_get_allowed_gender_for_user(request))

    if request.method == "POST" and form.is_valid():
        updated_phone = form.cleaned_data["phone_number"]

        if _validate_clerk_student_hostel_access(request, form):
            existing_user = User.objects.filter(phone_number=updated_phone).exclude(pk=student.user.pk).first()
            if existing_user:
                form.add_error("phone_number", "A user with this phone number already exists.")
            else:
                student = form.save()
                student.user.phone_number = updated_phone
                student.user.username = updated_phone
                student.user.save(update_fields=["phone_number", "username"])

                messages.success(request, "Student updated successfully.")
                return redirect("clerk_student_list" if request.user.role == "clerk" else "admin_student_list")

    template_name = (
        "clerk/students/edit_student.html"
        if request.user.role == "clerk"
        else "admin_panel/students/edit_student.html"
    )
    return render(request, template_name, {"form": form, "student": student})


@require_http_methods(["POST"])
def student_delete_view(request, pk):
    if not request.user.is_authenticated or request.user.role not in ["clerk", "admin"]:
        return redirect("login")

    queryset = _get_student_queryset_for_user(request)
    student = get_object_or_404(queryset, pk=pk)

    user = student.user
    user.delete()

    messages.success(request, "Student deleted successfully.")
    return redirect("clerk_student_list" if request.user.role == "clerk" else "admin_student_list")


@admin_required
@require_http_methods(["GET"])
def department_list_view(request):
    departments = Department.objects.all()
    return render(
        request,
        "admin_panel/departments/department_list.html",
        {"departments": departments},
    )


@admin_required
@require_http_methods(["GET", "POST"])
def department_add_view(request):
    form = DepartmentForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Department created successfully.")
        return redirect("department_list")

    return render(
        request,
        "admin_panel/departments/add_department.html",
        {"form": form},
    )


@admin_required
@require_http_methods(["GET", "POST"])
def department_edit_view(request, pk):
    department = get_object_or_404(Department, pk=pk)
    form = DepartmentForm(request.POST or None, instance=department)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Department updated successfully.")
        return redirect("department_list")

    return render(
        request,
        "admin_panel/departments/edit_department.html",
        {"form": form},
    )


@admin_required
@require_http_methods(["POST"])
def department_delete_view(request, pk):
    department = get_object_or_404(Department, pk=pk)
    unassigned = get_unassigned_department()

    Student.objects.filter(department=department).update(department=unassigned)
    department.delete()

    messages.success(request, "Department deleted successfully.")
    return redirect("department_list")


@require_http_methods(["GET"])
def student_import_view(request):
    if not request.user.is_authenticated or request.user.role not in ["clerk", "admin"]:
        return redirect("login")

    template_name = (
        "clerk/students/import_students.html"
        if request.user.role == "clerk"
        else "admin_panel/students/import_students.html"
    )
    return render(request, template_name)


@require_http_methods(["GET"])
def student_import_demo_file_view(request):
    if not request.user.is_authenticated or request.user.role not in ["clerk", "admin"]:
        return redirect("login")

    csv_content = generate_demo_student_csv()
    response = HttpResponse(csv_content, content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="student_import_demo.csv"'
    return response


def run_student_import_job(job_id, rows, current_user_id):
    from accounts.models import User
    from students.models import Student, StudentImportJob

    job = StudentImportJob.objects.get(pk=job_id)
    job.status = StudentImportJob.STATUS_PROCESSING
    job.total_rows = len(rows)
    job.processed_rows = 0
    job.error_message = ""
    job.save(update_fields=["status", "total_rows", "processed_rows", "error_message", "updated_at"])

    try:
        created_count = 0
        updated_count = 0
        skipped_count = 0
        failed_count = 0

        clerk_hostel = None
        is_clerk = False

        current_user = User.objects.filter(pk=current_user_id).select_related("clerk_profile").first()
        if current_user and getattr(current_user, "role", None) == "clerk":
            clerk_profile = getattr(current_user, "clerk_profile", None)
            if clerk_profile:
                clerk_hostel = clerk_profile.assigned_hostel
                is_clerk = True

        for row_index, row in enumerate(rows, start=1):
            try:
                clean_row = validate_import_row(row)

                if is_clerk and clean_row["derived_hostel"] != clerk_hostel:
                    skipped_count += 1
                    row_error = f"Row {row_index}: Clerk can only import students for assigned hostel."
                    existing_error = job.error_message or ""
                    if len(existing_error) < 4000:
                        job.error_message = (existing_error + "\n" + row_error).strip()
                else:
                    phone_number = clean_row["phone_number"]
                    existing_user = User.objects.filter(phone_number=phone_number).first()

                    if existing_user and hasattr(existing_user, "student_profile"):
                        student = existing_user.student_profile

                        if is_clerk and student.hostel != clerk_hostel:
                            skipped_count += 1
                        else:
                            student.full_name = clean_row["full_name"]
                            student.phone_number = clean_row["phone_number"]
                            student.department = clean_row["department"]
                            student.year = clean_row["year"]
                            student.gender = clean_row["gender"]
                            student.room_number = clean_row["room_number"]
                            student.save()

                            existing_user.username = clean_row["phone_number"]
                            existing_user.phone_number = clean_row["phone_number"]
                            if clean_row["password"]:
                                existing_user.set_password(clean_row["password"])
                            existing_user.save()
                            updated_count += 1
                    elif existing_user:
                        failed_count += 1
                        existing_error = job.error_message or ""
                        row_error = f"Row {row_index}: Phone number already belongs to a non-student account."
                        if len(existing_error) < 4000:
                            job.error_message = (existing_error + "\n" + row_error).strip()
                    else:
                        user = User.objects.create_user(
                            username=clean_row["phone_number"],
                            phone_number=clean_row["phone_number"],
                            password=clean_row["password"],
                            role="student",
                            is_active=True,
                        )

                        Student.objects.create(
                            user=user,
                            full_name=clean_row["full_name"],
                            phone_number=clean_row["phone_number"],
                            department=clean_row["department"],
                            year=clean_row["year"],
                            gender=clean_row["gender"],
                            room_number=clean_row["room_number"],
                        )
                        created_count += 1

            except Exception as e:
                failed_count += 1
                existing_error = job.error_message or ""
                row_error = f"Row {row_index}: {str(e)}"
                logger.exception("Student import row failed at row %s", row_index)
                if len(existing_error) < 4000:
                    job.error_message = (existing_error + "\n" + row_error).strip()

            job.processed_rows = row_index
            job.created_count = created_count
            job.updated_count = updated_count
            job.skipped_count = skipped_count
            job.failed_count = failed_count
            job.save(
                update_fields=[
                    "processed_rows",
                    "created_count",
                    "updated_count",
                    "skipped_count",
                    "failed_count",
                    "error_message",
                    "updated_at",
                ]
            )

        job.status = StudentImportJob.STATUS_COMPLETED
        job.save(update_fields=["status", "updated_at"])

    except Exception as e:
        logger.exception("Student import job failed for job id %s", job.id)
        job.status = StudentImportJob.STATUS_FAILED
        job.error_message = str(e)
        job.save(update_fields=["status", "error_message", "updated_at"])
        
        
@require_http_methods(["POST"])
def student_import_start_view(request):
    if not request.user.is_authenticated or request.user.role not in ["clerk", "admin"]:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return JsonResponse({"error": "No file uploaded."}, status=400)

    file_name = uploaded_file.name.lower()

    try:
        if file_name.endswith(".csv"):
            rows = parse_csv_file(uploaded_file)
        elif file_name.endswith(".xlsx"):
            rows = parse_xlsx_file(uploaded_file)
        else:
            return JsonResponse({"error": "Only CSV and XLSX files are supported."}, status=400)

        is_valid, validation_message = validate_columns(rows)
        if not is_valid:
            return JsonResponse({"error": validation_message}, status=400)

        job = StudentImportJob.objects.create(
            created_by=request.user,
            file_name=uploaded_file.name,
            status=StudentImportJob.STATUS_PENDING,
        )

        thread = threading.Thread(
            target=run_student_import_job,
            args=(job.id, rows, request.user.id),
            daemon=True,
        )
        thread.start()

        return JsonResponse(
            {
                "success": True,
                "job_id": job.id,
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@require_http_methods(["GET"])
def student_import_status_view(request, job_id):
    if not request.user.is_authenticated or request.user.role not in ["clerk", "admin"]:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    job = get_object_or_404(StudentImportJob, pk=job_id, created_by=request.user)

    percent = 0
    if job.total_rows > 0:
        percent = int((job.processed_rows / job.total_rows) * 100)

    return JsonResponse(
        {
            "job_id": job.id,
            "status": job.status,
            "total_rows": job.total_rows,
            "processed_rows": job.processed_rows,
            "created_count": job.created_count,
            "updated_count": job.updated_count,
            "skipped_count": job.skipped_count,
            "failed_count": job.failed_count,
            "error_message": job.error_message,
            "percent": percent,
        }
    )


@require_http_methods(["GET"])
def student_export_view(request):
    if not request.user.is_authenticated or request.user.role not in ["clerk", "admin"]:
        return redirect("login")

    queryset = _get_student_queryset_for_user(request)
    queryset = _apply_student_filters(request, queryset)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="students_export.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "full_name",
            "phone_number",
            "department",
            "year",
            "gender",
            "hostel",
            "room_number",
        ]
    )

    for student in queryset:
        writer.writerow(
            [
                student.full_name,
                student.phone_number,
                student.department.name if student.department else "",
                student.get_year_display(),
                student.get_gender_display(),
                student.get_hostel_display(),
                student.room_number,
            ]
        )

    return response


@require_http_methods(["POST"])
def student_bulk_delete_view(request):
    if not request.user.is_authenticated or request.user.role not in ["clerk", "admin"]:
        return redirect("login")

    selected_ids = request.POST.getlist("student_ids")
    queryset = _get_student_queryset_for_user(request).filter(id__in=selected_ids)

    count = 0
    for student in queryset:
        user = student.user
        user.delete()
        count += 1

    messages.success(request, f"{count} student(s) deleted successfully.")
    return redirect("clerk_student_list" if request.user.role == "clerk" else "admin_student_list")