from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from accounts.decorators import admin_required, student_required
from .forms import FeedbackFormCreateForm
from .models import FeedbackForm
from .services import (
    build_feedback_analysis,
    create_feedback_form_with_questions,
    delete_feedback_form,
    export_feedback_analysis_csv,
    get_active_feedback_form_for_hostel,
    get_all_feedback_forms,
    has_student_submitted_feedback,
    stop_feedback_form,
    submit_feedback_form,
)


@admin_required
@require_http_methods(["GET", "POST"])
def admin_feedback_create_view(request):
    form = FeedbackFormCreateForm(request.POST or None)

    if request.method == "POST":
        question_texts = request.POST.getlist("questions[]")
        question_types = request.POST.getlist("question_types[]")
        radio_options_list = request.POST.getlist("radio_options[]")

        questions = []

        for i in range(len(question_texts)):
            text = (question_texts[i] or "").strip()
            q_type = question_types[i] if i < len(question_types) else "rating"
            options = radio_options_list[i] if i < len(radio_options_list) else ""

            if not text:
                continue

            questions.append({
                "text": text,
                "type": q_type,
                "options": options,
            })

        if form.is_valid():
            try:
                create_feedback_form_with_questions(
                    admin_user=request.user,
                    name=form.cleaned_data["name"],
                    hostel=form.cleaned_data["hostel"],
                    duration_hours=form.cleaned_data["duration_hours"],
                    questions=questions,
                )
                messages.success(request, "Hostel Feedback form created and activated successfully.")
                return redirect("admin_feedback_create")
            except ValueError as e:
                form.add_error(None, str(e))

    return render(
        request,
        "admin_panel/feedbacks/create_form.html",
        {
            "form": form,
        },
    )


@admin_required
@require_http_methods(["GET"])
def admin_feedback_form_list_view(request):
    feedback_forms = get_all_feedback_forms()

    return render(
        request,
        "admin_panel/feedbacks/form_list.html",
        {
            "feedback_forms": feedback_forms,
        },
    )

@admin_required
@require_http_methods(["GET"])
def admin_feedback_form_view(request, pk):
    feedback_form = get_object_or_404(
        FeedbackForm.objects.prefetch_related("questions"),
        pk=pk,
    )

    return render(
        request,
        "admin_panel/feedbacks/form_view.html",
        {
            "feedback_form": feedback_form,
        },
    )


@admin_required
@require_http_methods(["POST"])
def admin_feedback_form_stop_view(request, pk):
    feedback_form = get_object_or_404(FeedbackForm, pk=pk)

    try:
        stop_feedback_form(feedback_form)
        messages.success(request, "Feedback form stopped successfully.")
    except ValueError as e:
        messages.error(request, str(e))

    return redirect("admin_feedback_form_list")


@admin_required
@require_http_methods(["POST"])
def admin_feedback_form_delete_view(request, pk):
    feedback_form = get_object_or_404(FeedbackForm, pk=pk)

    delete_feedback_form(feedback_form)
    messages.success(request, "Feedback form and all related data deleted successfully.")
    return redirect("admin_feedback_form_list")


@admin_required
@require_http_methods(["GET"])
def admin_feedback_analysis_list_view(request):
    feedback_forms = get_all_feedback_forms()

    return render(
        request,
        "admin_panel/feedbacks/analysis_list.html",
        {
            "feedback_forms": feedback_forms,
        },
    )


@admin_required
@require_http_methods(["GET"])
def admin_feedback_analysis_view(request, pk):
    feedback_form = get_object_or_404(
        FeedbackForm.objects.prefetch_related("questions", "submissions"),
        pk=pk,
    )

    analysis = build_feedback_analysis(feedback_form)

    return render(
        request,
        "admin_panel/feedbacks/analysis_view.html",
        {
            "feedback_form": feedback_form,
            **analysis,
        },
    )


@admin_required
@require_http_methods(["GET"])
def admin_feedback_analysis_export_view(request, pk):
    feedback_form = get_object_or_404(FeedbackForm, pk=pk)
    csv_content = export_feedback_analysis_csv(feedback_form)

    response = HttpResponse(csv_content, content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="feedback_analysis_{feedback_form.pk}.csv"'
    return response


@student_required
@require_http_methods(["GET", "POST"])
def student_feedback_page_view(request):
    student = getattr(request.user, "student_profile", None)

    if not student:
        messages.error(request, "Student profile not found.")
        return redirect("student_dashboard")

    active_form = get_active_feedback_form_for_hostel(student.hostel)

    if not active_form:
        return render(
            request,
            "student/feedbacks/feedback_page.html",
            {
                "page_mode": "no_form",
            },
        )

    if has_student_submitted_feedback(active_form, student):
        return render(
            request,
            "student/feedbacks/feedback_page.html",
            {
                "page_mode": "already_submitted",
                "feedback_form": active_form,
            },
        )

    if request.method == "POST":
        answers_by_question_id = {}
        for question in active_form.questions.all():
            answers_by_question_id[str(question.id)] = request.POST.get(f"question_{question.id}", "")

        try:
            submit_feedback_form(
                feedback_form=active_form,
                student=student,
                answers_by_question_id=answers_by_question_id,
            )
            messages.success(request, "Your feedback has been submitted successfully.")
            return redirect("student_feedback_page")
        except ValueError as e:
            messages.error(request, str(e))

    return render(
        request,
        "student/feedbacks/feedback_page.html",
        {
            "page_mode": "active_form",
            "feedback_form": active_form,
            "questions": active_form.questions.all(),
            "rating_choices": [1, 2, 3, 4, 5],
        },
    )