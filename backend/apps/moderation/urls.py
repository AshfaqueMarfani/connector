"""
URL configuration for the moderation app.
"""

from django.urls import path

from . import views

app_name = "moderation"

urlpatterns = [
    # Block / Unblock
    path(
        "moderation/block/",
        views.BlockCreateView.as_view(),
        name="block-create",
    ),
    path(
        "moderation/blocks/",
        views.BlockListView.as_view(),
        name="block-list",
    ),
    path(
        "moderation/block/<uuid:blocked_id>/",
        views.UnblockView.as_view(),
        name="unblock",
    ),
    # Report
    path(
        "moderation/report/",
        views.ReportCreateView.as_view(),
        name="report-create",
    ),
    path(
        "moderation/reports/",
        views.ReportListView.as_view(),
        name="report-list",
    ),
]
