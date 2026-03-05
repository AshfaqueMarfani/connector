"""
URL configuration for the locations app.
"""

from django.urls import path

from . import views

app_name = "locations"

urlpatterns = [
    path(
        "location/update/",
        views.LocationUpdateView.as_view(),
        name="location-update",
    ),
    path(
        "location/me/",
        views.LocationMeView.as_view(),
        name="location-me",
    ),
    path(
        "explore/nearby/",
        views.ExploreNearbyView.as_view(),
        name="explore-nearby",
    ),
]
