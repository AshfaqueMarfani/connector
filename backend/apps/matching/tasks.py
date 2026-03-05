"""
Celery tasks for the AI matching pipeline.

Task chain on status creation:
  1. ``parse_status_intent`` → AI/keyword parsing → updates Status fields
  2. ``find_matches_for_status`` → PostGIS radius query + scoring → creates AIMatchResult records + notifications

Periodic tasks:
  - ``expire_old_statuses`` → deactivates expired/stale statuses
  - ``run_batch_matching`` → re-runs matching for all active statuses
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger("apps")

# Matching radius (meters) by urgency level
URGENCY_RADIUS = {
    "low": 500,
    "medium": 1000,
    "high": 3000,
    "emergency": 10000,
}


# ------------------------------------------------------------------
# Status Intent Parsing
# ------------------------------------------------------------------
@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def parse_status_intent(self, status_id: str):
    """Parse a status with AI and update ``ai_parsed_intent`` / ``ai_tags``."""
    from apps.statuses.models import Status
    from apps.matching.services import AIService

    try:
        status = Status.objects.get(id=status_id, is_active=True)
    except Status.DoesNotExist:
        logger.warning("Status %s not found or inactive", status_id)
        return None

    try:
        result = AIService.parse_status_intent(status.text, status.status_type)

        status.ai_parsed_intent = result["parsed_intent"]
        status.ai_tags = result["tags"]
        status.save(update_fields=["ai_parsed_intent", "ai_tags", "updated_at"])

        logger.info(
            "Parsed status %s: tags=%s, category=%s",
            status_id, result["tags"], result["category"],
        )

        # Chain: trigger matching after parsing
        find_matches_for_status.delay(status_id)

        return {
            "status_id": status_id,
            "tags": result["tags"],
            "category": result["category"],
        }
    except Exception as exc:
        logger.error("Failed to parse status %s: %s", status_id, exc)
        raise self.retry(exc=exc)


# ------------------------------------------------------------------
# Spatial Matching
# ------------------------------------------------------------------
@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def find_matches_for_status(self, status_id: str):
    """
    Find nearby matching users/entities for a status and create
    ``AIMatchResult`` records + notifications.
    """
    from django.contrib.gis.db.models.functions import Distance
    from django.contrib.gis.measure import D

    from apps.locations.models import UserLocation
    from apps.matching.models import AIMatchResult
    from apps.matching.services import AIService
    from apps.moderation.models import Block
    from apps.statuses.models import Status

    try:
        status = Status.objects.select_related(
            "user", "user__profile",
        ).get(id=status_id, is_active=True)
    except Status.DoesNotExist:
        logger.warning("Status %s not found", status_id)
        return None

    # Determine search radius from urgency
    radius = URGENCY_RADIUS.get(status.urgency, 1000)

    # Get the search origin (status snapshot or user's current location)
    search_point = status.location_snapshot
    if not search_point:
        try:
            user_loc = UserLocation.objects.get(user=status.user)
            search_point = user_loc.point
        except UserLocation.DoesNotExist:
            logger.warning("No location for status %s user", status_id)
            return None

    # Gather blocked user IDs (both directions)
    blocked_ids = set(
        Block.objects.filter(blocker=status.user).values_list(
            "blocked_id", flat=True,
        )
    ) | set(
        Block.objects.filter(blocked=status.user).values_list(
            "blocker_id", flat=True,
        )
    )

    # PostGIS radius query
    nearby_locations = (
        UserLocation.objects.filter(
            point__dwithin=(search_point, D(m=radius)),
            user__is_active=True,
        )
        .exclude(user=status.user)
        .exclude(user_id__in=blocked_ids)
        .annotate(distance=Distance("point", search_point))
        .select_related("user", "user__profile")
        .order_by("distance")[:50]
    )

    matches_created = 0
    status_tags = status.ai_tags or []

    for loc in nearby_locations:
        profile = loc.user.profile

        # Compute match score
        score_result = AIService.compute_match_score(
            status_tags=status_tags,
            profile_tags=profile.tags or [],
            profile_skills=profile.skills or [],
            profile_interests=profile.interests or [],
            distance_meters=loc.distance.m if loc.distance else None,
            status_type=status.status_type,
        )

        # Skip low-relevance matches
        if score_result["score"] < 0.2:
            continue

        # Upsert match record
        match_obj, created = AIMatchResult.objects.update_or_create(
            status=status,
            matched_user=loc.user,
            defaults={
                "status_owner": status.user,
                "score": score_result["score"],
                "reason": score_result["reason"],
                "matched_tags": score_result["matched_tags"],
                "distance_meters": loc.distance.m if loc.distance else None,
                "match_status": AIMatchResult.MatchStatus.PENDING,
            },
        )

        if created:
            matches_created += 1
            # Notify the matched user
            _send_match_notification(status, loc.user, score_result)
            # Notify the status owner
            _send_match_notification_to_owner(status, loc.user, score_result)

    logger.info("Found %d new matches for status %s", matches_created, status_id)
    return {"status_id": status_id, "matches_created": matches_created}


def _send_match_notification(status, matched_user, score_result):
    """Send an AI-match notification to the matched user."""
    from apps.chat.models import Notification

    try:
        from apps.chat.utils import send_realtime_notification
    except ImportError:
        send_realtime_notification = None

    notification = Notification.objects.create(
        user=matched_user,
        notification_type=Notification.NotificationType.AI_MATCH,
        title=f"Relevant {status.get_status_type_display()} nearby",
        body=f"{status.user.full_name}: {status.text[:100]}",
        data={
            "status_id": str(status.id),
            "status_owner_id": str(status.user.id),
            "match_score": score_result["score"],
            "matched_tags": score_result["matched_tags"],
        },
    )

    if send_realtime_notification:
        try:
            send_realtime_notification(matched_user.id, notification)
        except Exception as e:
            logger.warning("Failed to push realtime match notification: %s", e)


def _send_match_notification_to_owner(status, matched_user, score_result):
    """Notify the status owner about a matching user."""
    from apps.chat.models import Notification

    try:
        from apps.chat.utils import send_realtime_notification
    except ImportError:
        send_realtime_notification = None

    notification = Notification.objects.create(
        user=status.user,
        notification_type=Notification.NotificationType.AI_MATCH,
        title="Someone nearby matches your broadcast",
        body=(
            f"{matched_user.full_name} matches your "
            f"{status.get_status_type_display().lower()}"
        ),
        data={
            "status_id": str(status.id),
            "matched_user_id": str(matched_user.id),
            "match_score": score_result["score"],
            "matched_tags": score_result["matched_tags"],
        },
    )

    if send_realtime_notification:
        try:
            send_realtime_notification(status.user.id, notification)
        except Exception as e:
            logger.warning("Failed to push realtime match notification: %s", e)


# ------------------------------------------------------------------
# Profile Tag Generation
# ------------------------------------------------------------------
@shared_task
def generate_profile_tags(profile_id: str):
    """Generate AI tags for a profile based on skills, interests, and bio."""
    from apps.matching.services import AIService
    from apps.profiles.models import Profile

    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        logger.warning("Profile %s not found", profile_id)
        return None

    tags = AIService.generate_profile_tags(
        skills=profile.skills or [],
        interests=profile.interests or [],
        bio=profile.bio or "",
    )

    profile.tags = tags
    profile.save(update_fields=["tags", "updated_at"])

    logger.info("Generated tags for profile %s: %s", profile_id, tags)
    return {"profile_id": profile_id, "tags": tags}


# ------------------------------------------------------------------
# Periodic: Status Expiration
# ------------------------------------------------------------------
@shared_task
def expire_old_statuses():
    """Deactivate statuses past their expiry or older than 7 days."""
    from apps.matching.models import AIMatchResult
    from apps.statuses.models import Status

    now = timezone.now()

    # Explicit expiry
    expired = Status.objects.filter(
        is_active=True,
        expires_at__lte=now,
    ).update(is_active=False)

    # Stale (>7 days, no explicit expiry)
    stale_cutoff = now - timedelta(days=7)
    stale = Status.objects.filter(
        is_active=True,
        expires_at__isnull=True,
        created_at__lte=stale_cutoff,
    ).update(is_active=False)

    # Expire related match results
    AIMatchResult.objects.filter(
        status__is_active=False,
        match_status__in=[
            AIMatchResult.MatchStatus.PENDING,
            AIMatchResult.MatchStatus.NOTIFIED,
        ],
    ).update(match_status=AIMatchResult.MatchStatus.EXPIRED)

    logger.info(
        "Expired %d statuses (expiry), %d stale statuses", expired, stale,
    )
    return {"expired": expired, "stale": stale}


# ------------------------------------------------------------------
# Periodic: Batch Matching
# ------------------------------------------------------------------
@shared_task
def run_batch_matching():
    """Re-run matching for all active, already-parsed statuses."""
    from apps.statuses.models import Status

    active_statuses = (
        Status.objects.filter(is_active=True)
        .exclude(ai_tags=[])
        .values_list("id", flat=True)
    )

    count = 0
    for status_id in active_statuses:
        find_matches_for_status.delay(str(status_id))
        count += 1

    logger.info("Queued batch matching for %d active statuses", count)
    return {"queued": count}


# ------------------------------------------------------------------
# Data Ingestion
# ------------------------------------------------------------------
@shared_task(bind=True, max_retries=2)
def process_ingestion_job(self, job_id: str, entities_data: list):
    """Process a bulk data ingestion job asynchronously."""
    from django.contrib.gis.geos import Point

    from apps.accounts.models import User
    from apps.locations.models import UserLocation
    from apps.matching.models import DataIngestionJob

    try:
        job = DataIngestionJob.objects.get(id=job_id)
    except DataIngestionJob.DoesNotExist:
        return None

    job.job_status = DataIngestionJob.JobStatus.PROCESSING
    job.total_records = len(entities_data)
    job.save(update_fields=["job_status", "total_records"])

    processed = 0
    failed = 0
    errors = []

    for i, entity in enumerate(entities_data):
        try:
            email = entity.get(
                "email",
                f"ingested_{i}_{str(job_id)[:8]}@connector.dev",
            )

            # Skip existing users
            if User.objects.filter(email=email).exists():
                processed += 1
                continue

            account_type = entity.get("account_type", "business")
            if account_type not in ("business", "ngo"):
                account_type = "business"

            # Create user (no password — ingested entity)
            user = User.objects.create_user(
                email=email,
                password=None,
                full_name=entity.get("name", f"Entity {i}"),
                account_type=account_type,
                eula_accepted=True,
            )
            user.set_unusable_password()
            user.save()

            # Update profile
            profile = user.profile
            profile.display_name = entity.get("name", f"Entity {i}")
            profile.bio = entity.get("bio", "")
            profile.skills = entity.get("skills", [])
            profile.interests = entity.get("interests", [])
            profile.tags = entity.get("tags", [])
            profile.is_public = True  # Ingested entities are always public
            profile.save()

            # Create location if coordinates provided
            lat = entity.get("latitude") or entity.get("lat")
            lon = entity.get("longitude") or entity.get("lon")
            if lat and lon:
                point = Point(float(lon), float(lat), srid=4326)
                UserLocation.objects.update_or_create(
                    user=user,
                    defaults={
                        "point": point,
                        "obfuscated_point": point,  # Public = exact
                    },
                )

            # Queue AI tag generation for the profile
            generate_profile_tags.delay(str(profile.id))
            processed += 1

        except Exception as e:
            failed += 1
            errors.append(f"Record {i}: {e!s}")
            logger.error("Ingestion error record %d: %s", i, e)

    job.processed_records = processed
    job.failed_records = failed
    job.error_log = "\n".join(errors)
    job.job_status = (
        DataIngestionJob.JobStatus.COMPLETED
        if failed == 0
        else DataIngestionJob.JobStatus.FAILED
    )
    job.completed_at = timezone.now()
    job.save()

    logger.info(
        "Ingestion job %s complete: %d processed, %d failed",
        job_id, processed, failed,
    )
    return {"job_id": job_id, "processed": processed, "failed": failed}
