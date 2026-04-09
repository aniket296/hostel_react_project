from django.urls import path
from .views import (
    student_academics_home_view,
    student_academics_list_view,
    student_academic_upload_view,
    academic_download_view,
    staff_academics_list_view,
    academic_edit_view,
    academic_delete_view,
)

urlpatterns = [
    path("student/academics/home/", student_academics_home_view, name="student_academics_home"),
    path("student/academics/", student_academics_list_view, name="student_academics_list"),
    path("student/academics/upload/", student_academic_upload_view, name="student_academic_upload"),

    path("clerk/academics/", staff_academics_list_view, name="clerk_academics_list"),
    path("admin-panel/academics/", staff_academics_list_view, name="admin_academics_list"),

    path("clerk/academics/<int:pk>/edit/", academic_edit_view, name="clerk_academic_edit"),
    path("admin-panel/academics/<int:pk>/edit/", academic_edit_view, name="admin_academic_edit"),

    path("clerk/academics/<int:pk>/delete/", academic_delete_view, name="clerk_academic_delete"),
    path("admin-panel/academics/<int:pk>/delete/", academic_delete_view, name="admin_academic_delete"),

    path("student/academics/<int:pk>/download/", academic_download_view, name="academic_download"),
    path("clerk/academics/<int:pk>/download/", academic_download_view, name="clerk_academic_download"),
    path("admin-panel/academics/<int:pk>/download/", academic_download_view, name="admin_academic_download"),
]