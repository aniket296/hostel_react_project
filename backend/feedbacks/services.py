from collections import Counter
import csv
from io import StringIO

from django.db import transaction
from django.utils import timezone

from .models import FeedbackForm, FeedbackSubmission, FeedbackAnswer, FeedbackQuestion


def expire_feedback_forms_if_needed():
    active_forms = FeedbackForm.objects.filter(status=FeedbackForm.STATUS_ACTIVE)
    now = timezone.now()

    for feedback_form in active_forms:
        if feedback_form.expires_at and now >= feedback_form.expires_at:
            feedback_form.status = FeedbackForm.STATUS_EXPIRED
            feedback_form.save(update_fields=["status"])


def validate_single_active_form_per_hostel(hostel):
    expire_feedback_forms_if_needed()

    return not FeedbackForm.objects.filter(
        hostel=hostel,
        status=FeedbackForm.STATUS_ACTIVE,
    ).exists()


# 🔥 UPDATED: supports dynamic question types
@transaction.atomic
def create_feedback_form_with_questions(*, admin_user, name, hostel, duration_hours, questions):
    if not validate_single_active_form_per_hostel(hostel):
        raise ValueError("An active feedback form already exists for the selected hostel.")

    if not questions:
        raise ValueError("At least one question is required.")

    valid_question_types = {choice[0] for choice in FeedbackQuestion.QUESTION_TYPE_CHOICES}
    normalized_questions = []

    for index, q in enumerate(questions, start=1):
        question_text = (q.get("text") or "").strip()
        question_type = q.get("type", FeedbackQuestion.TYPE_RATING)
        radio_options = q.get("options", "")

        if not question_text:
            continue

        if question_type not in valid_question_types:
            raise ValueError("Invalid feedback question type.")

        cleaned_options = [opt.strip() for opt in radio_options.splitlines() if opt.strip()]
        if question_type == FeedbackQuestion.TYPE_RADIO and not cleaned_options:
            raise ValueError(f"Radio question {index} must include at least one option.")

        normalized_questions.append(
            {
                "question_text": question_text,
                "question_type": question_type,
                "radio_options": "\n".join(cleaned_options) if question_type == FeedbackQuestion.TYPE_RADIO else "",
            }
        )

    if not normalized_questions:
        raise ValueError("At least one valid question is required.")

    feedback_form = FeedbackForm.objects.create(
        name=name.strip(),
        hostel=hostel,
        duration_hours=duration_hours,
        status=FeedbackForm.STATUS_ACTIVE,
        created_by=admin_user,
    )

    for display_order, question in enumerate(normalized_questions, start=1):
        FeedbackQuestion.objects.create(
            feedback_form=feedback_form,
            question_text=question["question_text"],
            question_type=question["question_type"],
            radio_options=question["radio_options"],
            display_order=display_order,
        )

    return feedback_form


def delete_feedback_form(feedback_form):
    feedback_form.delete()


def get_active_feedback_form_for_hostel(hostel):
    expire_feedback_forms_if_needed()

    return (
        FeedbackForm.objects.filter(
            hostel=hostel,
            status=FeedbackForm.STATUS_ACTIVE,
        )
        .prefetch_related("questions")
        .order_by("-created_at")
        .first()
    )


def has_student_submitted_feedback(feedback_form, student):
    return FeedbackSubmission.objects.filter(
        feedback_form=feedback_form,
        student=student,
    ).exists()


# 🔥 UPDATED: supports all answer types
@transaction.atomic
def submit_feedback_form(*, feedback_form, student, answers_by_question_id):
    feedback_form.mark_expired_if_needed()

    if not feedback_form.is_available_to_students:
        raise ValueError("This feedback form is no longer active.")

    if has_student_submitted_feedback(feedback_form, student):
        raise ValueError("You have already submitted feedback.")

    questions = list(feedback_form.questions.all())

    submission = FeedbackSubmission.objects.create(
        feedback_form=feedback_form,
        student=student,
    )

    for question in questions:
        value = (answers_by_question_id.get(str(question.id)) or "").strip()

        if not value:
            raise ValueError("Please answer all questions.")

        # 🔹 validation based on type
        if question.question_type == "rating":
            if value not in ["1", "2", "3", "4", "5"]:
                raise ValueError("Invalid rating value.")

        elif question.question_type == "radio":
            valid_options = question.get_radio_options_list()
            if value not in valid_options:
                raise ValueError("Invalid radio option selected.")

        # text / textarea → no restriction

        FeedbackAnswer.objects.create(
            submission=submission,
            question=question,
            answer_value=value,
        )

    return submission


