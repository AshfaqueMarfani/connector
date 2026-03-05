"""
Tests for core models — User, Profile, Location (Phase 1 validation).
"""

import math

from django.contrib.gis.geos import Point
from django.test import TestCase, override_settings

from apps.accounts.models import User
from apps.locations.models import UserLocation
from apps.profiles.models import Profile


class UserModelTests(TestCase):
    """Tests for the custom User model."""

    def test_create_individual_user(self):
        """Creating an individual user should work with email auth."""
        user = User.objects.create_user(
            email="test@example.com",
            full_name="Test User",
            password="TestPassword123!",
            account_type="individual",
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.account_type, "individual")
        self.assertFalse(user.is_public_entity)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_suspended)

    def test_create_business_user(self):
        """Business accounts should be flagged as public entities."""
        user = User.objects.create_user(
            email="biz@example.com",
            full_name="Test Business",
            password="TestPassword123!",
            account_type="business",
        )
        self.assertTrue(user.is_public_entity)

    def test_create_ngo_user(self):
        """NGO accounts should be flagged as public entities."""
        user = User.objects.create_user(
            email="ngo@example.com",
            full_name="Test NGO",
            password="TestPassword123!",
            account_type="ngo",
        )
        self.assertTrue(user.is_public_entity)

    def test_create_superuser(self):
        """Superuser creation should set all expected flags."""
        admin = User.objects.create_superuser(
            email="admin@example.com",
            full_name="Admin",
            password="AdminPassword123!",
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.eula_accepted)

    def test_eula_acceptance(self):
        """EULA acceptance should set timestamp."""
        user = User.objects.create_user(
            email="eula@example.com",
            password="TestPassword123!",
        )
        self.assertFalse(user.eula_accepted)
        user.accept_eula()
        user.refresh_from_db()
        self.assertTrue(user.eula_accepted)
        self.assertIsNotNone(user.eula_accepted_at)

    def test_suspend_user(self):
        """Suspending a user should deactivate their account."""
        user = User.objects.create_user(
            email="suspend@example.com",
            password="TestPassword123!",
        )
        user.suspend()
        user.refresh_from_db()
        self.assertTrue(user.is_suspended)
        self.assertFalse(user.is_active)

    def test_email_required(self):
        """User creation without email should raise ValueError."""
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="test123!")

    def test_duplicate_email(self):
        """Duplicate emails should raise an integrity error."""
        User.objects.create_user(email="dup@example.com", password="test123!")
        with self.assertRaises(Exception):
            User.objects.create_user(email="dup@example.com", password="test456!")


class ProfileModelTests(TestCase):
    """Tests for the Profile model and auto-creation via signal."""

    def test_profile_auto_created_on_user_creation(self):
        """A Profile should be automatically created when a User is created."""
        user = User.objects.create_user(
            email="profile@example.com",
            full_name="Profile Test",
            password="TestPassword123!",
        )
        self.assertTrue(hasattr(user, "profile"))
        self.assertIsInstance(user.profile, Profile)

    def test_individual_profile_is_private_by_default(self):
        """Individual profiles should be private (obfuscated location)."""
        user = User.objects.create_user(
            email="private@example.com",
            full_name="Private User",
            password="TestPassword123!",
            account_type="individual",
        )
        self.assertFalse(user.profile.is_public)
        self.assertTrue(user.profile.should_obfuscate_location)

    def test_business_profile_is_public_by_default(self):
        """Business profiles should be public (exact location)."""
        user = User.objects.create_user(
            email="public@example.com",
            full_name="Public Business",
            password="TestPassword123!",
            account_type="business",
        )
        self.assertTrue(user.profile.is_public)
        self.assertFalse(user.profile.should_obfuscate_location)

    def test_ngo_profile_is_public_by_default(self):
        """NGO profiles should be public (exact location)."""
        user = User.objects.create_user(
            email="ngo@example.com",
            full_name="Test NGO",
            password="TestPassword123!",
            account_type="ngo",
        )
        self.assertTrue(user.profile.is_public)


class LocationModelTests(TestCase):
    """Tests for the UserLocation model and obfuscation logic."""

    def setUp(self):
        self.individual = User.objects.create_user(
            email="individual@example.com",
            full_name="Individual",
            password="TestPassword123!",
            account_type="individual",
        )
        self.business = User.objects.create_user(
            email="business@example.com",
            full_name="Business",
            password="TestPassword123!",
            account_type="business",
        )
        # Karachi coordinates
        self.test_lat = 24.8607
        self.test_lon = 67.0011

    @override_settings(LOCATION_OBFUSCATION_RADIUS_METERS=200)
    def test_obfuscation_generates_different_point(self):
        """Obfuscated point should differ from the exact point."""
        exact = Point(self.test_lon, self.test_lat, srid=4326)
        obfuscated = UserLocation.generate_obfuscated_point(exact, radius_meters=200)

        # Points should NOT be identical
        self.assertNotEqual(exact.x, obfuscated.x)
        self.assertNotEqual(exact.y, obfuscated.y)

    @override_settings(LOCATION_OBFUSCATION_RADIUS_METERS=200)
    def test_obfuscation_within_radius(self):
        """Obfuscated point should be within the specified radius."""
        exact = Point(self.test_lon, self.test_lat, srid=4326)
        radius = 200

        # Run multiple times to account for randomness
        for _ in range(50):
            obfuscated = UserLocation.generate_obfuscated_point(
                exact, radius_meters=radius
            )
            # Calculate distance using Haversine
            distance = self._haversine_distance(
                exact.y, exact.x, obfuscated.y, obfuscated.x
            )
            self.assertLessEqual(
                distance,
                radius + 1,  # 1m tolerance for floating point
                f"Obfuscated point {distance:.1f}m away, exceeds {radius}m radius",
            )

    def test_location_update_private_user(self):
        """Private user location update should produce an obfuscated point."""
        location = UserLocation.objects.create(
            user=self.individual,
            point=Point(self.test_lon, self.test_lat, srid=4326),
            obfuscated_point=Point(self.test_lon, self.test_lat, srid=4326),
        )
        location.update_location(
            longitude=self.test_lon,
            latitude=self.test_lat,
        )
        location.refresh_from_db()

        # Obfuscated point should differ from exact point
        self.assertNotAlmostEqual(
            location.point.x, location.obfuscated_point.x, places=6
        )

    def test_location_update_public_entity(self):
        """Public entity location update should NOT obfuscate."""
        location = UserLocation.objects.create(
            user=self.business,
            point=Point(self.test_lon, self.test_lat, srid=4326),
            obfuscated_point=Point(self.test_lon, self.test_lat, srid=4326),
        )
        location.update_location(
            longitude=self.test_lon,
            latitude=self.test_lat,
        )
        location.refresh_from_db()

        # Both points should be identical for public entities
        self.assertAlmostEqual(
            location.point.x, location.obfuscated_point.x, places=6
        )
        self.assertAlmostEqual(
            location.point.y, location.obfuscated_point.y, places=6
        )

    @staticmethod
    def _haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate distance in meters between two GPS coordinates."""
        R = 6_371_000  # Earth's radius in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
