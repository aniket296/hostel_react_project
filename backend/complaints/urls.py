from django.urls import path
from .views import (
    admin_complaint_history_view,
    clerk_complaint_history_view,
    student_complaint_home_view,
    student_complaint_list_view,
    student_complaint_create_view,
    student_complaint_detail_view,
    student_mark_solved_view,
    student_mark_unsolved_view,
    complaint_list_by_status_view,
    complaint_detail_view,
    assign_worker_view,
    mark_completed_view,
    complaint_export_view,
    clerk_actions_complaint_list_view,
    clerk_actions_complaint_export_view,
    clerk_actions_bulk_mark_completed_view,
    clerk_actions_report_view,
    clerk_actions_report_export_view,
)

urlpatterns = [

    path("clerk/actions/complaints/", clerk_actions_complaint_list_view, name="clerk_actions_complaints"),
    path("clerk/actions/complaints/export/", clerk_actions_complaint_export_view, name="clerk_actions_complaints_export"),
    path("clerk/actions/complaints/bulk-mark-completed/", clerk_actions_bulk_mark_completed_view, name="clerk_actions_bulk_mark_completed"),
    path("clerk/actions/report/", clerk_actions_report_view, name="clerk_actions_report"),
    path("clerk/actions/report/export/", clerk_actions_report_export_view, name="clerk_actions_report_export"),

    # Student
    path("student/complaints/", student_complaint_home_view, name="student_complaint_home"),
    path("student/complaints/list", student_complaint_list_view, name="student_complaint_list"),
    path("student/complaints/new/", student_complaint_create_view, name="student_complaint_create"),
    path("student/complaints/<int:pk>/", student_complaint_detail_view, name="student_complaint_detail"),
    path("student/complaints/<int:pk>/mark-solved/", student_mark_solved_view, name="student_mark_solved"),
    path("student/complaints/<int:pk>/mark-unsolved/", student_mark_unsolved_view, name="student_mark_unsolved"),

    # Export
    path("clerk/complaints/export/", complaint_export_view, name="clerk_complaint_export"),
    path("admin-panel/complaints/export/", complaint_export_view, name="admin_complaint_export"),

    # History (must come before <str:status>)
    path("clerk/complaints/history/", clerk_complaint_history_view, name="clerk_complaint_history"),
    path("admin-panel/complaints/history/", admin_complaint_history_view, name="admin_complaint_history"),

    # Clerk
    path("clerk/complaints/detail/<int:pk>/", complaint_detail_view, name="clerk_complaint_detail"),
    path("clerk/complaints/<int:pk>/assign-worker/", assign_worker_view, name="clerk_assign_worker"),
    path("clerk/complaints/<int:pk>/mark-completed/", mark_completed_view, name="clerk_mark_completed"),
    path("clerk/complaints/<str:status>/", complaint_list_by_status_view, name="clerk_complaint_status_list"),
    

    # Admin
    path("admin-panel/complaints/detail/<int:pk>/", complaint_detail_view, name="admin_complaint_detail"),
    path("admin-panel/complaints/<int:pk>/assign-worker/", assign_worker_view, name="admin_assign_worker"),
    path("admin-panel/complaints/<int:pk>/mark-completed/", mark_completed_view, name="admin_mark_completed"),
    path("admin-panel/complaints/<str:status>/", complaint_list_by_status_view, name="admin_complaint_status_list"),
]