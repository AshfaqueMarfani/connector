"""
Management command to bulk-ingest public entity data (businesses, NGOs)
from external datasets.

Supports JSON input for mapping third-party scraped data to
Public Profile records with exact PostGIS locations.
"""

import json

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.accounts.models import User
from apps.locations.models import UserLocation


class Command(BaseCommand):
    help = (
        "Ingest external entity data (businesses/NGOs) from a JSON file "
        "and create Public Profiles with PostGIS locations."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "json_file",
            type=str,
            help="Path to the JSON file containing entity data.",
        )
        parser.add_argument(
            "--account-type",
            type=str,
            default="business",
            choices=["business", "ngo"],
            help="Account type for ingested entities (default: business).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and validate without writing to the database.",
        )

    def handle(self, *args, **options):
        json_file = options["json_file"]
        account_type = options["account_type"]
        dry_run = options["dry_run"]

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                entities = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"File not found: {json_file}")
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON: {e}")

        if not isinstance(entities, list):
            raise CommandError("JSON file must contain a top-level array of objects.")

        self.stdout.write(f"Found {len(entities)} entities in {json_file} " f"(type={account_type}, dry_run={dry_run})")

        """
        Expected JSON format per entity:
        {
            "name": "Al-Khidmat Foundation",
            "email": "info@alkhidmat.org",  (optional, auto-generated if missing)
            "bio": "Providing food and shelter services.",
            "tags": ["food", "shelter"],
            "latitude": 24.8607,
            "longitude": 67.0011,
            "phone": "+923001234567"  (optional)
        }
        """

        created = 0
        skipped = 0
        errors = 0

        for idx, entity in enumerate(entities):
            try:
                name = entity.get("name", "").strip()
                if not name:
                    self.stdout.write(self.style.WARNING(f"  [{idx}] Skipping: missing 'name'"))
                    skipped += 1
                    continue

                lat = entity.get("latitude")
                lon = entity.get("longitude")
                if lat is None or lon is None:
                    self.stdout.write(self.style.WARNING(f"  [{idx}] Skipping '{name}': missing coordinates"))
                    skipped += 1
                    continue

                # Validate coordinate ranges
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    self.stdout.write(
                        self.style.WARNING(f"  [{idx}] Skipping '{name}': invalid coordinates " f"({lat}, {lon})")
                    )
                    skipped += 1
                    continue

                # Generate email if not provided
                email = entity.get("email", "").strip()
                if not email:
                    slug = name.lower().replace(" ", "_")[:30]
                    email = f"ingested_{slug}_{idx}@entities.connector.dev"

                if dry_run:
                    self.stdout.write(f"  [DRY RUN] Would create: {name} ({email}) at " f"({lat}, {lon})")
                    created += 1
                    continue

                # Skip if email already exists
                if User.objects.filter(email=email).exists():
                    self.stdout.write(f"  [{idx}] Skipping '{name}': email exists")
                    skipped += 1
                    continue

                # Create user
                user = User.objects.create_user(
                    email=email,
                    full_name=name,
                    password=None,  # No password — these are system-created entities
                    account_type=account_type,
                    eula_accepted=True,
                    eula_accepted_at=timezone.now(),
                )
                # Ensure they can't log in with password
                user.set_unusable_password()
                user.save(update_fields=["password"])

                # Update profile
                profile = user.profile
                profile.display_name = name
                profile.bio = entity.get("bio", "")[:500]
                profile.tags = entity.get("tags", [])
                profile.save()

                # Create location (public entity → exact coordinates, no obfuscation)
                exact_point = Point(lon, lat, srid=4326)
                UserLocation.objects.create(
                    user=user,
                    point=exact_point,
                    obfuscated_point=exact_point,  # Public = no obfuscation
                    source="manual",
                )

                created += 1
                self.stdout.write(f"  Created: {name} ({email})")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  [{idx}] Error processing entity: {e}"))
                errors += 1

        self.stdout.write(
            self.style.SUCCESS(f"\nIngestion complete: {created} created, " f"{skipped} skipped, {errors} errors.")
        )
