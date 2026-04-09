from django.urls import path
from .views import (
    clerk_list_view,
    clerk_add_view,
    clerk_edit_view,
    clerk_delete_view,
)

urlpatterns = [

path(
"admin-panel/clerks/",
clerk_list_view,
name="clerk_list"
),

path(
"admin-panel/clerks/add/",
clerk_add_view,
name="clerk_add"
),

path(
"admin-panel/clerks/<int:pk>/edit/",
clerk_edit_view,
name="clerk_edit"
),

path(
"admin-panel/clerks/<int:pk>/delete/",
clerk_delete_view,
name="clerk_delete"
),

]