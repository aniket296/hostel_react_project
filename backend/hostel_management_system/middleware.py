from django.shortcuts import render
from django.urls import Resolver404, resolve
from core.models import SystemSettings


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        settings_obj = SystemSettings.get_solo()

        if settings_obj.maintenance_mode:
            allowed_names = {
                "login",
                "logout",
            }

            current_url_name = ""
            try:
                current_url_name = resolve(request.path_info).url_name or ""
            except Resolver404:
                current_url_name = ""

            user = getattr(request, "user", None)
            is_admin_user = (
                user is not None
                and getattr(user, "is_authenticated", False)
                and getattr(user, "role", None) == "admin"
            )

            if not is_admin_user and current_url_name not in allowed_names:
                return render(request, "errors/maintenance.html", status=503)

        response = self.get_response(request)
        return response