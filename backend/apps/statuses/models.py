"""
Status model for Connector.

Users broadcast needs or offers (e.g., "Need emergency food assistance"
or "Offering free tutoring"). These statuses are parsed by the AI agent
for intelligent matching.
"""

import uuid

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils.translation import gettext_lazy as _


class Status(models.Model):
    """
    A user's broadcast — a short-lived need or offer visible to nearby users.

    The AI matching agent processes active statuses to find relevant
    connections and sends push notifications to both parties.
    """

    class StatusType(models.TextChoices):
        NEED = "need", _("Need / Request")
        OFFER = "offer", _("Offer / Service")

    class UrgencyLevel(models.TextChoices):
        LOW = "low", _("Low")
        MEDIUM = "medium", _("Medium")
        HIGH = "high", _("High")
        EMERGENCY = "emergency", _("Emergency")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="statuses",
    )

    # Content
    status_type = models.CharField(
        _("type"),
        max_length=10,
        choices=StatusType.choices,
        db_index=True,
    )
    text = models.TextField(
        _("status text"),
        max_length=500,
        help_text=_("Describe your need or offer. The AI agent will parse this."),
    )
    urgency = models.CharField(
        _("urgency level"),
        max_length=15,
        choices=UrgencyLevel.choices,
        default=UrgencyLevel.MEDIUM,
    )

    # AI-generated fields (populated asynchronously by Celery tasks)
    ai_parsed_intent = models.TextField(
        _("AI parsed intent"),
        blank=True,
        default="",
        help_text=_("AI agent's interpretation of the user's intent."),
    )
    ai_tags = models.JSONField(
        _("AI tags"),
        default=list,
        blank=True,
        help_text=_("Tags extracted by the AI agent (e.g., ['food', 'shelter'])."),
    )

    # Location snapshot (where the user was when posting)
    location_snapshot = gis_models.PointField(
        _("location at time of posting"),
        srid=4326,
        geography=True,
        null=True,
        blank=True,
        help_text=_(
            "Obfuscated point for private users; exact point for public entities."
        ),
    )

    # Lifecycle
    is_active = models.BooleanField(
        _("active"),
        default=True,
        db_index=True,
        help_text=_("Inactive statuses are no longer visible or matched."),
    )
    expires_at = models.DateTimeField(
        _("expires at"),
        null=True,
        blank=True,
        help_text=_("Auto-deactivate after this time."),
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("status")
        verbose_name_plural = _("statuses")
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["is_active", "status_type"],
                name="idx_status_active_type",
            ),
            models.Index(
                fields=["user", "is_active"],
                name="idx_status_user_active",
            ),
        ]

    def __str__(self):
        return f"[{self.get_status_type_display()}] {self.text[:60]}"

    def deactivate(self):
        """Mark this status as inactive."""
        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])
