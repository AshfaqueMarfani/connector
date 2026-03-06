"""
Views for the accounts app.
Handles user registration and JWT token retrieval.
"""

import logging

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import UserRegistrationSerializer, UserSerializer

logger = logging.getLogger("apps")
User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/

    Register a new user account.
    - Requires EULA acceptance (App Store compliance).
    - Automatically creates a linked Profile (via signal).
    - Returns the created user data.
    """

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = serializer.save()
            logger.info("New user registered: %s (type=%s)", user.email, user.account_type)

            return Response(
                {
                    "success": True,
                    "message": "Account created successfully.",
                    "data": UserSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception:
            logger.exception("Registration failed for email: %s", request.data.get("email"))
            raise


class UserMeView(generics.RetrieveAPIView):
    """
    GET /api/v1/auth/me/

    Retrieve the authenticated user's own data.
    """

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/

    Returns JWT access + refresh tokens.
    Checks that the user has accepted the EULA and is not suspended.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            # Verify EULA and suspension status
            email = request.data.get("email", "")
            try:
                user = User.objects.get(email=email)

                if user.is_suspended:
                    return Response(
                        {
                            "success": False,
                            "errors": {
                                "detail": "Your account has been suspended. " "Contact support for more information."
                            },
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

                if not user.eula_accepted:
                    return Response(
                        {
                            "success": False,
                            "errors": {"detail": "You must accept the EULA before logging in."},
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

                response.data = {
                    "success": True,
                    "data": {
                        "access": response.data["access"],
                        "refresh": response.data["refresh"],
                        "user": UserSerializer(user).data,
                    },
                }
            except User.DoesNotExist:
                pass  # Let DRF's default handling take over

        return response


class CustomTokenRefreshView(TokenRefreshView):
    """
    POST /api/v1/auth/token/refresh/

    Refresh an expired access token using a valid refresh token.
    """

    permission_classes = [permissions.AllowAny]
