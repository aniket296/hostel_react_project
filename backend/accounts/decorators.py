from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseForbidden


def role_required(required_role):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")

            if getattr(request.user, "is_locked", False) and getattr(request.user, "role", None) != "admin":
                messages.error(request, "Account locked. Please contact Admin.")
                return redirect("login")

            if getattr(request.user, "role", None) != required_role:
                return HttpResponseForbidden()

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


student_required = role_required("student")
clerk_required = role_required("clerk")
admin_required = role_required("admin")