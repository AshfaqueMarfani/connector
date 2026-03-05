"""
Management command to create 5 QA test agents for pre-launch testing.

These accounts cover all account types, privacy modes, status types,
and connection scenarios so every feature can be exercised before
submitting to Google Play / App Store.

Credentials:
  Email pattern:  agent<N>@otaskflow.com   (N = 1..5)
  Password:       TestAgent#2026

Run:
  docker-compose run --rm backend python manage.py create_test_agents
  docker-compose -f docker-compose.prod.yml run --rm backend python manage.py create_test_agents
"""

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.locations.models import UserLocation
from apps.statuses.models import Status


# ── Agent definitions ─────────────────────────────────────────────────────
AGENTS = [
    {
        "email": "agent1@otaskflow.com",
        "full_name": "Aisha Khan",
        "account_type": "individual",
        "bio": (
            "Community organizer & volunteer. Looking to connect"
            " with locals who need help with groceries,"
            " tutoring, or daily errands."
        ),
        "skills": ["tutoring", "cooking", "first aid", "translation"],
        "interests": ["food assistance", "education", "mentorship"],
        "tags": ["volunteer", "education", "community"],
        "lat": 24.8615,
        "lon": 67.0090,
        "status_type": "offer",
        "status_text": "Offering free English tutoring sessions for school students — weekdays 4-6 PM near Saddar.",
        "urgency": "low",
    },
    {
        "email": "agent2@otaskflow.com",
        "full_name": "Hassan Auto Workshop",
        "account_type": "business",
        "bio": (
            "Trusted auto repair & roadside assistance in"
            " Clifton. 15 years serving the community."
            " Fair prices, honest work."
        ),
        "skills": [],
        "interests": [],
        "tags": ["auto repair", "mechanic", "roadside assistance", "towing"],
        "lat": 24.8560,
        "lon": 66.9950,
        "status_type": "offer",
        "status_text": "20% discount on brake pad replacement this week — walk-ins welcome!",
        "urgency": "medium",
    },
    {
        "email": "agent3@otaskflow.com",
        "full_name": "Karachi Relief Foundation",
        "account_type": "ngo",
        "bio": (
            "Non-profit providing food, shelter, and medical"
            " aid to vulnerable communities across Karachi"
            " since 2018."
        ),
        "skills": [],
        "interests": [],
        "tags": ["food", "shelter", "medical", "disaster relief", "clothing"],
        "lat": 24.8700,
        "lon": 67.0150,
        "status_type": "need",
        "status_text": "Urgently need volunteer drivers to deliver food rations to 50 families in Lyari this Saturday.",
        "urgency": "high",
    },
    {
        "email": "agent4@otaskflow.com",
        "full_name": "Omar Farooq",
        "account_type": "individual",
        "bio": "Freelance electrician & plumber. Available for quick home repairs. Fair rates, same-day service.",
        "skills": ["electrician", "plumbing", "carpentry", "painting"],
        "interests": ["home repair jobs", "contract work"],
        "tags": ["handyman", "electrician", "plumber"],
        "lat": 24.8530,
        "lon": 67.0200,
        "status_type": "offer",
        "status_text": "Available today for emergency electrical and plumbing repairs — DM me your location.",
        "urgency": "medium",
    },
    {
        "email": "agent5@otaskflow.com",
        "full_name": "Sara's Kitchen & Catering",
        "account_type": "business",
        "bio": (
            "Home-style catering for events, offices, and"
            " families. Pakistani, continental & Chinese"
            " cuisine. Halal certified."
        ),
        "skills": [],
        "interests": [],
        "tags": ["restaurant", "catering", "food", "halal"],
        "lat": 24.8480,
        "lon": 66.9880,
        "status_type": "need",
        "status_text": "Looking for a reliable delivery rider for daily lunch box deliveries in Clifton & DHA area.",
        "urgency": "medium",
    },
]

PASSWORD = "TestAgent#2026"


class Command(BaseCommand):
    help = (
        "Create 5 QA test agents (agent1-5@otaskflow.com) with profiles, "
        "locations, and statuses for pre-launch testing."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing test agents before recreating them.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = User.objects.filter(
                email__in=[a["email"] for a in AGENTS]
            ).delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing objects."))

        self.stdout.write("")
        self.stdout.write("Creating 5 QA test agents for otaskflow.com...")
        self.stdout.write("=" * 55)

        created = 0

        for agent in AGENTS:
            email = agent["email"]

            if User.objects.filter(email=email).exists():
                self.stdout.write(f"  ⏭  {email} already exists — skipping")
                continue

            # Create User
            user = User.objects.create_user(
                email=email,
                full_name=agent["full_name"],
                password=PASSWORD,
                account_type=agent["account_type"],
                eula_accepted=True,
                eula_accepted_at=timezone.now(),
            )

            # Update Profile
            profile = user.profile
            profile.display_name = agent["full_name"]
            profile.bio = agent["bio"]
            if agent["skills"]:
                profile.skills = agent["skills"]
            if agent["interests"]:
                profile.interests = agent["interests"]
            if agent["tags"]:
                profile.tags = agent["tags"]
            profile.is_online = True
            profile.save()

            # Create Location
            exact_point = Point(agent["lon"], agent["lat"], srid=4326)
            if profile.should_obfuscate_location:
                obfuscated = UserLocation.generate_obfuscated_point(exact_point)
            else:
                obfuscated = exact_point

            UserLocation.objects.create(
                user=user,
                point=exact_point,
                obfuscated_point=obfuscated,
                source="manual",
            )

            # Create Status
            Status.objects.create(
                user=user,
                status_type=agent["status_type"],
                text=agent["status_text"],
                urgency=agent["urgency"],
                location_snapshot=obfuscated,
            )

            created += 1
            kind = agent["account_type"].upper()
            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✅  {email:<25} {kind:<12} {agent['full_name']}"
                )
            )

        self.stdout.write("")
        self.stdout.write("=" * 55)
        self.stdout.write(
            self.style.SUCCESS(f"Done — {created} test agent(s) created.")
        )
        self.stdout.write("")
        self.stdout.write("  Credentials:")
        self.stdout.write(f"    Password (all):  {PASSWORD}")
        self.stdout.write("    Emails:")
        for a in AGENTS:
            self.stdout.write(f"      {a['email']:<25} ({a['account_type']})")
        self.stdout.write("")
