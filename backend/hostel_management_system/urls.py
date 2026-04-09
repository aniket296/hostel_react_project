from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("core.urls")),
    path("", include("students.urls")),
    path("", include("clerks.urls")),
    path("", include("complaints.urls")),
    path("", include("academics.urls")),
    path("", include("feedbacks.urls")),
    path("api/", include("api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
handler403 = "core.error_views.custom_403_view"
handler404 = "core.error_views.custom_404_view"
handler500 = "core.error_views.custom_500_view"