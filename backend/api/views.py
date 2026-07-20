from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
import os
from rest_framework import generics, permissions
from rest_framework.parsers import FormParser, MultiPartParser
from django.http import FileResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from students.models import Student, Department
from clerks.models import Clerk
from complaints.models import Complaint
from academics.models import AcademicFile, Subject
from feedbacks.models import FeedbackForm
from feedbacks.services import build_feedback_analysis, get_active_feedback_form_for_hostel, has_student_submitted_feedback, submit_feedback_form
from feedbacks.services import create_feedback_form_with_questions, delete_feedback_form, export_feedback_analysis_csv, get_all_feedback_forms, stop_feedback_form
from complaints.services import create_student_complaint, assign_worker_and_start, mark_completed, mark_solved, mark_unsolved, reopen_unsolved
from core.models import SystemSettings, BackupRecord
from core.utils import create_mysql_backup, restore_mysql_backup
from .permissions import IsAdminRole, IsAdminOrClerkRole, IsStudentRole
from .serializers import (
    UserSerializer, DepartmentSerializer, StudentSerializer, StudentCreateUpdateSerializer,
    ClerkSerializer, ClerkCreateUpdateSerializer, ComplaintSerializer, ComplaintCreateSerializer,
    AcademicFileSerializer, AcademicFileCreateSerializer, SubjectSerializer,
    FeedbackFormSerializer, FeedbackFormCreateSerializer, SystemSettingsSerializer, BackupRecordSerializer,
)

User = get_user_model()


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


def _refresh_cookie_kwargs():
    return {
        "httponly": True,
        "samesite": os.getenv("AUTH_COOKIE_SAMESITE", "Lax"),
        "secure": os.getenv("AUTH_COOKIE_SECURE", "True").lower() == "true",
        "path": "/",
    }


class LoginApiView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        identifier = (request.data.get("identifier") or "").strip()
        password = request.data.get("password") or ""
        user = User.objects.filter(Q(username=identifier) | Q(phone_number=identifier)).first()
        if user and user.is_locked and user.role != User.ROLE_ADMIN:
            return Response({"detail": "Account locked. Please contact Admin."}, status=403)
        authed = authenticate(request, username=identifier, password=password)
        if authed is None:
            if user:
                if user.role != User.ROLE_ADMIN:
                    user.failed_login_attempts += 1
                    if user.failed_login_attempts >= 3:
                        user.is_locked = True
                    user.save(update_fields=["failed_login_attempts", "is_locked"])
            return Response({"detail": "Invalid credentials."}, status=400)
        authed.reset_login_attempts()
        tokens = _tokens_for_user(authed)
        response = Response({"user": UserSerializer(authed).data, **tokens})
        response.set_cookie("refresh_token", tokens["refresh"], **_refresh_cookie_kwargs())
        return response


class RefreshApiView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        raw = request.COOKIES.get("refresh_token") or request.data.get("refresh")
        if not raw:
            return Response({"detail": "Refresh token missing."}, status=400)
        try:
            token = RefreshToken(raw)
            return Response({"access": str(token.access_token)})
        except TokenError:
            return Response({"detail": "Invalid refresh token."}, status=401)


class LogoutApiView(APIView):
    def post(self, request):
        response = Response({"detail": "Logged out."})
        raw = request.COOKIES.get("refresh_token")
        if raw:
            try:
                RefreshToken(raw).blacklist()
            except Exception:
                pass
        response.delete_cookie("refresh_token", path="/")
        return response


