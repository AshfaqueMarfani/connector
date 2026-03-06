"""
API views for AI matching and data ingestion.
"""

import logging

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.matching.models import AIMatchResult, DataIngestionJob
from apps.matching.serializers import (
    AIMatchResultSerializer,
    DataIngestionJobSerializer,
    DataIngestionRequestSerializer,
)
from apps.matching.tasks import generate_profile_tags, process_ingestion_job

logger = logging.getLogger("apps")


# ------------------------------------------------------------------
# Match Suggestions
# ------------------------------------------------------------------
class MatchListView(generics.ListAPIView):
    """
    GET /api/v1/matches/

    List AI-generated match suggestions for the authenticated user.
    Viewing automatically marks pending matches as "viewed".
    """

    serializer_class = AIMatchResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = AIMatchResult.objects.filter(
            matched_user=user,
            match_status__in=[
                AIMatchResult.MatchStatus.PENDING,
                AIMatchResult.MatchStatus.NOTIFIED,
                AIMatchResult.MatchStatus.VIEWED,
            ],
        ).select_related(
            "status",
            "status_owner",
            "status_owner__profile",
            "matched_user",
        )

        # Mark pending as viewed
        AIMatchResult.objects.filter(
            matched_user=user,
            match_status=AIMatchResult.MatchStatus.PENDING,
        ).update(match_status=AIMatchResult.MatchStatus.VIEWED)

        return qs


class MatchSentListView(generics.ListAPIView):
    """
    GET /api/v1/matches/sent/

    List matches originating from the current user's statuses.
    """

    serializer_class = AIMatchResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            AIMatchResult.objects.filter(status_owner=self.request.user)
            .exclude(match_status=AIMatchResult.MatchStatus.EXPIRED)
            .select_related(
                "matched_user",
                "matched_user__profile",
                "status",
                "status_owner",
            )
        )


class MatchDismissView(APIView):
    """
    POST /api/v1/matches/<uuid:pk>/dismiss/

    Dismiss an AI match suggestion.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            match = AIMatchResult.objects.get(
                id=pk,
                matched_user=request.user,
            )
        except AIMatchResult.DoesNotExist:
            return Response(
                {"success": False, "error": "Match not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        match.match_status = AIMatchResult.MatchStatus.DISMISSED
        match.save(update_fields=["match_status", "updated_at"])

        return Response({"success": True, "message": "Match dismissed."})


# ------------------------------------------------------------------
# Profile Tag Generation
# ------------------------------------------------------------------
class GenerateProfileTagsView(APIView):
    """
    POST /api/v1/ai/generate-tags/

    Queue AI tag generation for the authenticated user's profile.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = request.user.profile
        generate_profile_tags.delay(str(profile.id))
        return Response(
            {
                "success": True,
                "message": "Tag generation queued. Tags will update shortly.",
            }
        )


# ------------------------------------------------------------------
# Data Ingestion (Admin Only)
# ------------------------------------------------------------------
class DataIngestionView(APIView):
    """
    POST /api/v1/admin/ingest/

    Bulk-import entities (businesses, NGOs) from a JSON payload.
    Admin-only. Processing runs asynchronously via Celery.
    """

    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = DataIngestionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        entities = serializer.validated_data["entities"]
        source_name = serializer.validated_data.get("source_name", "API Upload")

        job = DataIngestionJob.objects.create(
            initiated_by=request.user,
            source_name=source_name,
            total_records=len(entities),
        )

        # Queue async processing
        process_ingestion_job.delay(str(job.id), entities)

        return Response(
            {
                "success": True,
                "data": DataIngestionJobSerializer(job).data,
                "message": f"Ingestion job created. {len(entities)} records queued.",
            },
            status=status.HTTP_202_ACCEPTED,
        )


class DataIngestionJobListView(generics.ListAPIView):
    """
    GET /api/v1/admin/ingest/jobs/

    List all data ingestion jobs (admin only).
    """

    serializer_class = DataIngestionJobSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return DataIngestionJob.objects.all()


class DataIngestionJobDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/admin/ingest/jobs/<uuid:pk>/

    Get details + status of a specific ingestion job (admin only).
    """

    serializer_class = DataIngestionJobSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = DataIngestionJob.objects.all()
