"""
Serializers for the locations app.

Handles location updates and ensures obfuscation compliance
for private profiles in all outbound data.
"""

from rest_framework import serializers

from django.contrib.gis.geos import Point

from .models import LocationHistory, UserLocation


class LocationUpdateSerializer(serializers.Serializer):
    """
    Accepts a location update from the client.
    Validates coordinates and optional metadata.
    """

    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    source = serializers.ChoiceField(
        choices=UserLocation.LocationSource.choices,
        default="gps",
    )
    accuracy = serializers.FloatField(required=False, allow_null=True, min_value=0)
    altitude = serializers.FloatField(required=False, allow_null=True)
    heading = serializers.FloatField(required=False, allow_null=True, min_value=0, max_value=360)
    speed = serializers.FloatField(required=False, allow_null=True, min_value=0)
    is_background = serializers.BooleanField(default=False)


class UserLocationSerializer(serializers.ModelSerializer):
    """
    Serializer for UserLocation.

    CRITICAL: For private profiles, this serializer ONLY exposes the
    obfuscated_point, NEVER the exact point. The `point` field is
    excluded from all public-facing serialization.
    """

    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    is_exact = serializers.SerializerMethodField()

    class Meta:
        model = UserLocation
        fields = [
            "latitude",
            "longitude",
            "is_exact",
            "source",
            "accuracy_meters",
            "updated_at",
        ]
        read_only_fields = fields

    def get_latitude(self, obj) -> float:
        """
        Return latitude from the appropriate point field.
        For private profiles → obfuscated_point.
        For public entities → exact point (which equals obfuscated_point).
        """
        point = self._get_safe_point(obj)
        return round(point.y, 6) if point else None

    def get_longitude(self, obj) -> float:
        """Return longitude from the appropriate point field."""
        point = self._get_safe_point(obj)
        return round(point.x, 6) if point else None

    def get_is_exact(self, obj) -> bool:
        """Whether the returned coordinates are exact (public entity) or obfuscated."""
        return not obj.user.profile.should_obfuscate_location

    def _get_safe_point(self, obj) -> Point:
        """
        Always return the obfuscated_point for serialization.
        Public entities have obfuscated_point == point, so this is safe
        for all account types.
        """
        return obj.obfuscated_point


class UserLocationOwnerSerializer(serializers.ModelSerializer):
    """
    Serializer for the location owner's own view.
    Shows BOTH exact and obfuscated coordinates so the user
    can see what others see vs. their real position.
    """

    exact_latitude = serializers.SerializerMethodField()
    exact_longitude = serializers.SerializerMethodField()
    obfuscated_latitude = serializers.SerializerMethodField()
    obfuscated_longitude = serializers.SerializerMethodField()

    class Meta:
        model = UserLocation
        fields = [
            "exact_latitude",
            "exact_longitude",
            "obfuscated_latitude",
            "obfuscated_longitude",
            "source",
            "accuracy_meters",
            "altitude",
            "heading",
            "speed",
            "is_background_tracking",
            "updated_at",
        ]
        read_only_fields = fields

    def get_exact_latitude(self, obj) -> float:
        return round(obj.point.y, 6) if obj.point else None

    def get_exact_longitude(self, obj) -> float:
        return round(obj.point.x, 6) if obj.point else None

    def get_obfuscated_latitude(self, obj) -> float:
        return round(obj.obfuscated_point.y, 6) if obj.obfuscated_point else None

    def get_obfuscated_longitude(self, obj) -> float:
        return round(obj.obfuscated_point.x, 6) if obj.obfuscated_point else None


class LocationHistorySerializer(serializers.ModelSerializer):
    """Serializer for location history entries."""

    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = LocationHistory
        fields = ["latitude", "longitude", "source", "recorded_at"]
        read_only_fields = fields

    def get_latitude(self, obj) -> float:
        return round(obj.point.y, 6) if obj.point else None

    def get_longitude(self, obj) -> float:
        return round(obj.point.x, 6) if obj.point else None