class MeApiView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class DashboardSummaryApiView(APIView):
    def get(self, request):
        role = request.user.role
        data = {"role": role}
        if role == User.ROLE_ADMIN:
            from clerks.models import Clerk
            data.update({
                "total_students": Student.objects.count(),
                "total_clerks": Clerk.objects.count(),
                "new_count": Complaint.objects.filter(status=Complaint.STATUS_NEW).count(),
                "in_progress_count": Complaint.objects.filter(status=Complaint.STATUS_IN_PROGRESS).count(),
                "completed_count": Complaint.objects.filter(status=Complaint.STATUS_COMPLETED).count(),
                "solved_count": Complaint.objects.filter(status=Complaint.STATUS_SOLVED).count(),
                "unsolved_count": Complaint.objects.filter(status=Complaint.STATUS_UNSOLVED).count(),
                "total_files": AcademicFile.objects.count(),
                "locked_accounts_count": User.objects.filter(is_locked=True).count(),
            })
        elif role == User.ROLE_CLERK:
            clerk = getattr(request.user, "clerk_profile", None)
            queryset = Complaint.objects.all()
            if clerk:
                queryset = queryset.filter(hostel_snapshot=clerk.assigned_hostel)
            data.update({
                "assigned_hostel": clerk.assigned_hostel if clerk else None,
                "new_count": queryset.filter(status=Complaint.STATUS_NEW).count(),
                "in_progress_count": queryset.filter(status=Complaint.STATUS_IN_PROGRESS).count(),
                "completed_count": queryset.filter(status=Complaint.STATUS_COMPLETED).count(),
                "solved_count": queryset.filter(status=Complaint.STATUS_SOLVED).count(),
                "unsolved_count": queryset.filter(status=Complaint.STATUS_UNSOLVED).count(),
            })
        else:
            student = getattr(request.user, "student_profile", None)
            data.update({
                "student_name": student.full_name if student else request.user.get_display_name(),
                "hostel": getattr(student, "hostel", None),
                "complaint_count": student.complaints.count() if student else 0,
                "has_active_feedback": bool(student and get_active_feedback_form_for_hostel(student.hostel)),
            })
        return Response(data)


class DepartmentListCreateApiView(generics.ListCreateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAuthenticated()]
        return [IsAdminRole()]


class DepartmentDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminRole]


class StudentListCreateApiView(generics.ListCreateAPIView):
    serializer_class = StudentSerializer
    permission_classes = [IsAdminOrClerkRole]

    def get_queryset(self):
        queryset = Student.objects.select_related("user", "department")
        q = (self.request.GET.get("q") or "").strip()
        if self.request.user.role == User.ROLE_CLERK:
            clerk = getattr(self.request.user, "clerk_profile", None)
            if clerk:
                queryset = queryset.filter(hostel=clerk.assigned_hostel)
        if q:
            queryset = queryset.filter(Q(full_name__icontains=q) | Q(phone_number__icontains=q) | Q(room_number__icontains=q) | Q(department__name__icontains=q))
        return queryset.order_by("full_name")

    def create(self, request, *args, **kwargs):
        serializer = StudentCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        phone = data["phone_number"]
        if User.objects.filter(phone_number=phone).exists():
            return Response({"phone_number": ["Phone number already exists."]}, status=400)
        user = User.objects.create_user(username=phone, phone_number=phone, password=data.get("password") or phone, role=User.ROLE_STUDENT)
        student = Student.objects.create(user=user, full_name=data["full_name"], phone_number=phone, department=data.get("department"), year=data["year"], gender=data["gender"], room_number=data["room_number"])
        return Response(StudentSerializer(student).data, status=201)


class StudentDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.select_related("user", "department")
    serializer_class = StudentSerializer
    permission_classes = [IsAdminOrClerkRole]

    def update(self, request, *args, **kwargs):
        student = self.get_object()
        serializer = StudentCreateUpdateSerializer(student, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data.get("phone_number")
        if phone_number and User.objects.filter(phone_number=phone_number).exclude(pk=student.user.pk).exists():
            return Response({"phone_number": ["Phone number already exists."]}, status=400)
        for attr, value in serializer.validated_data.items():
            if attr != "password":
                setattr(student, attr, value)
        student.save()
        if phone_number:
            student.user.phone_number = phone_number
            student.user.username = phone_number
            student.user.save(update_fields=["phone_number", "username"])
        if serializer.validated_data.get("password"):
            student.user.set_password(serializer.validated_data["password"])
            student.user.save(update_fields=["password"])
        return Response(StudentSerializer(student).data)

    def destroy(self, request, *args, **kwargs):
        student = self.get_object()
        user = student.user
        student.delete()
        user.delete()
        return Response(status=204)


class ClerkListCreateApiView(generics.ListCreateAPIView):
    queryset = Clerk.objects.select_related("user")
    permission_classes = [IsAdminRole]

    def get_serializer_class(self):
        return ClerkSerializer if self.request.method == "GET" else ClerkCreateUpdateSerializer

    def create(self, request, *args, **kwargs):
        serializer = ClerkCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if User.objects.filter(username=data["username"]).exists():
            return Response({"username": ["Username already exists."]}, status=400)
        user = User.objects.create_user(username=data["username"], password=data.get("password") or data["username"], phone_number=data.get("phone_number") or None, role=User.ROLE_CLERK)
        clerk = Clerk.objects.create(user=user, full_name=data["full_name"], phone_number=data["phone_number"], assigned_hostel=data["assigned_hostel"])
        return Response(ClerkSerializer(clerk).data, status=201)


class ClerkDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Clerk.objects.select_related("user")
    permission_classes = [IsAdminRole]

    def get_serializer_class(self):
        return ClerkSerializer if self.request.method == "GET" else ClerkCreateUpdateSerializer

    def update(self, request, *args, **kwargs):
        clerk = self.get_object()
        serializer = ClerkCreateUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if "username" in data and data["username"] != clerk.user.username:
            if User.objects.filter(username=data["username"]).exclude(pk=clerk.user.pk).exists():
                return Response({"username": ["Username already exists."]}, status=400)
            clerk.user.username = data["username"]
        if "phone_number" in data and data["phone_number"] != clerk.user.phone_number:
            if data["phone_number"] and User.objects.filter(phone_number=data["phone_number"]).exclude(pk=clerk.user.pk).exists():
                return Response({"phone_number": ["Phone number already exists."]}, status=400)
            clerk.user.phone_number = data["phone_number"] or None
            clerk.phone_number = data["phone_number"]
        if data.get("password"):
            clerk.user.set_password(data["password"])
        clerk.user.save()
        for attr in ["full_name", "assigned_hostel"]:
            if attr in data:
                setattr(clerk, attr, data[attr])
        clerk.save()
        return Response(ClerkSerializer(clerk).data)

    def destroy(self, request, *args, **kwargs):
        clerk = self.get_object()
        user = clerk.user
        clerk.delete()
        user.delete()
        return Response(status=204)


class ComplaintListApiView(generics.ListAPIView):
    serializer_class = ComplaintSerializer

    def get_queryset(self):
        queryset = Complaint.objects.select_related("student").prefetch_related("status_history", "status_history__changed_by_user")
        status_filter = self.request.GET.get("status")
        q = (self.request.GET.get("q") or "").strip()
        role = self.request.user.role
        if role == User.ROLE_STUDENT:
            queryset = queryset.filter(student=getattr(self.request.user, "student_profile", None))
        elif role == User.ROLE_CLERK:
            clerk = getattr(self.request.user, "clerk_profile", None)
            if clerk:
                queryset = queryset.filter(hostel_snapshot=clerk.assigned_hostel)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if q:
            queryset = queryset.filter(Q(description__icontains=q) | Q(student_name_snapshot__icontains=q) | Q(room_number_snapshot__icontains=q) | Q(worker_name__icontains=q))
        return queryset


class StudentComplaintCreateApiView(APIView):
    permission_classes = [IsStudentRole]

    def post(self, request):
        serializer = ComplaintCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = request.user.student_profile
        complaint = create_student_complaint(
            student=student,
            description=serializer.validated_data["description"],
        )
        return Response(ComplaintSerializer(complaint).data, status=201)


class ComplaintActionApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, action):
        complaint = get_object_or_404(Complaint, pk=pk)
        if request.user.role == User.ROLE_STUDENT:
            student = getattr(request.user, "student_profile", None)
            if not student or complaint.student_id != student.id:
                return Response({"detail": "Forbidden"}, status=403)
            if action not in {"mark-solved", "mark-unsolved"}:
                return Response({"detail": "Forbidden"}, status=403)
        elif request.user.role == User.ROLE_CLERK:
            clerk = getattr(request.user, "clerk_profile", None)
            if not clerk or complaint.hostel_snapshot != clerk.assigned_hostel:
                return Response({"detail": "Forbidden"}, status=403)
        if action == "assign-worker":
            assign_worker_and_start(complaint=complaint, worker_name=(request.data.get("worker_name") or "").strip(), changed_by_user=request.user)
        elif action == "mark-completed":
            mark_completed(complaint=complaint, changed_by_user=request.user)
        elif action == "mark-solved":
            mark_solved(complaint=complaint, changed_by_user=request.user)
        elif action == "mark-unsolved":
            mark_unsolved(complaint=complaint, changed_by_user=request.user)
        elif action == "reopen":
            reopen_unsolved(complaint=complaint, changed_by_user=request.user, new_worker_name=(request.data.get("worker_name") or "").strip() or None)
        else:
            return Response({"detail": "Unknown action."}, status=400)
        complaint.refresh_from_db()
        return Response(ComplaintSerializer(complaint).data)


