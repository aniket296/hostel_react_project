from django.urls import path
from .views import (
    student_dashboard,
    clerk_dashboard_view,
    admin_dashboard,
    locked_accounts_list_view,
    unlock_account_view,
    system_settings_view,
    admin_profile_view,
    admin_change_password_view,
    backup_list_view,
    backup_create_view,
    backup_download_view,
    backup_delete_view,
    backup_restore_view,
    admin_boys_hostel_dashboard,
    admin_girls_hostel_dashboard,
)

urlpatterns = [
    path("student/dashboard/", student_dashboard, name="student_dashboard"),
    path("clerk/dashboard/", clerk_dashboard_view, name="clerk_dashboard"),
    path("admin-panel/dashboard/", admin_dashboard, name="admin_dashboard"),

    path("admin-panel/locked-accounts/", locked_accounts_list_view, name="locked_accounts_list"),
    path("admin-panel/locked-accounts/<int:pk>/unlock/", unlock_account_view, name="unlock_account"),

    path("admin-panel/settings/", system_settings_view, name="system_settings"),

    path("admin-panel/profile/", admin_profile_view, name="admin_profile"),
    path("admin-panel/change-password/", admin_change_password_view, name="admin_change_password"),

    path("admin-panel/backups/", backup_list_view, name="backup_list"),
    path("admin-panel/backups/create/", backup_create_view, name="backup_create"),
    path("admin-panel/backups/<int:pk>/download/", backup_download_view, name="backup_download"),
    path("admin-panel/backups/<int:pk>/delete/", backup_delete_view, name="backup_delete"),
    path("admin-panel/backups/<int:pk>/restore/", backup_restore_view, name="backup_restore"),
    path("admin-panel/hostels/boys/", admin_boys_hostel_dashboard, name="admin_boys_hostel_dashboard"),
    path("admin-panel/hostels/girls/", admin_girls_hostel_dashboard, name="admin_girls_hostel_dashboard"),
]