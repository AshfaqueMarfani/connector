"""
Tests for API endpoints — Registration, Login, Profile, Location (Phase 1).
"""

from django.contrib.gis.geos import Point
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.locations.models import UserLocation


class AuthAPITests(TestCase):
    """Tests for authentication endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_register_success(self):
        """POST /api/v1/auth/register/ should create a user."""
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "email": "newuser@example.com",
                "full_name": "New User",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "account_type": "individual",
                "eula_accepted": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertTrue(
            User.objects.filter(email="newuser@example.com").exists()
        )

    def test_register_without_eula(self):
        """Registration should fail if EULA is not accepted."""
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "email": "noeula@example.com",
                "full_name": "No EULA",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "account_type": "individual",
                "eula_accepted": False,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch(self):
        """Registration should fail if passwords don't match."""
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "email": "mismatch@example.com",
                "full_name": "Mismatch",
                "password": "SecurePass123!",
                "password_confirm": "DifferentPass456!",
                "account_type": "individual",
                "eula_accepted": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """POST /api/v1/auth/login/ should return JWT tokens."""
        User.objects.create_user(
            email="login@example.com",
            password="SecurePass123!",
            eula_accepted=True,
        )
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "login@example.com", "password": "SecurePass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["data"])
        self.assertIn("refresh", response.data["data"])

    def test_login_suspended_user(self):
        """Suspended users should not be able to log in."""
        user = User.objects.create_user(
            email="suspended@example.com",
            password="SecurePass123!",
            eula_accepted=True,
        )
        user.suspend()
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "suspended@example.com", "password": "SecurePass123!"},
            format="json",
        )
        # Should either be 403 or 401 depending on whether DRF catches first
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )


class ProfileAPITests(TestCase):
    """Tests for profile endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="profileapi@example.com",
            full_name="Profile API",
            password="SecurePass123!",
            account_type="individual",
            eula_accepted=True,
        )
        self.client.force_authenticate(user=self.user)

    def test_get_own_profile(self):
        """GET /api/v1/profile/me/ should return the user's profile."""
        response = self.client.get("/api/v1/profile/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["display_name"], "Profile API")

    def test_update_profile(self):
        """PATCH /api/v1/profile/me/ should update skills and bio."""
        response = self.client.patch(
            "/api/v1/profile/me/",
            {
                "bio": "Updated bio text",
                "skills": ["plumbing", "tutoring"],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["bio"], "Updated bio text")
        self.assertEqual(
            response.data["data"]["skills"], ["plumbing", "tutoring"]
        )


class LocationAPITests(TestCase):
    """Tests for location endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="locapi@example.com",
            full_name="Location API",
            password="SecurePass123!",
            account_type="individual",
            eula_accepted=True,
        )
        self.client.force_authenticate(user=self.user)

    def test_update_location(self):
        """POST /api/v1/location/update/ should create/update location."""
        response = self.client.post(
            "/api/v1/location/update/",
            {"latitude": 24.8607, "longitude": 67.0011, "source": "gps"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertTrue(UserLocation.objects.filter(user=self.user).exists())

    def test_update_location_invalid_coords(self):
        """Invalid coordinates should be rejected."""
        response = self.client.post(
            "/api/v1/location/update/",
            {"latitude": 999, "longitude": 67.0011},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_explore_without_location(self):
        """Explore should fail if the user has no location set."""
        response = self.client.get("/api/v1/explore/nearby/?radius=500")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_explore_with_location(self):
        """Explore should return results when location is set."""
        # Set the user's location
        UserLocation.objects.create(
            user=self.user,
            point=Point(67.0011, 24.8607, srid=4326),
            obfuscated_point=Point(67.0011, 24.8607, srid=4326),
        )
        response = self.client.get("/api/v1/explore/nearby/?radius=500")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("results", response.data["data"])
