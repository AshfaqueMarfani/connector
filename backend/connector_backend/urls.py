"""
Root URL configuration for connector_backend.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from connector_backend.health import HealthCheckView, ReadinessCheckView

urlpatterns = [
    # Health checks (unauthenticated – for load balancers & monitoring)
    path("api/v1/health/", HealthCheckView.as_view(), name="health-check"),
    path("api/v1/ready/", ReadinessCheckView.as_view(), name="readiness-check"),
    # Django Admin
    path("admin/", admin.site.urls),
    # API v1 – Auth
    path("api/v1/auth/", include("apps.accounts.urls", namespace="accounts")),
    # API v1 – Profiles
    path("api/v1/", include("apps.profiles.urls", namespace="profiles")),
    # API v1 – Location & Explore
    path("api/v1/", include("apps.locations.urls", namespace="locations")),
    # API v1 – Statuses
    path("api/v1/", include("apps.statuses.urls", namespace="statuses")),
    # API v1 – Moderation (Block/Report)
    path("api/v1/", include("apps.moderation.urls", namespace="moderation")),
    # API v1 – Chat, Connections & Notifications
    path("api/v1/", include("apps.chat.urls", namespace="chat")),
    # API v1 – AI Matching & Data Ingestion
    path("api/v1/", include("apps.matching.urls", namespace="matching")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
