from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from students.models import Student


class FeedbackForm(models.Model):
    HOSTEL_BOYS = "boys_hostel"
    HOSTEL_GIRLS = "girls_hostel"

    HOSTEL_CHOICES = [
        (HOSTEL_BOYS, "Boys Hostel"),
        (HOSTEL_GIRLS, "Girls Hostel"),
    ]

    STATUS_ACTIVE = "active"
    STATUS_STOPPED = "stopped"
    STATUS_EXPIRED = "expired"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_STOPPED, "Stopped"),
        (STATUS_EXPIRED, "Expired"),
    ]

    DURATION_12 = 12
    DURATION_24 = 24
    DURATION_48 = 48
    DURATION_72 = 72
    DURATION_168 = 168

    DURATION_CHOICES = [
        (DURATION_12, "12 Hours"),
        (DURATION_24, "24 Hours"),
        (DURATION_48, "48 Hours"),
        (DURATION_72, "72 Hours"),
        (DURATION_168, "7 Days"),
    ]

    name = models.CharField(max_length=200)
    hostel = models.CharField(max_length=20, choices=HOSTEL_CHOICES)
    duration_hours = models.PositiveIntegerField(choices=DURATION_CHOICES)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_feedback_forms",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(blank=True, null=True)
    stopped_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.get_hostel_display()}"

    def save(self, *args, **kwargs):
        if not self.activated_at:
            self.activated_at = timezone.now()

        if not self.expires_at:
            self.expires_at = self.activated_at + timedelta(hours=self.duration_hours)

        super().save(*args, **kwargs)

    @property
    def is_expired_by_time(self):
        return self.expires_at and timezone.now() >= self.expires_at

    @property
    def is_available_to_students(self):
        return self.status == self.STATUS_ACTIVE and not self.is_expired_by_time

    def mark_expired_if_needed(self):
        if self.status == self.STATUS_ACTIVE and self.is_expired_by_time:
            self.status = self.STATUS_EXPIRED
            self.save(update_fields=["status"])

    def stop(self):
        self.status = self.STATUS_STOPPED
        self.stopped_at = timezone.now()
        self.save(update_fields=["status", "stopped_at"])


class FeedbackQuestion(models.Model):
    TYPE_RATING = "rating"
    TYPE_RADIO = "radio"
    TYPE_TEXT = "text"
    TYPE_TEXTAREA = "textarea"

    QUESTION_TYPE_CHOICES = [
        (TYPE_RATING, "Rating Dropdown"),
        (TYPE_RADIO, "Radio Choice"),
        (TYPE_TEXT, "Text Input"),
        (TYPE_TEXTAREA, "Textarea"),
    ]

    feedback_form = models.ForeignKey(
        FeedbackForm,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    question_text = models.CharField(max_length=500)
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default=TYPE_RATING,
    )
    radio_options = models.TextField(
        blank=True,
        default="",
        help_text="For radio type only. Enter one option per line.",
    )
    display_order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["display_order", "id"]

    def __str__(self):
        return self.question_text

    def get_radio_options_list(self):
        return [opt.strip() for opt in self.radio_options.splitlines() if opt.strip()]


class FeedbackSubmission(models.Model):
    feedback_form = models.ForeignKey(
        FeedbackForm,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="feedback_submissions",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["feedback_form", "student"],
                name="unique_feedback_submission_per_student_per_form",
            )
        ]

    def __str__(self):
        return f"{self.feedback_form.name} - Submission #{self.pk}"


class FeedbackAnswer(models.Model):
    submission = models.ForeignKey(
        FeedbackSubmission,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        FeedbackQuestion,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    answer_value = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "question"],
                name="unique_feedback_answer_per_question_per_submission",
            )
        ]

    def __str__(self):
        return f"{self.question.question_text} - {self.answer_value}"