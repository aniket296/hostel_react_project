from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import F
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import LoginForm
from .models import User


def get_dashboard_url(user):
    if user.role == User.ROLE_STUDENT:
        return "student_dashboard"
    if user.role == User.ROLE_CLERK:
        return "clerk_dashboard"
    if user.role == User.ROLE_ADMIN:
        return "admin_dashboard"
    return "login"


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect(get_dashboard_url(request.user))

    form = LoginForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            username_or_phone = request.POST.get("identifier", "").strip()
            password = request.POST.get("password", "")

            user = None
            try:
                user = User.objects.get(phone_number=username_or_phone)
            except User.DoesNotExist:
                try:
                    user = User.objects.get(username=username_or_phone)
                except User.DoesNotExist:
                    user = None

            if user and user.is_locked and user.role != User.ROLE_ADMIN:
                messages.error(request, "Account locked. Please contact Admin.")
                return render(request, "accounts/login.html", {"form": form})

            authenticated_user = authenticate(
                request,
                username=username_or_phone,
                password=password,
            )

            if authenticated_user is not None:
                authenticated_user.reset_login_attempts()
                login(request, authenticated_user)
                messages.success(
                    request,
                    f"Welcome, {authenticated_user.get_display_name()}!",
                )
                return redirect(get_dashboard_url(authenticated_user))

            if user:
                if user.role == User.ROLE_ADMIN:
                    messages.error(request, "Invalid credentials.")
                else:
                    # V-09 fix: use atomic F() expression to avoid race condition when
                    # concurrent bad-password attempts read the same stale counter value.
                    User.objects.filter(pk=user.pk).update(
                        failed_login_attempts=F("failed_login_attempts") + 1
                    )
                    user.refresh_from_db(fields=["failed_login_attempts"])
                    if user.failed_login_attempts >= 3:
                        User.objects.filter(pk=user.pk).update(is_locked=True)
                        messages.error(request, "Account locked. Please contact Admin.")
                    else:
                        remaining = 3 - user.failed_login_attempts
                        messages.error(
                            request,
                            f"Invalid credentials. {remaining} attempt(s) remaining.",
                        )
            else:
                messages.error(request, "Invalid credentials.")

    return render(request, "accounts/login.html", {"form": form})


@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")