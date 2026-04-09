from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from accounts.decorators import admin_required
from .forms import ClerkCreateForm, ClerkEditForm
from .models import Clerk

User = get_user_model()


@admin_required
@require_http_methods(["GET"])
def clerk_list_view(request):
    clerks = Clerk.objects.all()
    return render(
        request,
        "admin_panel/clerks/clerk_list.html",
        {"clerks": clerks},
    )


@admin_required
@require_http_methods(["GET", "POST"])
def clerk_add_view(request):
    form = ClerkCreateForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        phone_number = form.cleaned_data.get("phone_number", "").strip()

        if User.objects.filter(username=username).exists():
            form.add_error("username", "Username already exists.")
        elif phone_number and User.objects.filter(phone_number=phone_number).exists():
            form.add_error("phone_number", "Phone number already exists.")
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                phone_number=phone_number or None,
                role="clerk",
            )

            clerk = form.save(commit=False)
            clerk.user = user
            clerk.save()

            messages.success(request, "Clerk created successfully.")
            return redirect("clerk_list")

    return render(
        request,
        "admin_panel/clerks/add_clerk.html",
        {"form": form},
    )


@admin_required
@require_http_methods(["GET", "POST"])
def clerk_edit_view(request, pk):
    clerk = get_object_or_404(Clerk, pk=pk)
    form = ClerkEditForm(request.POST or None, instance=clerk)

    if request.method == "POST" and form.is_valid():
        phone_number = form.cleaned_data.get("phone_number", "").strip()

        existing_user = User.objects.filter(phone_number=phone_number).exclude(pk=clerk.user.pk).first()
        if phone_number and existing_user:
            form.add_error("phone_number", "Phone number already exists.")
        else:
            clerk = form.save()
            clerk.user.phone_number = phone_number or None
            clerk.user.save(update_fields=["phone_number"])

            messages.success(request, "Clerk updated successfully.")
            return redirect("clerk_list")

    return render(
        request,
        "admin_panel/clerks/edit_clerk.html",
        {"form": form},
    )


@admin_required
@require_http_methods(["POST"])
def clerk_delete_view(request, pk):
    clerk = get_object_or_404(Clerk, pk=pk)

    if request.method == "POST":
        user = clerk.user
        clerk.delete()
        user.delete()

        messages.success(request, "Clerk deleted successfully.")

    return redirect("clerk_list")