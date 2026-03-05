"""
Django admin configuration for the profiles app.
"""

from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        "display_name",
        "user",
        "is_public",
        "is_online",
        "live_tracking_enabled",
        "created_at",
    ]
    list_filter = ["is_public", "is_online", "live_tracking_enabled"]
    search_fields = ["display_name", "user__email", "user__full_name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["user"]
