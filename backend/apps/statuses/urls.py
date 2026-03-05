"""
URL configuration for the statuses app.
"""

from django.urls import path

from . import views

app_name = "statuses"

urlpatterns = [
    path(
        "status/",
        views.StatusCreateView.as_view(),
        name="status-create",
    ),
    path(
        "status/list/",
        views.StatusListView.as_view(),
        name="status-list",
    ),
    path(
        "status/<uuid:pk>/deactivate/",
        views.StatusDeactivateView.as_view(),
        name="status-deactivate",
    ),
]
