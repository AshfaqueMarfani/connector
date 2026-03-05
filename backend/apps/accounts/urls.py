"""
URL configuration for the accounts app.
"""

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path(
        "register/",
        views.UserRegistrationView.as_view(),
        name="register",
    ),
    path(
        "login/",
        views.CustomTokenObtainPairView.as_view(),
        name="login",
    ),
    path(
        "token/refresh/",
        views.CustomTokenRefreshView.as_view(),
        name="token-refresh",
    ),
    path(
        "me/",
        views.UserMeView.as_view(),
        name="me",
    ),
]
