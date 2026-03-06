"""
Views for the statuses app.
"""

import logging

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import Status
from .serializers import StatusCreateSerializer, StatusSerializer

logger = logging.getLogger("apps")


class StatusCreateView(generics.CreateAPIView):
    """
    POST /api/v1/status/

    Broadcast a new need or offer.
    Captures the user's current obfuscated location snapshot.
    """

    serializer_class = StatusCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        # Capture location snapshot if available
        location_snapshot = None
        try:
            user_location = user.location
            profile = user.profile
            if profile.should_obfuscate_location:
                location_snapshot = user_location.obfuscated_point
            else:
                location_snapshot = user_location.point
        except Exception:
            logger.warning(
                "No location available for status snapshot (user=%s)",
                user.email,
            )

        serializer.save(user=user, location_snapshot=location_snapshot)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_create(serializer)
            logger.info(
                "Status created by user %s (type=%s)",
                request.user.email,
                serializer.validated_data.get("status_type"),
            )

            # Trigger Celery task for AI parsing & matching
            from apps.matching.tasks import parse_status_intent

            parse_status_intent.delay(str(serializer.instance.id))

            return Response(
                {
                    "success": True,
                    "message": "Status broadcast created.",
                    "data": StatusSerializer(serializer.instance).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception:
            logger.exception("Status creation failed for user %s", request.user.email)
            raise


class StatusListView(generics.ListAPIView):
    """
    GET /api/v1/status/

    List the authenticated user's statuses.
    """

    serializer_class = StatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Status.objects.filter(user=self.request.user).order_by("-created_at")


class StatusDeactivateView(generics.UpdateAPIView):
    """
    PATCH /api/v1/status/<uuid:pk>/deactivate/

    Deactivate an active status (mark as inactive).
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StatusSerializer

    def get_queryset(self):
        return Status.objects.filter(user=self.request.user, is_active=True)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            instance.deactivate()
            return Response(
                {
                    "success": True,
                    "message": "Status deactivated.",
                    "data": StatusSerializer(instance).data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception:
            logger.exception("Status deactivation failed for %s", instance.id)
            raise
