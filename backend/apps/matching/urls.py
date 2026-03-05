"""
URL configuration for the matching app.
"""

from django.urls import path

from apps.matching import views

app_name = "matching"

urlpatterns = [
    # Match suggestions
    path(
        "matches/",
        views.MatchListView.as_view(),
        name="match-list",
    ),
    path(
        "matches/sent/",
        views.MatchSentListView.as_view(),
        name="match-sent-list",
    ),
    path(
        "matches/<uuid:pk>/dismiss/",
        views.MatchDismissView.as_view(),
        name="match-dismiss",
    ),
    # Profile tag generation
    path(
        "ai/generate-tags/",
        views.GenerateProfileTagsView.as_view(),
        name="generate-tags",
    ),
    # Data ingestion (admin only)
    path(
        "admin-api/ingest/",
        views.DataIngestionView.as_view(),
        name="data-ingest",
    ),
    path(
        "admin-api/ingest/jobs/",
        views.DataIngestionJobListView.as_view(),
        name="ingest-job-list",
    ),
    path(
        "admin-api/ingest/jobs/<uuid:pk>/",
        views.DataIngestionJobDetailView.as_view(),
        name="ingest-job-detail",
    ),
]
