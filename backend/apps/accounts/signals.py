"""
Signals for the accounts app.

Automatically creates a Profile instance when a new User is created.
"""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """
    When a new User is created, automatically generate a linked Profile.
    Privacy defaults depend on account type:
      - Individuals → private by default
      - Businesses/NGOs → public by default
    """
    if created:
        from apps.profiles.models import Profile

        is_public = instance.is_public_entity
        Profile.objects.create(
            user=instance,
            display_name=instance.full_name or instance.email.split("@")[0],
            is_public=is_public,
        )
