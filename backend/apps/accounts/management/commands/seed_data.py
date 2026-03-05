"""
Management command to seed the database with sample data for development.

Creates test users (individuals, businesses, NGOs) with profiles,
locations, and statuses to solve the "cold start" problem during dev.
"""

import random

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.locations.models import UserLocation
from apps.statuses.models import Status


class Command(BaseCommand):
    help = "Seed the database with sample users, profiles, locations, and statuses."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=20,
            help="Number of seed users to create (default: 20)",
        )
        parser.add_argument(
            "--city",
            type=str,
            default="karachi",
            choices=["karachi", "nyc", "london"],
            help="City center for seed locations (default: karachi)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing seed data before creating new data.",
        )

    def handle(self, *args, **options):
        count = options["count"]
        city = options["city"]
        clear = options["clear"]

        # City center coordinates (lat, lon)
        city_centers = {
            "karachi": (24.8607, 67.0011),
            "nyc": (40.7128, -74.0060),
            "london": (51.5074, -0.1278),
        }
        center_lat, center_lon = city_centers[city]

        if clear:
            self.stdout.write(self.style.WARNING("Clearing existing seed data..."))
            User.objects.filter(email__endswith="@seed.connector.dev").delete()
            self.stdout.write(self.style.SUCCESS("Seed data cleared."))

        self.stdout.write(
            f"Seeding {count} users around {city.title()} "
            f"({center_lat}, {center_lon})..."
        )

        # Sample data pools
        individual_skills = [
            "plumbing", "electrician", "tutoring", "cooking",
            "carpentry", "driving", "translation", "first aid",
            "photography", "web design", "tailoring", "gardening",
        ]
        ngo_tags = [
            "food", "shelter", "medical", "education", "legal aid",
            "clothing", "counseling", "disaster relief",
        ]
        business_tags = [
            "restaurant", "hardware store", "pharmacy", "grocery",
            "clinic", "salon", "auto repair", "laundry",
        ]
        needs = [
            "Need emergency food assistance for family of 4",
            "Looking for affordable plumbing service nearby",
            "Need tutoring for 10th grade mathematics",
            "Seeking free legal consultation for tenant dispute",
            "Looking for someone to help move furniture today",
            "Need first aid training for community center",
            "Looking for affordable tailoring service",
            "Need translation help (Urdu to English) for documents",
        ]
        offers = [
            "Offering free tutoring in science and math",
            "Free food distribution every Friday at 2pm",
            "Discounted electrical repair services this week",
            "Offering free legal aid clinic on Saturdays",
            "Volunteer drivers available for medical appointments",
            "Free community cooking class this weekend",
            "Offering photography services at reduced rates",
            "Free gardening workshop — learn to grow your own food",
        ]

        created_count = 0

        for i in range(count):
            # Distribute: 50% individual, 25% business, 25% NGO
            if i % 4 == 0:
                account_type = "business"
            elif i % 4 == 1:
                account_type = "ngo"
            else:
                account_type = "individual"

            email = f"seed_{account_type}_{i:03d}@seed.connector.dev"

            # Skip if already exists
            if User.objects.filter(email=email).exists():
                self.stdout.write(f"  Skipping {email} (already exists)")
                continue

            # Create user
            try:
                user = User.objects.create_user(
                    email=email,
                    full_name=f"Seed {account_type.title()} {i:03d}",
                    password="SeedPassword123!",
                    account_type=account_type,
                    eula_accepted=True,
                    eula_accepted_at=timezone.now(),
                )

                # Update profile
                profile = user.profile
                if account_type == "individual":
                    profile.skills = random.sample(
                        individual_skills, k=random.randint(1, 4)
                    )
                    profile.interests = random.sample(ngo_tags, k=random.randint(1, 3))
                elif account_type == "business":
                    profile.tags = random.sample(business_tags, k=random.randint(1, 3))
                    profile.bio = f"Local {random.choice(business_tags)} serving the community."
                else:  # ngo
                    profile.tags = random.sample(ngo_tags, k=random.randint(2, 4))
                    profile.bio = f"NGO providing {', '.join(profile.tags)} services."

                profile.is_online = random.choice([True, False])
                profile.save()

                # Create location (random offset within ~2km of city center)
                lat_offset = random.uniform(-0.018, 0.018)  # ~2km
                lon_offset = random.uniform(-0.018, 0.018)
                lat = center_lat + lat_offset
                lon = center_lon + lon_offset
                exact_point = Point(lon, lat, srid=4326)

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

                # Create a random status for 60% of users
                if random.random() < 0.6:
                    if random.choice([True, False]):
                        text = random.choice(needs)
                        status_type = "need"
                    else:
                        text = random.choice(offers)
                        status_type = "offer"

                    Status.objects.create(
                        user=user,
                        status_type=status_type,
                        text=text,
                        urgency=random.choice(["low", "medium", "high"]),
                        location_snapshot=obfuscated,
                    )

                created_count += 1
                self.stdout.write(f"  Created: {email} ({account_type})")

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  Failed to create {email}: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! Created {created_count} seed users around {city.title()}."
            )
        )
