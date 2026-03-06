"""
Location model for Connector.

All geospatial data is stored as PostGIS Point fields.
Provides location obfuscation logic for private profiles (App Store compliance).
"""

import logging
import math
import random
import uuid

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger("apps")


class UserLocation(models.Model):
    """
    Stores a user's current geographic position as a PostGIS Point.

    Key behaviors:
      1. `point` stores the EXACT GPS coordinate (private, never exposed
         directly for individual/private profiles).
      2. `obfuscated_point` stores a randomly offset coordinate within
         LOCATION_OBFUSCATION_RADIUS_METERS of the real position. This is
         what gets served to the public map for private profiles.
      3. Public profiles (businesses/NGOs) have obfuscated_point == point
         (no offset needed; they render with pinpoint accuracy).
      4. PostGIS `ST_DWithin` is used for all radius queries — never raw
         float math.
    """

    class LocationSource(models.TextChoices):
        GPS = "gps", _("Device GPS")
        MANUAL = "manual", _("Manual Entry")
        NETWORK = "network", _("Network/WiFi")
        BACKGROUND = "background", _("Background Tracking")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="location",
    )

    # ── PostGIS Point Fields ──────────────────────────────────────────
    # SRID 4326 = WGS 84 (standard GPS coordinate system)
    point = gis_models.PointField(
        _("exact location"),
        srid=4326,
        geography=True,
        help_text=_("The user's real GPS position. NEVER exposed publicly for " "private/individual profiles."),
    )
    obfuscated_point = gis_models.PointField(
        _("obfuscated location"),
        srid=4326,
        geography=True,
        help_text=_(
            "Randomized offset position served on the public map for "
            "private profiles. Equals exact point for public entities."
        ),
    )

    # Metadata
    source = models.CharField(
        _("location source"),
        max_length=20,
        choices=LocationSource.choices,
        default=LocationSource.GPS,
    )
    accuracy_meters = models.FloatField(
        _("accuracy (meters)"),
        null=True,
        blank=True,
        help_text=_("GPS accuracy reported by the device."),
    )
    altitude = models.FloatField(
        _("altitude (meters)"),
        null=True,
        blank=True,
    )
    heading = models.FloatField(
        _("heading (degrees)"),
        null=True,
        blank=True,
    )
    speed = models.FloatField(
        _("speed (m/s)"),
        null=True,
        blank=True,
    )

    # Tracking state
    is_background_tracking = models.BooleanField(
        _("background tracking active"),
        default=False,
    )

    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("user location")
        verbose_name_plural = _("user locations")
        indexes = [
            gis_models.Index(fields=["updated_at"], name="idx_location_updated"),
        ]

    def __str__(self):
        return f"Location for {self.user.email}: " f"({self.point.y:.6f}, {self.point.x:.6f})"

    # ── Obfuscation Logic ────────────────────────────────────────────

    @staticmethod
    def generate_obfuscated_point(
        exact_point: Point,
        radius_meters: int = None,
    ) -> Point:
        """
        Generate a randomly offset Point within `radius_meters` of the
        exact GPS position.

        Uses proper spherical math:
          1. Generate a random bearing (0–360°).
          2. Generate a random distance (0 – radius_meters).
          3. Calculate the new lat/lon using the Haversine-derived
             destination formula.

        Args:
            exact_point: The real PostGIS Point (lon, lat).
            radius_meters: Maximum offset radius. Defaults to
                           settings.LOCATION_OBFUSCATION_RADIUS_METERS.

        Returns:
            A new PostGIS Point with SRID 4326.
        """
        if radius_meters is None:
            radius_meters = settings.LOCATION_OBFUSCATION_RADIUS_METERS

        # Earth's radius in meters
        earth_radius = 6_371_000.0

        lat = math.radians(exact_point.y)
        lon = math.radians(exact_point.x)

        # Random bearing in radians (0 – 2π)
        bearing = random.uniform(0, 2 * math.pi)

        # Random distance (use sqrt for uniform distribution within circle)
        distance = radius_meters * math.sqrt(random.random())

        # Angular distance
        angular_distance = distance / earth_radius

        # Destination latitude
        new_lat = math.asin(
            math.sin(lat) * math.cos(angular_distance) + math.cos(lat) * math.sin(angular_distance) * math.cos(bearing)
        )

        # Destination longitude
        new_lon = lon + math.atan2(
            math.sin(bearing) * math.sin(angular_distance) * math.cos(lat),
            math.cos(angular_distance) - math.sin(lat) * math.sin(new_lat),
        )

        new_lat_deg = math.degrees(new_lat)
        new_lon_deg = math.degrees(new_lon)

        return Point(new_lon_deg, new_lat_deg, srid=4326)

    def update_location(
        self,
        longitude: float,
        latitude: float,
        source: str = "gps",
        accuracy: float = None,
        altitude: float = None,
        heading: float = None,
        speed: float = None,
        is_background: bool = False,
    ) -> None:
        """
        Update the user's location with a new GPS coordinate.

        Automatically computes the obfuscated point based on the user's
        profile privacy setting:
          - Private profiles → random offset within obfuscation radius
          - Public profiles → obfuscated_point = exact point (no offset)
        """
        try:
            exact_point = Point(longitude, latitude, srid=4326)
            self.point = exact_point
            self.source = source
            self.accuracy_meters = accuracy
            self.altitude = altitude
            self.heading = heading
            self.speed = speed
            self.is_background_tracking = is_background

            # Determine if we need to obfuscate
            profile = self.user.profile
            if profile.should_obfuscate_location:
                self.obfuscated_point = self.generate_obfuscated_point(exact_point)
            else:
                # Public entity — show exact position
                self.obfuscated_point = exact_point

            self.save()

            # Update the user's online status
            profile.is_online = True
            profile.last_seen = timezone.now()
            profile.save(update_fields=["is_online", "last_seen"])

            logger.info(
                "Location updated for user %s (source=%s, obfuscated=%s)",
                self.user.email,
                source,
                profile.should_obfuscate_location,
            )

        except Exception:
            logger.exception("Failed to update location for user %s", self.user.email)
            raise


class LocationHistory(models.Model):
    """
    Append-only log of location updates for analytics and debugging.

    Important: This table stores ONLY obfuscated points for private
    profiles, ensuring that historical exact GPS data is never
    accumulated for individuals (privacy compliance).
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="location_history",
    )
    point = gis_models.PointField(
        _("recorded location"),
        srid=4326,
        geography=True,
        help_text=_(
            "For private profiles this is the OBFUSCATED point. " "For public entities this is the exact point."
        ),
    )
    source = models.CharField(
        max_length=20,
        choices=UserLocation.LocationSource.choices,
        default=UserLocation.LocationSource.GPS,
    )
    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _("location history")
        verbose_name_plural = _("location histories")
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(
                fields=["user", "recorded_at"],
                name="idx_lochistory_user_time",
            ),
        ]

    def __str__(self):
        return f"History for {self.user.email} at " f"{self.recorded_at.isoformat()}"
