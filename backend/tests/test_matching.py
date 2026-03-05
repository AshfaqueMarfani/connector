"""
Phase 3 Tests: AI Matching, Data Ingestion, Profile Tags.

Covers:
- AIService keyword-based intent parsing (fallback mode)
- AIService profile tag generation
- AIService match scoring algorithm
- parse_status_intent Celery task
- find_matches_for_status Celery task (spatial + scoring)
- expire_old_statuses periodic task
- generate_profile_tags Celery task
- Match list / dismiss API endpoints
- Generate-tags API endpoint
- Data ingestion API (admin only)
- Data ingestion job lifecycle
- Permission enforcement (admin-only endpoints)
- Status creation triggers AI parsing
"""

from datetime import timedelta
from unittest.mock import patch

from django.contrib.gis.geos import Point
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.chat.models import Notification
from apps.locations.models import UserLocation
from apps.matching.models import AIMatchResult, DataIngestionJob
from apps.matching.services import AIService
from apps.profiles.models import Profile
from apps.statuses.models import Status


# ======================================================================
# AI Service Unit Tests (keyword fallback — no OpenAI key)
# ======================================================================
class AIServiceParsingTests(TestCase):
    """Test the keyword-based fallback AI service."""

    def test_parse_food_need(self):
        """Parsing a food-related need should extract food tags."""
        result = AIService.parse_status_intent(
            "Need emergency food assistance for my family",
            status_type="need",
        )
        self.assertIn("food", result["tags"])
        self.assertEqual(result["category"], "food")
        self.assertIn("emergency", result["urgency_hint"])
        self.assertTrue(len(result["parsed_intent"]) > 0)

    def test_parse_medical_offer(self):
        """Parsing a medical offer should extract medical tags."""
        result = AIService.parse_status_intent(
            "Offering free medical consultation at my clinic today",
            status_type="offer",
        )
        self.assertIn("medical", result["tags"])
        self.assertEqual(result["category"], "medical")
        self.assertIn("offers", result["parsed_intent"])

    def test_parse_education_need(self):
        """Parsing an education-related need."""
        result = AIService.parse_status_intent(
            "Looking for a tutor who can teach programming basics",
            status_type="need",
        )
        self.assertIn("education", result["tags"])

    def test_parse_multiple_categories(self):
        """A status mentioning food and shelter should get both tags."""
        result = AIService.parse_status_intent(
            "Need food and shelter for refugees arriving tonight",
            status_type="need",
        )
        self.assertIn("food", result["tags"])
        self.assertIn("shelter", result["tags"])
        self.assertEqual(result["urgency_hint"], "high")  # "need" is a high word

    def test_parse_unknown_category(self):
        """Unrecognised text should return 'general' category."""
        result = AIService.parse_status_intent(
            "Something very abstract with no obvious keywords",
            status_type="need",
        )
        self.assertEqual(result["category"], "general")

    def test_urgency_emergency_detection(self):
        """Emergency keywords should set urgency to emergency."""
        result = AIService.parse_status_intent(
            "URGENT need for blood donation type O+",
            status_type="need",
        )
        self.assertEqual(result["urgency_hint"], "emergency")


class AIServiceTagGenerationTests(TestCase):
    """Test keyword-based profile tag generation."""

    def test_generate_tags_from_skills(self):
        """Skills like plumbing should produce 'utilities' tag."""
        tags = AIService.generate_profile_tags(
            skills=["plumbing", "electrical repair"],
            interests=[],
            bio="Experienced handyman",
        )
        self.assertIn("utilities", tags)

    def test_generate_tags_from_interests(self):
        """Interests like food distribution should produce 'food' tag."""
        tags = AIService.generate_profile_tags(
            skills=[],
            interests=["food distribution", "community outreach"],
            bio="",
        )
        self.assertIn("food", tags)
        self.assertIn("community", tags)

    def test_generate_generic(self):
        """No matching keywords should return ['general']."""
        tags = AIService.generate_profile_tags(
            skills=["abstract art"],
            interests=["philosophy"],
            bio="Thinker",
        )
        self.assertEqual(tags, ["general"])