class SubjectListApiView(generics.ListAPIView):
    queryset = Subject.objects.all().order_by("name")
    serializer_class = SubjectSerializer


class AcademicListCreateApiView(generics.ListCreateAPIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = AcademicFile.objects.select_related("department", "subject")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            queryset = queryset.filter(Q(course_code__icontains=q) | Q(subject__name__icontains=q) | Q(department__name__icontains=q))
        return queryset

    def get_serializer_class(self):
        return AcademicFileSerializer if self.request.method == "GET" else AcademicFileCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = AcademicFileCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = getattr(request.user, "student_profile", None)
        obj = serializer.save(uploaded_by_student=student, uploaded_by_name_snapshot=(student.full_name if student else request.user.get_display_name()))
        return Response(AcademicFileSerializer(obj, context={"request": request}).data, status=201)


class AcademicDetailApiView(generics.RetrieveDestroyAPIView):
    queryset = AcademicFile.objects.select_related("department", "subject")
    serializer_class = AcademicFileSerializer
    permission_classes = [IsAdminOrClerkRole]

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete()
        return Response(status=204)


class AcademicDownloadApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        obj = get_object_or_404(AcademicFile.objects.select_related("department", "subject"), pk=pk)
        if request.user.role == User.ROLE_STUDENT:
            student = getattr(request.user, "student_profile", None)
            if not student:
                return Response({"detail": "Forbidden"}, status=403)
        elif request.user.role not in {User.ROLE_ADMIN, User.ROLE_CLERK}:
            return Response({"detail": "Forbidden"}, status=403)

        if not obj.file or not obj.file.storage.exists(obj.file.name):
            return Response({"detail": "File not found."}, status=404)

        return FileResponse(
            obj.file.open("rb"),
            as_attachment=True,
            filename=os.path.basename(obj.file.name),
        )


class FeedbackFormListApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role == User.ROLE_ADMIN:
            forms = get_all_feedback_forms().prefetch_related("questions")
            return Response(FeedbackFormSerializer(forms, many=True).data)
        student = getattr(request.user, "student_profile", None)
        if not student:
            return Response([])
        active = get_active_feedback_form_for_hostel(student.hostel)
        if not active:
            return Response([])
        data = FeedbackFormSerializer(active).data
        data["already_submitted"] = has_student_submitted_feedback(active, student)
        return Response([data])

    def post(self, request):
        if request.user.role != User.ROLE_ADMIN:
            return Response({"detail": "Forbidden"}, status=403)
        serializer = FeedbackFormCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            form = create_feedback_form_with_questions(
                admin_user=request.user,
                name=serializer.validated_data["name"],
                hostel=serializer.validated_data["hostel"],
                duration_hours=serializer.validated_data["duration_hours"],
                questions=serializer.validated_data["questions"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(FeedbackFormSerializer(form).data, status=201)


class FeedbackFormActionApiView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, pk, action):
        form = get_object_or_404(FeedbackForm, pk=pk)
        try:
            if action == "stop":
                stop_feedback_form(form)
            elif action == "delete":
                delete_feedback_form(form)
            else:
                return Response({"detail": "Unknown action."}, status=400)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response({"detail": "OK"})


class FeedbackSubmitApiView(APIView):
    permission_classes = [IsStudentRole]

    def post(self, request, pk):
        student = request.user.student_profile
        form = get_object_or_404(FeedbackForm.objects.prefetch_related("questions"), pk=pk)
        if form.hostel != student.hostel:
            return Response({"detail": "This feedback form is not available for your hostel."}, status=403)
        answers = request.data.get("answers") or {}
        submission = submit_feedback_form(form, student, {str(k): v for k, v in answers.items()})
        return Response({"submission_id": submission.id}, status=201)


class FeedbackAnalysisApiView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, pk):
        form = get_object_or_404(FeedbackForm.objects.prefetch_related("questions", "submissions__student", "submissions__answers__question"), pk=pk)
        return Response(build_feedback_analysis(form))


class LockedAccountsApiView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        users = User.objects.filter(is_locked=True).order_by("role", "username", "phone_number")
        return Response(UserSerializer(users, many=True).data)

    def post(self, request):
        user = get_object_or_404(User, pk=request.data.get("user_id"), is_locked=True)
        user.unlock_account()
        return Response({"detail": "Account unlocked."})


class SystemSettingsApiView(APIView):
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        return Response(SystemSettingsSerializer(SystemSettings.get_solo()).data)

    def patch(self, request):
        settings_obj = SystemSettings.get_solo()
        serializer = SystemSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(SystemSettingsSerializer(settings_obj).data)

    def put(self, request):
        return self.patch(request)


class BackupListApiView(generics.ListAPIView):
    queryset = BackupRecord.objects.select_related("created_by_user").all()
    serializer_class = BackupRecordSerializer
    permission_classes = [IsAdminRole]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def post(self, request):
        try:
            temp_path, file_name = create_mysql_backup()
            with open(temp_path, "rb") as backup_file:
                record = BackupRecord(created_by_user=request.user)
                record.backup_file.save(file_name, backup_file, save=True)
            if temp_path:
                import os
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            return Response(BackupRecordSerializer(record, context={"request": request}).data, status=201)
        except Exception as exc:
            return Response({"detail": f"Backup failed: {exc}"}, status=400)


class BackupActionApiView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, pk, action):
        backup = get_object_or_404(BackupRecord, pk=pk)
        if action == "restore":
            if not backup.backup_file:
                return Response({"detail": "Backup file not found."}, status=400)
            try:
                restore_mysql_backup(backup.backup_file.path)
            except Exception as exc:
                return Response({"detail": f"Restore failed: {exc}"}, status=400)
            return Response({"detail": "Database restored successfully."})
        if action == "delete":
            backup.delete()
            return Response({"detail": "Deleted."})
        return Response({"detail": "Unknown action."}, status=400)

    def get(self, request, pk, action):
        if action != "download":
            return Response({"detail": "Unknown action."}, status=400)
        backup = get_object_or_404(BackupRecord, pk=pk)
        if not backup.backup_file:
            return Response({"detail": "Backup file not found."}, status=404)
        return FileResponse(
            backup.backup_file.open("rb"),
            as_attachment=True,
            filename=backup.backup_file.name.split("/")[-1],
        )
