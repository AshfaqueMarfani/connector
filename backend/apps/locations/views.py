"""
Views for the locations app.

Handles location updates (with obfuscation) and PostGIS-powered
radius explore queries using ST_DWithin.
"""

import logging

from django.contrib.auth import get_user_model
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.moderation.models import Block
from apps.profiles.serializers import ProfilePublicSerializer

from .models import LocationHistory, UserLocation
from .serializers import LocationUpdateSerializer, UserLocationOwnerSerializer, UserLocationSerializer

logger = logging.getLogger("apps")
User = get_user_model()


class LocationUpdateView(APIView):
    """
    POST /api/v1/location/update/

    Update the authenticated user's GPS position.

    Behavior:
      - Stores exact GPS coordinate in `point` (never publicly exposed
        for private profiles).
      - Computes and stores `obfuscated_point` based on profile privacy.
      - Logs to LocationHistory (using the obfuscated point for private users).
      - Returns the user's own location data (both exact and obfuscated).
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LocationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user = request.user

        try:
            # Get or create the UserLocation record
            location, created = UserLocation.objects.get_or_create(
                user=user,
                defaults={
                    "point": Point(data["longitude"], data["latitude"], srid=4326),
                    "obfuscated_point": Point(data["longitude"], data["latitude"], srid=4326),
                },
            )

            # Update with full obfuscation logic
            location.update_location(
                longitude=data["longitude"],
                latitude=data["latitude"],
                source=data.get("source", "gps"),
                accuracy=data.get("accuracy"),
                altitude=data.get("altitude"),
                heading=data.get("heading"),
                speed=data.get("speed"),
                is_background=data.get("is_background", False),
            )

            # Log to history (obfuscated point for private users)
            profile = user.profile
            history_point = location.obfuscated_point if profile.should_obfuscate_location else location.point
            LocationHistory.objects.create(
                user=user,
                point=history_point,
                source=data.get("source", "gps"),
            )

            owner_serializer = UserLocationOwnerSerializer(location)
            return Response(
                {
                    "success": True,
                    "message": "Location updated successfully.",
                    "data": owner_serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception:
            logger.exception("Location update failed for user %s", user.email)
            return Response(
                {
                    "success": False,
                    "errors": {"detail": "Failed to update location. Please try again."},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LocationMeView(generics.RetrieveAPIView):
    """
    GET /api/v1/location/me/

    Retrieve the authenticated user's own location
    (shows both exact and obfuscated coordinates).
    """

    serializer_class = UserLocationOwnerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            return self.request.user.location
        except UserLocation.DoesNotExist:
            return None

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response(
                {
                    "success": True,
                    "data": None,
                    "message": "No location data available. Update your location first.",
                },
                status=status.HTTP_200_OK,
            )
        serializer = self.get_serializer(instance)
        return Response(
            {"success": True, "data": serializer.data},
            status=status.HTTP_200_OK,
        )


class ExploreNearbyView(APIView):
    """
    GET /api/v1/explore/nearby/?radius=500&type=ngo,service

    PostGIS-powered radius query using ST_DWithin.

    Returns:
      - Public entities with exact GPS coordinates.
      - Private users with obfuscated GPS coordinates.
      - Excludes blocked users.
      - Results ordered by distance from the requesting user.

    Query parameters:
      - radius: Search radius in meters (100-5000, default 500)
      - type: Comma-separated account types to filter (individual, business, ngo)
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Validate that the requesting user has a location
        try:
            user_location = user.location
        except UserLocation.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "errors": {"detail": "You must update your location before exploring nearby users."},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse query parameters
        try:
            radius = int(request.query_params.get("radius", 500))
            radius = max(100, min(radius, 5000))  # Clamp between 100m and 5km
        except (ValueError, TypeError):
            radius = 500

        type_filter = request.query_params.get("type", "")
        account_types = [
            t.strip().lower() for t in type_filter.split(",") if t.strip().lower() in ("individual", "business", "ngo")
        ]

        try:
            # Get the user's location as the search center
            search_center = user_location.point

            # Get list of users blocked by or blocking the current user
            blocked_user_ids = set(Block.objects.filter(blocker=user).values_list("blocked_id", flat=True)) | set(
                Block.objects.filter(blocked=user).values_list("blocker_id", flat=True)
            )

            # PostGIS ST_DWithin query on the obfuscated_point field
            # This ensures we're searching against what the public map actually shows
            nearby_locations = (
                UserLocation.objects.filter(obfuscated_point__dwithin=(search_center, D(m=radius)))
                .exclude(user=user)
                .exclude(user_id__in=blocked_user_ids)
                .exclude(user__is_active=False)
                .exclude(user__is_suspended=True)
                .select_related("user", "user__profile")
            )

            # Filter by account type if specified
            if account_types:
                nearby_locations = nearby_locations.filter(user__account_type__in=account_types)

            # Annotate with distance from the search center and order by it
            nearby_locations = nearby_locations.annotate(distance=Distance("obfuscated_point", search_center)).order_by(
                "distance"
            )

            # Build response data
            results = []
            for loc in nearby_locations[:100]:  # Cap at 100 results
                profile = loc.user.profile
                location_serializer = UserLocationSerializer(loc)
                profile_serializer = ProfilePublicSerializer(profile)

                results.append(
                    {
                        "profile": profile_serializer.data,
                        "location": location_serializer.data,
                        "distance_meters": round(loc.distance.m, 1) if loc.distance else None,
                    }
                )

            return Response(
                {
                    "success": True,
                    "data": {
                        "radius_meters": radius,
                        "total_results": len(results),
                        "results": results,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception:
            logger.exception("Explore nearby failed for user %s", user.email)
            return Response(
                {
                    "success": False,
                    "errors": {"detail": "Failed to search nearby. Please try again."},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