class AIServiceScoringTests(TestCase):
    """Test the match scoring algorithm."""

    def test_perfect_tag_match(self):
        """Perfect tag overlap + close distance = high score."""
        result = AIService.compute_match_score(
            status_tags=["food", "shelter"],
            profile_tags=["food", "shelter"],
            profile_skills=[],
            profile_interests=[],
            distance_meters=50,
            status_type="need",
        )
        self.assertGreater(result["score"], 0.8)
        self.assertIn("food", result["matched_tags"])
        self.assertIn("shelter", result["matched_tags"])

    def test_no_tag_match_far_distance(self):
        """No tag overlap + far distance = low score."""
        result = AIService.compute_match_score(
            status_tags=["food"],
            profile_tags=["technology"],
            profile_skills=[],
            profile_interests=[],
            distance_meters=8000,
            status_type="need",
        )
        self.assertLess(result["score"], 0.3)

    def test_skills_contribute_to_matching(self):
        """Profile skills should be included in matching."""
        result = AIService.compute_match_score(
            status_tags=["food"],
            profile_tags=[],
            profile_skills=["food"],
            profile_interests=[],
            distance_meters=200,
            status_type="need",
        )
        # "food" in skills matches "food" in status tags
        self.assertIn("food", result["matched_tags"])
        self.assertGreater(result["score"], 0.5)

    def test_distance_scoring(self):
        """Closer distance should result in higher score."""
        close = AIService.compute_match_score(
            status_tags=["food"],
            profile_tags=["food"],
            profile_skills=[],
            profile_interests=[],
            distance_meters=50,
        )
        far = AIService.compute_match_score(
            status_tags=["food"],
            profile_tags=["food"],
            profile_skills=[],
            profile_interests=[],
            distance_meters=8000,
        )
        self.assertGreater(close["score"], far["score"])

    def test_type_bonus(self):
        """Need + skilled profile should get type bonus."""
        with_bonus = AIService.compute_match_score(
            status_tags=["food"],
            profile_tags=["food"],
            profile_skills=["cooking"],
            profile_interests=[],
            distance_meters=200,
            status_type="need",
        )
        without_bonus = AIService.compute_match_score(
            status_tags=["food"],
            profile_tags=["food"],
            profile_skills=[],
            profile_interests=[],
            distance_meters=200,
            status_type="offer",
        )
        self.assertGreater(with_bonus["score"], without_bonus["score"])


