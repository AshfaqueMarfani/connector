"""
URL configuration for the profiles app.
"""

from django.urls import path

from . import views

app_name = "profiles"

urlpatterns = [
    path(
        "profile/me/",
        views.ProfileMeView.as_view(),
        name="profile-me",
    ),
    path(
        "profile/<uuid:pk>/",
        views.ProfileDetailView.as_view(),
        name="profile-detail",
    ),
]
