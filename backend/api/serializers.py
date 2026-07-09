from django.contrib.auth import get_user_model
from rest_framework import serializers
from students.models import Student, Department
from clerks.models import Clerk
from complaints.models import Complaint, ComplaintStatusHistory
from academics.models import AcademicFile, Subject
from feedbacks.models import FeedbackForm, FeedbackQuestion, FeedbackSubmission, FeedbackAnswer
from core.models import SystemSettings, BackupRecord

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    hostel = serializers.SerializerMethodField()
    room_number = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "phone_number", "role", "is_locked",
            "display_name", "full_name", "hostel", "room_number",
        ]

    def get_display_name(self, obj):
        student = getattr(obj, "student_profile", None)
        if student and student.full_name:
            return student.full_name
        return obj.get_display_name()

    def get_full_name(self, obj):
        student = getattr(obj, "student_profile", None)
        return student.full_name if student else obj.get_display_name()

    def get_hostel(self, obj):
        student = getattr(obj, "student_profile", None)
        return getattr(student, "hostel", None)

    def get_room_number(self, obj):
        student = getattr(obj, "student_profile", None)
        return getattr(student, "room_number", "")


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "created_at", "updated_at"]


class StudentSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Student
        fields = ["id", "user", "full_name", "phone_number", "department", "department_name", "year", "gender", "hostel", "room_number", "created_at", "updated_at"]


class StudentCreateUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)

    class Meta:
        model = Student
        fields = ["full_name", "phone_number", "department", "year", "gender", "room_number", "password"]


class ClerkSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)

    class Meta:
        model = Clerk
        fields = ["id", "user_id", "username", "full_name", "phone_number", "assigned_hostel", "created_at", "updated_at"]


class ClerkCreateUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Clerk
        fields = ["username", "password", "full_name", "phone_number", "assigned_hostel"]


class ComplaintHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ComplaintStatusHistory
        fields = ["id", "status", "changed_by_role_snapshot", "changed_by_name", "timestamp"]

    def get_changed_by_name(self, obj):
        return obj.changed_by_user.get_display_name() if obj.changed_by_user else ""


class ComplaintSerializer(serializers.ModelSerializer):
    status_history = ComplaintHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Complaint
        fields = ["id", "student", "student_name_snapshot", "student_phone_snapshot", "department_name_snapshot", "year_snapshot", "hostel_snapshot", "room_number_snapshot", "description", "worker_name", "status", "created_at", "updated_at", "completed_at", "solved_at", "unsolved_at", "status_history"]


class ComplaintCreateSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=100)
    room_number = serializers.CharField(max_length=20, required=False, allow_blank=True)


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name"]


class AcademicFileSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    uploaded_by_name = serializers.CharField(source="uploaded_by_name_snapshot", read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = AcademicFile
        fields = [
            "id", "department", "department_name", "year", "subject", "subject_name",
            "course_code", "description", "file_type", "original_file_name", "stored_file_name",
            "file_extension", "file_size", "file_hash", "uploaded_by_name_snapshot",
            "uploaded_by_name", "created_at", "updated_at", "download_url"
        ]

    def get_download_url(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(f"/media/{obj.file.name}")
        return obj.file.url if obj.file else ""


class AcademicFileCreateSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(write_only=True, required=False, allow_blank=False)
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all(), required=False, allow_null=True)
    file_type = serializers.ChoiceField(choices=[
        (AcademicFile.TYPE_PYQ_PT, "PYQ PT"),
        (AcademicFile.TYPE_PYQ_SEMESTER, "PYQ Semester"),
        (AcademicFile.TYPE_NOTES, "Notes"),
        (AcademicFile.TYPE_QUESTION_BANK, "Question Bank"),
        (AcademicFile.TYPE_CURRICULUM, "Curriculum"),
    ])

    class Meta:
        model = AcademicFile
        fields = ["department", "year", "subject", "subject_name", "course_code", "description", "file_type", "file"]

    def validate(self, attrs):
        subject = attrs.get("subject")
        subject_name = (attrs.get("subject_name") or "").strip()
        if not subject and not subject_name:
            raise serializers.ValidationError({"subject_name": "Subject name is required."})
        return attrs

    def create(self, validated_data):
        subject = validated_data.pop("subject", None)
        subject_name = (validated_data.pop("subject_name", "") or "").strip()
        if subject is None:
            subject, _ = Subject.objects.get_or_create(name=subject_name)
        validated_data["subject"] = subject
        return super().create(validated_data)

class FeedbackQuestionSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source="question_text", read_only=True)
    order = serializers.IntegerField(source="display_order", read_only=True)

    class Meta:
        model = FeedbackQuestion
        fields = ["id", "text", "question_type", "radio_options", "order"]


class FeedbackFormSerializer(serializers.ModelSerializer):
    questions = FeedbackQuestionSerializer(many=True, read_only=True)
    is_active = serializers.SerializerMethodField()
    started_at = serializers.DateTimeField(source="activated_at", read_only=True)
    ends_at = serializers.DateTimeField(source="expires_at", read_only=True)

    class Meta:
        model = FeedbackForm
        fields = ["id", "name", "hostel", "duration_hours", "status", "is_active", "started_at", "ends_at", "created_at", "questions"]

    def get_is_active(self, obj):
        return obj.is_available_to_students


class FeedbackFormCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    hostel = serializers.ChoiceField(choices=FeedbackForm.HOSTEL_CHOICES)
    duration_hours = serializers.IntegerField()
    questions = serializers.ListField(child=serializers.DictField(), allow_empty=False)


class FeedbackAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question.question_text", read_only=True)
    answer_text = serializers.CharField(source="answer_value", read_only=True)

    class Meta:
        model = FeedbackAnswer
        fields = ["id", "question", "question_text", "answer_text"]


class FeedbackSubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    answers = FeedbackAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = FeedbackSubmission
        fields = ["id", "student", "student_name", "submitted_at", "answers"]


class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = ["id", "college_name", "system_title", "college_logo", "header_photo", "maintenance_mode", "updated_at"]


class BackupRecordSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by_user.username", read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = BackupRecord
        fields = ["id", "backup_file", "created_by", "created_at", "notes", "download_url"]

    def get_download_url(self, obj):
        request = self.context.get("request")
        if request and obj.backup_file:
            return request.build_absolute_uri(f"/media/{obj.backup_file.name}")
        return obj.backup_file.url if obj.backup_file else ""
