"""
Django admin configuration for the statuses app.
"""

from django.contrib import admin

from .models import Status


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = [
        "short_text",
        "user",
        "status_type",
        "urgency",
        "is_active",
        "created_at",
    ]
    list_filter = ["status_type", "urgency", "is_active"]
    search_fields = ["text", "user__email"]
    readonly_fields = ["id", "ai_parsed_intent", "ai_tags", "created_at", "updated_at"]
    raw_id_fields = ["user"]
    date_hierarchy = "created_at"

    actions = ["deactivate_statuses"]

    @admin.display(description="Status Text")
    def short_text(self, obj):
        return obj.text[:80] if obj.text else ""

    @admin.action(description="Deactivate selected statuses")
    def deactivate_statuses(self, request, queryset):
        count = queryset.filter(is_active=True).update(is_active=False)
        self.message_user(request, f"{count} status(es) deactivated.")
