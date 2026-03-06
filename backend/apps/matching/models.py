"""
AI Matching models for Connector.

Tracks AI-generated match results between user statuses and nearby
profiles, plus data ingestion job records for bulk entity import.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AIMatchResult(models.Model):
    """
    Records an AI-generated match between a Status and a potentially
    relevant nearby user/entity.

    Created asynchronously by the ``find_matches_for_status`` Celery task
    after the AI agent parses a new status broadcast.
    """

    class MatchStatus(models.TextChoices):
        PENDING = "pending", _("Pending")
        NOTIFIED = "notified", _("Notified")
        VIEWED = "viewed", _("Viewed")
        CONNECTED = "connected", _("Connected")
        DISMISSED = "dismissed", _("Dismissed")
        EXPIRED = "expired", _("Expired")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # The status that triggered this match
    status = models.ForeignKey(
        "statuses.Status",
        on_delete=models.CASCADE,
        related_name="matches",
    )

    # The user who posted the status
    status_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="status_matches_initiated",
    )

    # The matched user/entity
    matched_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="status_matches_received",
    )

    # Match metadata
    score = models.FloatField(
        _("match score"),
        default=0.0,
        help_text=_("AI confidence score (0.0 to 1.0)."),
    )
    reason = models.TextField(
        _("match reason"),
        blank=True,
        default="",
        help_text=_("AI-generated explanation for this match."),
    )
    matched_tags = models.JSONField(
        _("matched tags"),
        default=list,
        blank=True,
        help_text=_("Tags that overlapped between the status and matched profile."),
    )
    distance_meters = models.FloatField(
        _("distance in meters"),
        null=True,
        blank=True,
        help_text=_("Distance between the status location and matched user."),
    )

    # Lifecycle
    match_status = models.CharField(
        _("match status"),
        max_length=15,
        choices=MatchStatus.choices,
        default=MatchStatus.PENDING,
    )
    notified_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("AI match result")
        verbose_name_plural = _("AI match results")
        ordering = ["-score", "-created_at"]
        unique_together = [["status", "matched_user"]]
        indexes = [
            models.Index(
                fields=["status_owner", "match_status"],
                name="idx_match_owner_status",
            ),
            models.Index(
                fields=["matched_user", "match_status"],
                name="idx_match_user_status",
            ),
            models.Index(fields=["score"], name="idx_match_score"),
        ]

    def __str__(self):
        return f"Match: {self.status} → {self.matched_user} " f"(score={self.score:.2f})"


class DataIngestionJob(models.Model):
    """
    Tracks bulk data ingestion operations (e.g., importing external NGO
    directories or business registries into the platform).
    """

    class JobStatus(models.TextChoices):
        PENDING = "pending", _("Pending")
        PROCESSING = "processing", _("Processing")
        COMPLETED = "completed", _("Completed")
        FAILED = "failed", _("Failed")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ingestion_jobs",
    )

    source_name = models.CharField(
        _("data source"),
        max_length=255,
        help_text=_("Name or identifier of the data source."),
    )
    job_status = models.CharField(
        _("status"),
        max_length=15,
        choices=JobStatus.choices,
        default=JobStatus.PENDING,
    )

    total_records = models.PositiveIntegerField(default=0)
    processed_records = models.PositiveIntegerField(default=0)
    failed_records = models.PositiveIntegerField(default=0)
    error_log = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("data ingestion job")
        verbose_name_plural = _("data ingestion jobs")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Ingestion: {self.source_name} ({self.get_job_status_display()})"
