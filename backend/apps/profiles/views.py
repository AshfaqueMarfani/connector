"""
Views for the profiles app.
"""

import logging

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import Profile
from .serializers import ProfilePublicSerializer, ProfileSerializer

logger = logging.getLogger("apps")


class ProfileMeView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/v1/profile/me/ — Retrieve own profile.
    PATCH /api/v1/profile/me/ — Update own profile (skills, interests, privacy toggle, etc.).
    """

    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            return self.request.user.profile
        except Profile.DoesNotExist:
            logger.error("Profile not found for user %s", self.request.user.email)
            raise

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)  # Always allow partial updates
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_update(serializer)
            logger.info("Profile updated for user %s", request.user.email)
            return Response(
                {
                    "success": True,
                    "message": "Profile updated successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception:
            logger.exception("Profile update failed for user %s", request.user.email)
            raise


class ProfileDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/profile/<uuid:pk>/

    Retrieve a public-facing profile by UUID.
    Excludes sensitive fields.
    """

    queryset = Profile.objects.select_related("user").filter(user__is_active=True)
    serializer_class = ProfilePublicSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"
