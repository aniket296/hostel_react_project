from datetime import datetime
from .models import SystemSettings


def system_settings(request):
    settings_obj = SystemSettings.get_solo()
    return {
        "college_name": settings_obj.college_name,
        "system_title": settings_obj.system_title,
        "college_logo": settings_obj.college_logo,
        "header_photo": settings_obj.header_photo,
        "maintenance_mode": settings_obj.maintenance_mode,
    }


def current_year(request):
    return {
        "current_year": datetime.now().year
    }


def role_flags(request):
    user = request.user
    return {
        "is_student": user.is_authenticated and getattr(user, "role", None) == "student",
        "is_clerk": user.is_authenticated and getattr(user, "role", None) == "clerk",
        "is_admin": user.is_authenticated and getattr(user, "role", None) == "admin",
    }