"""
Views for the moderation app.
Handles blocking, unblocking, and reporting (App Store UGC compliance).
"""

import logging

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Block, Report
from .serializers import BlockCreateSerializer, BlockSerializer, ReportCreateSerializer, ReportSerializer

logger = logging.getLogger("apps")


class BlockCreateView(generics.CreateAPIView):
    """
    POST /api/v1/moderation/block/

    Block another user.
    Mandatory button on every profile (App Store UGC compliance).
    """

    serializer_class = BlockCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(blocker=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_create(serializer)
            logger.info(
                "User %s blocked user %s",
                request.user.email,
                serializer.validated_data["blocked"].email,
            )
            return Response(
                {
                    "success": True,
                    "message": "User blocked successfully.",
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception:
            logger.exception("Block creation failed for user %s", request.user.email)
            raise


class BlockListView(generics.ListAPIView):
    """
    GET /api/v1/moderation/blocks/

    List users blocked by the authenticated user.
    """

    serializer_class = BlockSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Block.objects.filter(blocker=self.request.user).select_related("blocked")


class UnblockView(APIView):
    """
    DELETE /api/v1/moderation/block/<uuid:blocked_id>/

    Remove a block on another user.
    """

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, blocked_id):
        try:
            block = Block.objects.get(
                blocker=request.user,
                blocked_id=blocked_id,
            )
            blocked_email = block.blocked.email
            block.delete()
            logger.info("User %s unblocked user %s", request.user.email, blocked_email)
            return Response(
                {
                    "success": True,
                    "message": "User unblocked successfully.",
                },
                status=status.HTTP_200_OK,
            )
        except Block.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "errors": {"detail": "Block not found."},
                },
                status=status.HTTP_404_NOT_FOUND,
            )


class ReportCreateView(generics.CreateAPIView):
    """
    POST /api/v1/moderation/report/

    Report a user or specific content.
    Mandatory button on every profile and chat message (App Store UGC compliance).
    """

    serializer_class = ReportCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_create(serializer)
            logger.info(
                "Report filed by %s against %s (category=%s)",
                request.user.email,
                serializer.validated_data["reported_user"].email,
                serializer.validated_data["category"],
            )
            return Response(
                {
                    "success": True,
                    "message": "Report submitted. Our moderation team will review it.",
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception:
            logger.exception("Report creation failed for user %s", request.user.email)
            raise


class ReportListView(generics.ListAPIView):
    """
    GET /api/v1/moderation/reports/

    List reports filed by the authenticated user.
    """

    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Report.objects.filter(reporter=self.request.user)
