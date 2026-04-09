from django.contrib import admin

from .models import (
    FeedbackForm,
    FeedbackQuestion,
    FeedbackSubmission,
    FeedbackAnswer,
)


class FeedbackQuestionInline(admin.TabularInline):
    model = FeedbackQuestion
    extra = 0


@admin.register(FeedbackForm)
class FeedbackFormAdmin(admin.ModelAdmin):
    list_display = ("name", "hostel", "status", "created_at", "activated_at", "expires_at")
    list_filter = ("hostel", "status")
    search_fields = ("name",)
    inlines = [FeedbackQuestionInline]


@admin.register(FeedbackSubmission)
class FeedbackSubmissionAdmin(admin.ModelAdmin):
    list_display = ("feedback_form", "student", "submitted_at")
    list_filter = ("feedback_form",)
    search_fields = ("feedback_form__name", "student__full_name", "student__phone_number")


@admin.register(FeedbackAnswer)
class FeedbackAnswerAdmin(admin.ModelAdmin):
    list_display = ("submission", "question", "answer_value")
    list_filter = ("question__feedback_form",)
    search_fields = ("submission__feedback_form__name", "question__question_text", "answer_value")