def get_all_feedback_forms():
    expire_feedback_forms_if_needed()
    return FeedbackForm.objects.all().order_by("-created_at")


def stop_feedback_form(feedback_form):
    feedback_form.mark_expired_if_needed()

    if feedback_form.status != FeedbackForm.STATUS_ACTIVE:
        raise ValueError("Only active feedback forms can be stopped.")

    feedback_form.stop()
    return feedback_form


# 🔥 UPDATED: only applies stats for rating questions
def build_feedback_form_question_stats(feedback_form):
    questions = feedback_form.questions.all()
    stats = []

    for question in questions:
        if question.question_type != "rating":
            continue

        values = list(
            FeedbackAnswer.objects.filter(question=question)
            .values_list("answer_value", flat=True)
        )

        ratings = [int(v) for v in values if v.isdigit()]
        total = len(ratings)
        counter = Counter(ratings)

        stats.append(
            {
                "question": question,
                "total_responses": total,
                "most_frequent_rating": counter.most_common(1)[0][0] if counter else "-",
                "average_rating": round(sum(ratings) / total, 2) if total else "-",
                "count_1": counter.get(1, 0),
                "count_2": counter.get(2, 0),
                "count_3": counter.get(3, 0),
                "count_4": counter.get(4, 0),
                "count_5": counter.get(5, 0),
            }
        )

    return stats


def build_feedback_analysis(feedback_form):
    questions = list(feedback_form.questions.all())
    question_stats = build_feedback_form_question_stats(feedback_form)

    submissions = feedback_form.submissions.prefetch_related("answers__question")

    student_rows = []

    for submission in submissions:
        answer_map = {a.question_id: a.answer_value for a in submission.answers.all()}

        student_rows.append(
            {
                "student_name": submission.student.full_name,
                "ratings": [answer_map.get(q.id, "-") for q in questions],
            }
        )

    return {
        "question_stats": question_stats,
        "questions": questions,
        "student_rows": student_rows,
    }


def export_feedback_analysis_csv(feedback_form):
    questions = list(feedback_form.questions.all().order_by("display_order", "id"))
    question_stats = build_feedback_form_question_stats(feedback_form)

    submissions = (
        feedback_form.submissions
        .select_related("student")
        .prefetch_related("answers__question")
        .order_by("-submitted_at")
    )

    output = StringIO()
    writer = csv.writer(output)

    # =========================
    # SECTION 1: OVERALL ANALYSIS
    # =========================
    writer.writerow(["OVERALL ANALYSIS"])
    writer.writerow(
        [
            "Form Name",
            "Hostel",
            "Question",
            "Most Frequent Rating",
            "Average Rating",
            "Count 1",
            "Count 2",
            "Count 3",
            "Count 4",
            "Count 5",
            "Total Responses",
        ]
    )

    for item in question_stats:
        writer.writerow(
            [
                feedback_form.name,
                feedback_form.get_hostel_display(),
                item["question"].question_text,
                item["most_frequent_rating"],
                item["average_rating"],
                item["count_1"],
                item["count_2"],
                item["count_3"],
                item["count_4"],
                item["count_5"],
                item["total_responses"],
            ]
        )

    # blank row separator
    writer.writerow([])
    writer.writerow([])

    # =========================
    # SECTION 2: STUDENT FEEDBACK DETAILS
    # =========================
    writer.writerow(["STUDENT FEEDBACK DETAILS"])

    student_header = ["Student Name"]
    for index, question in enumerate(questions, start=1):
        student_header.append(f"Q{index}: {question.question_text}")
    writer.writerow(student_header)

    for submission in submissions:
        answer_map = {answer.question_id: answer.answer_value for answer in submission.answers.all()}

        row = [submission.student.full_name]
        for question in questions:
            row.append(answer_map.get(question.id, "-"))

        writer.writerow(row)

    return output.getvalue()