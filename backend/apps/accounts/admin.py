"""
Django admin configuration for the accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for the User model with email-based authentication."""

    list_display = [
        "email",
        "full_name",
        "account_type",
        "is_active",
        "is_suspended",
        "eula_accepted",
        "date_joined",
    ]
    list_filter = [
        "account_type",
        "is_active",
        "is_suspended",
        "is_staff",
        "eula_accepted",
    ]
    search_fields = ["email", "full_name"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {"fields": ("full_name", "account_type")},
        ),
        (
            _("EULA / Compliance"),
            {"fields": ("eula_accepted", "eula_accepted_at")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_suspended",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            _("Important dates"),
            {"fields": ("last_login", "date_joined")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "full_name",
                    "account_type",
                    "password1",
                    "password2",
                    "eula_accepted",
                ),
            },
        ),
    )

    readonly_fields = ["date_joined", "eula_accepted_at"]

    actions = ["suspend_users", "unsuspend_users"]

    @admin.action(description="Suspend selected users")
    def suspend_users(self, request, queryset):
        count = 0
        for user in queryset:
            if not user.is_suspended:
                user.suspend()
                count += 1
        self.message_user(request, f"{count} user(s) suspended.")

    @admin.action(description="Unsuspend selected users")
    def unsuspend_users(self, request, queryset):
        count = queryset.filter(is_suspended=True).update(
            is_suspended=False, is_active=True
        )
        self.message_user(request, f"{count} user(s) unsuspended.")
