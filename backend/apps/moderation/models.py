"""
Moderation models for Connector.

Implements mandatory App Store UGC compliance:
  - Block: User A blocks User B → B can no longer contact A or appear
    in A's explore results.
  - Report: User A reports User B or specific content → Creates a review
    ticket for the moderation dashboard.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Block(models.Model):
    """
    User blocking relationship.

    When User A blocks User B:
      - B is hidden from A's explore/nearby results.
      - B cannot send chat messages to A.
      - B cannot view A's profile.

    This is a mandatory UGC feature for App Store approval.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocks_given",
        help_text=_("The user who initiated the block."),
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocks_received",
        help_text=_("The user who has been blocked."),
    )
    reason = models.TextField(
        _("reason"),
        max_length=500,
        blank=True,
        default="",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("block")
        verbose_name_plural = _("blocks")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["blocker", "blocked"],
                name="unique_block_pair",
            ),
            models.CheckConstraint(
                check=~models.Q(blocker=models.F("blocked")),
                name="no_self_block",
            ),
        ]
        indexes = [
            models.Index(fields=["blocker"], name="idx_block_blocker"),
            models.Index(fields=["blocked"], name="idx_block_blocked"),
        ]

    def __str__(self):
        return f"{self.blocker.email} blocked {self.blocked.email}"


class Report(models.Model):
    """
    Content/user report for moderation review.

    Mandatory for App Store UGC compliance. Every profile and every
    chat message must have a visible "Report" button.
    """

    class ReportCategory(models.TextChoices):
        SPAM = "spam", _("Spam")
        HARASSMENT = "harassment", _("Harassment / Bullying")
        HATE_SPEECH = "hate_speech", _("Hate Speech")
        INAPPROPRIATE = "inappropriate", _("Inappropriate Content")
        IMPERSONATION = "impersonation", _("Impersonation")
        SCAM = "scam", _("Scam / Fraud")
        VIOLENCE = "violence", _("Violence / Threats")
        OTHER = "other", _("Other")

    class ReportStatus(models.TextChoices):
        PENDING = "pending", _("Pending Review")
        REVIEWING = "reviewing", _("Under Review")
        RESOLVED = "resolved", _("Resolved")
        DISMISSED = "dismissed", _("Dismissed")

    class ContentType(models.TextChoices):
        PROFILE = "profile", _("User Profile")
        STATUS = "status", _("Status / Broadcast")
        CHAT_MESSAGE = "chat_message", _("Chat Message")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_filed",
        help_text=_("The user filing the report."),
    )
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_received",
        help_text=_("The user being reported."),
    )

    # What is being reported
    content_type = models.CharField(
        _("content type"),
        max_length=20,
        choices=ContentType.choices,
    )
    content_id = models.UUIDField(
        _("content ID"),
        null=True,
        blank=True,
        help_text=_(
            "UUID of the reported content (status ID, message ID, etc.). "
            "Null if the report is against the user's profile in general."
        ),
    )

    # Report details
    category = models.CharField(
        _("category"),
        max_length=20,
        choices=ReportCategory.choices,
    )
    description = models.TextField(
        _("description"),
        max_length=1000,
        blank=True,
        default="",
        help_text=_("Optional additional details from the reporter."),
    )

    # Moderation workflow
    status = models.CharField(
        _("review status"),
        max_length=20,
        choices=ReportStatus.choices,
        default=ReportStatus.PENDING,
        db_index=True,
    )
    moderator_notes = models.TextField(
        _("moderator notes"),
        blank=True,
        default="",
    )
    resolved_at = models.DateTimeField(
        _("resolved at"),
        null=True,
        blank=True,
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports_resolved",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("report")
        verbose_name_plural = _("reports")
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["status", "created_at"],
                name="idx_report_status_created",
            ),
            models.Index(
                fields=["reported_user"],
                name="idx_report_reported_user",
            ),
        ]

    def __str__(self):
        return f"Report #{str(self.id)[:8]} — " f"{self.get_category_display()} against {self.reported_user.email}"
