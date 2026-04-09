from django.urls import path

from .views import (
    admin_feedback_create_view,
    admin_feedback_form_list_view,
    admin_feedback_form_view,
    admin_feedback_form_stop_view,
    admin_feedback_form_delete_view,  
    admin_feedback_analysis_list_view,
    admin_feedback_analysis_view,
    admin_feedback_analysis_export_view,
    student_feedback_page_view,
)

urlpatterns = [
    path("admin-panel/feedback/create/", admin_feedback_create_view, name="admin_feedback_create"),

    path("admin-panel/feedback/forms/", admin_feedback_form_list_view, name="admin_feedback_form_list"),
    path("admin-panel/feedback/forms/<int:pk>/view/", admin_feedback_form_view, name="admin_feedback_form_view"),
    path("admin-panel/feedback/forms/<int:pk>/stop/", admin_feedback_form_stop_view, name="admin_feedback_form_stop"),
    
    
    path("admin-panel/feedback/forms/<int:pk>/delete/", admin_feedback_form_delete_view, name="admin_feedback_form_delete"),

    path("admin-panel/feedback/analysis/", admin_feedback_analysis_list_view, name="admin_feedback_analysis_list"),
    path("admin-panel/feedback/analysis/<int:pk>/", admin_feedback_analysis_view, name="admin_feedback_analysis_view"),
    path("admin-panel/feedback/analysis/<int:pk>/export/", admin_feedback_analysis_export_view, name="admin_feedback_analysis_export"),

    path("student/feedback/", student_feedback_page_view, name="student_feedback_page"),
]