"""
Custom User model for Connector.

Uses email as the primary authentication field instead of username.
Supports account types: INDIVIDUAL, BUSINESS, NGO.
"""

import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model.

    - Email is the unique identifier for authentication.
    - Account type determines privacy defaults and map rendering behavior.
    - EULA acceptance is mandatory (App Store compliance).
    """

    class AccountType(models.TextChoices):
        INDIVIDUAL = "individual", _("Individual")
        BUSINESS = "business", _("Business")
        NGO = "ngo", _("NGO / Non-Profit")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for the user."),
    )
    email = models.EmailField(
        _("email address"),
        unique=True,
        db_index=True,
        error_messages={
            "unique": _("A user with that email already exists."),
        },
    )
    full_name = models.CharField(
        _("full name"),
        max_length=255,
        blank=True,
    )
    account_type = models.CharField(
        _("account type"),
        max_length=20,
        choices=AccountType.choices,
        default=AccountType.INDIVIDUAL,
        db_index=True,
        help_text=_(
            "Determines privacy defaults: Individuals are private by default; "
            "Businesses and NGOs are public by default."
        ),
    )

    # EULA / TOS acceptance – mandatory for App Store compliance
    eula_accepted = models.BooleanField(
        _("EULA accepted"),
        default=False,
        help_text=_("User must accept EULA before using the platform."),
    )
    eula_accepted_at = models.DateTimeField(
        _("EULA accepted at"),
        null=True,
        blank=True,
    )

    # Account status flags
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. " "Unselect this instead of deleting accounts."
        ),
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into the admin site."),
    )
    is_suspended = models.BooleanField(
        _("suspended"),
        default=False,
        help_text=_("Suspended users cannot log in or interact with the platform. " "Set by moderation actions."),
    )

    # Timestamps
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    updated_at = models.DateTimeField(_("last updated"), auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["email"], name="idx_user_email"),
            models.Index(fields=["account_type"], name="idx_user_account_type"),
            models.Index(fields=["is_active", "is_suspended"], name="idx_user_status"),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    @property
    def is_public_entity(self) -> bool:
        """Businesses and NGOs are rendered with exact GPS on the public map."""
        return self.account_type in (
            self.AccountType.BUSINESS,
            self.AccountType.NGO,
        )

    def accept_eula(self):
        """Record EULA acceptance with a timestamp."""
        self.eula_accepted = True
        self.eula_accepted_at = timezone.now()
        self.save(update_fields=["eula_accepted", "eula_accepted_at"])

    def suspend(self, reason: str = ""):
        """Suspend the user account (moderation action)."""
        self.is_suspended = True
        self.is_active = False
        self.save(update_fields=["is_suspended", "is_active"])