# ======================================================================
# Celery Task Tests (synchronous execution via ALWAYS_EAGER)
# ======================================================================
@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}},
)
class ParseStatusIntentTaskTests(TestCase):
    """Test the parse_status_intent Celery task."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="taskuser@test.com",
            password="TestPass123!",
            full_name="Task User",
            account_type="individual",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )
        UserLocation.objects.create(
            user=self.user,
            point=Point(67.0011, 24.8607, srid=4326),
            obfuscated_point=Point(67.002, 24.861, srid=4326),
        )

    def test_parse_status_updates_fields(self):
        """Task should update ai_parsed_intent and ai_tags on the status."""
        from apps.matching.tasks import parse_status_intent

        s = Status.objects.create(
            user=self.user,
            status_type="need",
            text="Need emergency food assistance for family of five",
            urgency="emergency",
            location_snapshot=Point(67.0011, 24.8607, srid=4326),
        )

        result = parse_status_intent(str(s.id))

        s.refresh_from_db()
        self.assertTrue(len(s.ai_parsed_intent) > 0)
        self.assertIn("food", s.ai_tags)
        self.assertEqual(result["tags"], s.ai_tags)

    def test_parse_nonexistent_status(self):
        """Task should return None for non-existent status."""
        from apps.matching.tasks import parse_status_intent

        result = parse_status_intent("00000000-0000-0000-0000-000000000000")
        self.assertIsNone(result)

    def test_parse_inactive_status(self):
        """Task should skip inactive statuses."""
        from apps.matching.tasks import parse_status_intent

        s = Status.objects.create(
            user=self.user,
            status_type="need",
            text="Need food assistance but this is deactivated",
            is_active=False,
        )
        result = parse_status_intent(str(s.id))
        self.assertIsNone(result)


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}},
)
class FindMatchesTaskTests(TestCase):
    """Test the find_matches_for_status Celery task (spatial matching)."""

    def setUp(self):
        # Create status poster (Karachi center)
        self.poster = User.objects.create_user(
            email="poster@test.com",
            password="TestPass123!",
            full_name="Status Poster",
            account_type="individual",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )
        self.poster.profile.tags = ["food"]
        self.poster.profile.save()
        UserLocation.objects.create(
            user=self.poster,
            point=Point(67.0011, 24.8607, srid=4326),
            obfuscated_point=Point(67.002, 24.861, srid=4326),
        )

        # Create nearby NGO with food tag (~200m away)
        self.ngo = User.objects.create_user(
            email="ngo@test.com",
            password="TestPass123!",
            full_name="Food Relief NGO",
            account_type="ngo",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )
        self.ngo.profile.tags = ["food", "shelter"]
        self.ngo.profile.skills = ["food distribution"]
        self.ngo.profile.is_public = True
        self.ngo.profile.save()
        UserLocation.objects.create(
            user=self.ngo,
            point=Point(67.0030, 24.8620, srid=4326),
            obfuscated_point=Point(67.0030, 24.8620, srid=4326),
        )

        # Create far-away user (way outside any radius)
        self.far_user = User.objects.create_user(
            email="faraway@test.com",
            password="TestPass123!",
            full_name="Far Away User",
            account_type="individual",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )
        self.far_user.profile.tags = ["food"]
        self.far_user.profile.save()
        UserLocation.objects.create(
            user=self.far_user,
            point=Point(70.0, 30.0, srid=4326),  # ~600km away
            obfuscated_point=Point(70.0, 30.0, srid=4326),
        )

    def test_finds_nearby_matching_user(self):
        """Should find the nearby NGO with matching food tag."""
        from apps.matching.tasks import find_matches_for_status

        s = Status.objects.create(
            user=self.poster,
            status_type="need",
            text="Need emergency food assistance",
            urgency="medium",
            ai_tags=["food"],
            location_snapshot=Point(67.0011, 24.8607, srid=4326),
        )

        result = find_matches_for_status(str(s.id))

        self.assertEqual(result["matches_created"], 1)
        match = AIMatchResult.objects.get(status=s, matched_user=self.ngo)
        self.assertGreater(match.score, 0.4)
        self.assertIn("food", match.matched_tags)
        self.assertIsNotNone(match.distance_meters)

    def test_does_not_match_far_user(self):
        """User 600km away should NOT be matched (radius ~1km for medium)."""
        from apps.matching.tasks import find_matches_for_status

        s = Status.objects.create(
            user=self.poster,
            status_type="need",
            text="Need food assistance",
            urgency="medium",
            ai_tags=["food"],
            location_snapshot=Point(67.0011, 24.8607, srid=4326),
        )

        find_matches_for_status(str(s.id))
        self.assertFalse(
            AIMatchResult.objects.filter(
                status=s, matched_user=self.far_user,
            ).exists()
        )

    def test_creates_notifications_for_both_parties(self):
        """Both the poster and matched user should get AI_MATCH notifications."""
        from apps.matching.tasks import find_matches_for_status

        s = Status.objects.create(
            user=self.poster,
            status_type="need",
            text="Need emergency food assistance",
            urgency="medium",
            ai_tags=["food"],
            location_snapshot=Point(67.0011, 24.8607, srid=4326),
        )

        find_matches_for_status(str(s.id))

        # Matched user (NGO) should be notified
        ngo_notifs = Notification.objects.filter(
            user=self.ngo,
            notification_type=Notification.NotificationType.AI_MATCH,
        )
        self.assertEqual(ngo_notifs.count(), 1)
        self.assertIn("food", ngo_notifs.first().data.get("matched_tags", []))

        # Status owner (poster) should also be notified
        poster_notifs = Notification.objects.filter(
            user=self.poster,
            notification_type=Notification.NotificationType.AI_MATCH,
        )
        self.assertEqual(poster_notifs.count(), 1)

    def test_blocked_users_excluded(self):
        """Blocked users should not appear in matches."""
        from apps.matching.tasks import find_matches_for_status
        from apps.moderation.models import Block

        Block.objects.create(blocker=self.poster, blocked=self.ngo)

        s = Status.objects.create(
            user=self.poster,
            status_type="need",
            text="Need food assistance",
            urgency="medium",
            ai_tags=["food"],
            location_snapshot=Point(67.0011, 24.8607, srid=4326),
        )

        result = find_matches_for_status(str(s.id))
        self.assertEqual(result["matches_created"], 0)

    def test_emergency_uses_larger_radius(self):
        """Emergency urgency should use 10km radius."""
        from apps.matching.tasks import find_matches_for_status

        # Create a user ~8km away (still within 10km emergency radius)
        mid_user = User.objects.create_user(
            email="midrange@test.com",
            password="TestPass123!",
            full_name="Mid Range User",
            account_type="ngo",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )
        mid_user.profile.tags = ["food"]
        mid_user.profile.is_public = True
        mid_user.profile.save()
        # ~8km away from poster (approx 0.07 degrees lat)
        UserLocation.objects.create(
            user=mid_user,
            point=Point(67.0011, 24.9307, srid=4326),
            obfuscated_point=Point(67.0011, 24.9307, srid=4326),
        )

        s = Status.objects.create(
            user=self.poster,
            status_type="need",
            text="EMERGENCY food assistance needed urgently",
            urgency="emergency",
            ai_tags=["food"],
            location_snapshot=Point(67.0011, 24.8607, srid=4326),
        )

        result = find_matches_for_status(str(s.id))
        # Should match both the nearby NGO and the mid-range user
        self.assertGreaterEqual(result["matches_created"], 2)


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}},
)
class ExpireStatusesTaskTests(TestCase):
    """Test the expire_old_statuses periodic task."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="expire@test.com",
            password="TestPass123!",
            full_name="Expire User",
            account_type="individual",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )

    def test_expires_past_expiry(self):
        """Statuses with expires_at in the past should be deactivated."""
        from apps.matching.tasks import expire_old_statuses

        s = Status.objects.create(
            user=self.user,
            status_type="need",
            text="This should expire soon based on expiry time",
            expires_at=timezone.now() - timedelta(hours=1),
        )

        result = expire_old_statuses()
        s.refresh_from_db()
        self.assertFalse(s.is_active)
        self.assertEqual(result["expired"], 1)

    def test_expires_stale_statuses(self):
        """Statuses >7 days old without explicit expiry should be deactivated."""
        from apps.matching.tasks import expire_old_statuses

        s = Status.objects.create(
            user=self.user,
            status_type="offer",
            text="This is a stale old status without expiration set",
        )
        # Backdate
        Status.objects.filter(id=s.id).update(
            created_at=timezone.now() - timedelta(days=8),
        )

        result = expire_old_statuses()
        s.refresh_from_db()
        self.assertFalse(s.is_active)
        self.assertEqual(result["stale"], 1)

    def test_active_status_not_expired(self):
        """Recent statuses with future expiry should remain active."""
        from apps.matching.tasks import expire_old_statuses

        s = Status.objects.create(
            user=self.user,
            status_type="need",
            text="This status is still valid and should not be expired",
            expires_at=timezone.now() + timedelta(hours=24),
        )

        expire_old_statuses()
        s.refresh_from_db()
        self.assertTrue(s.is_active)

    def test_expired_matches_updated(self):
        """Match results for expired statuses should be marked expired."""
        from apps.matching.tasks import expire_old_statuses

        other_user = User.objects.create_user(
            email="other@test.com",
            password="TestPass123!",
            full_name="Other User",
            account_type="ngo",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )

        s = Status.objects.create(
            user=self.user,
            status_type="need",
            text="This should expire and its matches too should expire",
            expires_at=timezone.now() - timedelta(hours=1),
        )
        match = AIMatchResult.objects.create(
            status=s,
            status_owner=self.user,
            matched_user=other_user,
            score=0.8,
            match_status=AIMatchResult.MatchStatus.PENDING,
        )

        expire_old_statuses()
        match.refresh_from_db()
        self.assertEqual(match.match_status, AIMatchResult.MatchStatus.EXPIRED)


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}},
)
class GenerateProfileTagsTaskTests(TestCase):
    """Test the generate_profile_tags Celery task."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="taguser@test.com",
            password="TestPass123!",
            full_name="Tag User",
            account_type="business",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )
        self.user.profile.skills = ["plumbing", "electrical repair"]
        self.user.profile.interests = ["community service"]
        self.user.profile.bio = "Local handyman offering repairs"
        self.user.profile.save()

    def test_generates_tags(self):
        """Task should populate profile.tags from skills/interests."""
        from apps.matching.tasks import generate_profile_tags

        result = generate_profile_tags(str(self.user.profile.id))

        self.user.profile.refresh_from_db()
        self.assertTrue(len(self.user.profile.tags) > 0)
        self.assertIn("utilities", self.user.profile.tags)
        self.assertEqual(result["tags"], self.user.profile.tags)

    def test_nonexistent_profile(self):
        """Task should return None for non-existent profile."""
        from apps.matching.tasks import generate_profile_tags

        result = generate_profile_tags("00000000-0000-0000-0000-000000000000")
        self.assertIsNone(result)


# ======================================================================
# API Endpoint Tests
# ======================================================================
@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}},
)
class MatchAPITests(TestCase):
    """Test match list and dismiss API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user_a = User.objects.create_user(
            email="matcha@test.com",
            password="TestPass123!",
            full_name="Match User A",
            account_type="individual",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )
        self.user_b = User.objects.create_user(
            email="matchb@test.com",
            password="TestPass123!",
            full_name="Match User B",
            account_type="ngo",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )

        # Create a status and match
        self.test_status = Status.objects.create(
            user=self.user_a,
            status_type="need",
            text="Need food assistance for this test case",
            ai_tags=["food"],
        )
        self.match = AIMatchResult.objects.create(
            status=self.test_status,
            status_owner=self.user_a,
            matched_user=self.user_b,
            score=0.85,
            reason="Matched tags: food",
            matched_tags=["food"],
            distance_meters=150.0,
        )

    def test_list_matches_for_matched_user(self):
        """Matched user should see their match suggestions."""
        self.client.force_authenticate(user=self.user_b)
        resp = self.client.get("/api/v1/matches/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(
            resp.data["results"][0]["id"],
            str(self.match.id),
        )

    def test_list_matches_sent(self):
        """Status owner should see matches from their statuses."""
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get("/api/v1/matches/sent/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_dismiss_match(self):
        """Dismissing a match should update its status."""
        self.client.force_authenticate(user=self.user_b)
        resp = self.client.post(f"/api/v1/matches/{self.match.id}/dismiss/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.match.refresh_from_db()
        self.assertEqual(
            self.match.match_status, AIMatchResult.MatchStatus.DISMISSED,
        )

    def test_dismiss_nonexistent_match(self):
        """Dismissing a non-existent match should return 404."""
        self.client.force_authenticate(user=self.user_b)
        resp = self.client.post(
            "/api/v1/matches/00000000-0000-0000-0000-000000000000/dismiss/"
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_dismiss_others_match(self):
        """User A should not be able to dismiss User B's match."""
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.post(f"/api/v1/matches/{self.match.id}/dismiss/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_viewing_marks_pending_as_viewed(self):
        """Listing matches should update PENDING → VIEWED."""
        self.assertEqual(
            self.match.match_status, AIMatchResult.MatchStatus.PENDING,
        )
        self.client.force_authenticate(user=self.user_b)
        self.client.get("/api/v1/matches/")

        self.match.refresh_from_db()
        self.assertEqual(
            self.match.match_status, AIMatchResult.MatchStatus.VIEWED,
        )

    def test_unauthenticated_access_rejected(self):
        """Unauthenticated requests should be rejected."""
        resp = self.client.get("/api/v1/matches/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class GenerateTagsAPITests(TestCase):
    """Test the generate-tags API endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="tagapi@test.com",
            password="TestPass123!",
            full_name="Tag API User",
            account_type="individual",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
    )
    def test_generate_tags_endpoint(self):
        """POST to generate-tags should queue tag generation."""
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/v1/ai/generate-tags/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])

    def test_unauthenticated_rejected(self):
        """Unauthenticated requests should be rejected."""
        resp = self.client.post("/api/v1/ai/generate-tags/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ======================================================================
# Data Ingestion API Tests
# ======================================================================
@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}},
)
class DataIngestionAPITests(TestCase):
    """Test data ingestion endpoints (admin only)."""

    def setUp(self):
        self.client = APIClient()
        # Admin user
        self.admin = User.objects.create_superuser(
            email="ingestadmin@test.com",
            password="AdminPass123!",
            full_name="Ingest Admin",
        )
        # Regular user
        self.regular = User.objects.create_user(
            email="regular@test.com",
            password="TestPass123!",
            full_name="Regular User",
            account_type="individual",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )

    def test_ingest_entities(self):
        """Admin should be able to ingest entities."""
        self.client.force_authenticate(user=self.admin)
        payload = {
            "source_name": "Karachi NGO Directory",
            "entities": [
                {
                    "name": "Test Food Bank",
                    "bio": "Providing food to families in need",
                    "account_type": "ngo",
                    "tags": ["food", "community"],
                    "skills": ["food distribution"],
                    "lat": 24.8607,
                    "lon": 67.0011,
                },
                {
                    "name": "Repair Services Inc",
                    "bio": "Mobile phone and laptop repairs",
                    "account_type": "business",
                    "tags": ["technology"],
                    "lat": 24.8700,
                    "lon": 67.0100,
                },
            ],
        }

        resp = self.client.post(
            "/api/v1/admin-api/ingest/",
            data=payload,
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(resp.data["success"])

        # Job should be created
        job = DataIngestionJob.objects.first()
        self.assertIsNotNone(job)
        # Since ALWAYS_EAGER, job should be completed
        job.refresh_from_db()
        self.assertEqual(job.job_status, DataIngestionJob.JobStatus.COMPLETED)
        self.assertEqual(job.processed_records, 2)
        self.assertEqual(job.failed_records, 0)

        # Users should have been created
        self.assertTrue(User.objects.filter(full_name="Test Food Bank").exists())
        self.assertTrue(User.objects.filter(full_name="Repair Services Inc").exists())

    def test_ingest_rejects_missing_name(self):
        """Entities without a name field should be rejected."""
        self.client.force_authenticate(user=self.admin)
        payload = {
            "entities": [{"bio": "No name here"}],
        }
        resp = self.client.post(
            "/api/v1/admin-api/ingest/",
            data=payload,
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_regular_user_cannot_ingest(self):
        """Non-admin users should get 403."""
        self.client.force_authenticate(user=self.regular)
        payload = {
            "entities": [{"name": "Blocked Entity"}],
        }
        resp = self.client.post(
            "/api/v1/admin-api/ingest/",
            data=payload,
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_ingest_rejected(self):
        """Unauthenticated ingestion should be rejected."""
        payload = {"entities": [{"name": "Anon Entity"}]}
        resp = self.client.post(
            "/api/v1/admin-api/ingest/",
            data=payload,
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_ingestion_jobs(self):
        """Admin should be able to list ingestion jobs."""
        self.client.force_authenticate(user=self.admin)
        DataIngestionJob.objects.create(
            initiated_by=self.admin,
            source_name="Test Source",
        )
        resp = self.client.get("/api/v1/admin-api/ingest/jobs/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_job_detail(self):
        """Admin should be able to see job details."""
        self.client.force_authenticate(user=self.admin)
        job = DataIngestionJob.objects.create(
            initiated_by=self.admin,
            source_name="Detail Test",
        )
        resp = self.client.get(f"/api/v1/admin-api/ingest/jobs/{job.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["source_name"], "Detail Test")

    def test_regular_user_cannot_list_jobs(self):
        """Non-admin users should get 403 for job listing."""
        self.client.force_authenticate(user=self.regular)
        resp = self.client.get("/api/v1/admin-api/ingest/jobs/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


# ======================================================================
# Integration: Status Creation Triggers AI Parsing
# ======================================================================
@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}},
)
class StatusCreationTriggerTests(TestCase):
    """Test that creating a status via API triggers AI parsing."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="trigger@test.com",
            password="TestPass123!",
            full_name="Trigger User",
            account_type="individual",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )
        UserLocation.objects.create(
            user=self.user,
            point=Point(67.0011, 24.8607, srid=4326),
            obfuscated_point=Point(67.002, 24.861, srid=4326),
        )
        self.client.force_authenticate(user=self.user)

    def test_status_creation_triggers_parsing(self):
        """Creating a status should trigger AI parsing and update fields."""
        resp = self.client.post(
            "/api/v1/status/",
            data={
                "status_type": "need",
                "text": "Need emergency food supplies for displaced families",
                "urgency": "high",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Verify the status was AI-parsed
        created_status = Status.objects.get(id=resp.data["data"]["id"])
        self.assertTrue(len(created_status.ai_parsed_intent) > 0)
        self.assertIn("food", created_status.ai_tags)

    def test_status_creation_triggers_matching(self):
        """Creating a status near a matching user should create a match."""
        # Create a nearby NGO
        ngo = User.objects.create_user(
            email="nearbyngo@test.com",
            password="TestPass123!",
            full_name="Nearby Food NGO",
            account_type="ngo",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )
        ngo.profile.tags = ["food", "shelter"]
        ngo.profile.is_public = True
        ngo.profile.save()
        UserLocation.objects.create(
            user=ngo,
            point=Point(67.0030, 24.8620, srid=4326),
            obfuscated_point=Point(67.0030, 24.8620, srid=4326),
        )

        resp = self.client.post(
            "/api/v1/status/",
            data={
                "status_type": "need",
                "text": "Need emergency food assistance for my neighbourhood",
                "urgency": "high",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Verify match was created
        matches = AIMatchResult.objects.filter(
            status_owner=self.user, matched_user=ngo,
        )
        self.assertEqual(matches.count(), 1)
        self.assertIn("food", matches.first().matched_tags)

        # Verify notifications were sent
        self.assertTrue(
            Notification.objects.filter(
                user=ngo,
                notification_type=Notification.NotificationType.AI_MATCH,
            ).exists()
        )
