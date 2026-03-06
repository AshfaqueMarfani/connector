"""
Profile model for Connector.

Stores user display info, skills, interests, and the critical
privacy toggle that controls location exposure on the public map.
"""

import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _


class Profile(models.Model):
    """
    User profile — linked 1:1 to the custom User model.

    Privacy rules (App Store compliance):
      - is_public=False (Individuals): Map shows obfuscated location only.
      - is_public=True (Businesses/NGOs): Map shows exact GPS pin.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    # Display fields
    display_name = models.CharField(
        _("display name"),
        max_length=150,
        help_text=_("Name shown on the map and in search results."),
    )
    bio = models.TextField(
        _("bio"),
        max_length=500,
        blank=True,
        default="",
        help_text=_("Short description visible to nearby users."),
    )
    avatar = models.ImageField(
        _("avatar"),
        upload_to="avatars/%Y/%m/",
        blank=True,
        null=True,
    )

    # Categorization
    skills = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        default=list,
        help_text=_("List of skills this user offers (e.g., 'plumbing', 'tutoring')."),
    )
    interests = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        default=list,
        help_text=_("List of interests or needs (e.g., 'food assistance', 'legal aid')."),
    )
    tags = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list,
        help_text=_("AI-generated or user-set tags for matching " "(e.g., 'Food', 'Shelter', 'Electrician')."),
    )

    # Privacy toggle — critical for App Store compliance
    is_public = models.BooleanField(
        _("public profile"),
        default=False,
        db_index=True,
        help_text=_(
            "Public profiles (businesses/NGOs) show exact GPS on the map. "
            "Private profiles (individuals) show an obfuscated location only."
        ),
    )

    # Live tracking opt-in (background location)
    live_tracking_enabled = models.BooleanField(
        _("live tracking enabled"),
        default=False,
        help_text=_(
            "When enabled, the app may update location in the background. "
            "A persistent OS notification is required when active."
        ),
    )

    # Online / availability status
    is_online = models.BooleanField(
        _("currently online"),
        default=False,
    )
    last_seen = models.DateTimeField(
        _("last seen"),
        null=True,
        blank=True,
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("profile")
        verbose_name_plural = _("profiles")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_public"], name="idx_profile_is_public"),
            models.Index(fields=["is_online"], name="idx_profile_is_online"),
        ]

    def __str__(self):
        visibility = "Public" if self.is_public else "Private"
        return f"{self.display_name} ({visibility})"

    @property
    def should_obfuscate_location(self) -> bool:
        """
        Returns True if this profile's GPS must be obfuscated on the map.
        Only private (individual) profiles require obfuscation.
        """
        return not self.is_public
