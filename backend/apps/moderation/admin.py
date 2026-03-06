"""
Django admin configuration for the moderation app.
This is the MODERATION DASHBOARD required for App Store UGC compliance.
"""

from django.contrib import admin
from django.utils import timezone

from .models import Block, Report


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ["blocker", "blocked", "reason_short", "created_at"]
    search_fields = ["blocker__email", "blocked__email"]
    readonly_fields = ["id", "created_at"]
    raw_id_fields = ["blocker", "blocked"]

    @admin.display(description="Reason")
    def reason_short(self, obj):
        return obj.reason[:80] if obj.reason else "—"


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """
    Moderation dashboard for reviewing UGC reports.

    Moderators can:
      - Filter by status (Pending, Reviewing, Resolved, Dismissed)
      - Review content details and reporter information
      - Add moderator notes
      - Resolve/dismiss reports
      - Suspend offending users directly
    """

    list_display = [
        "id_short",
        "reporter",
        "reported_user",
        "category",
        "content_type",
        "status",
        "created_at",
    ]
    list_filter = ["status", "category", "content_type"]
    search_fields = [
        "reporter__email",
        "reported_user__email",
        "description",
    ]
    readonly_fields = [
        "id",
        "reporter",
        "reported_user",
        "content_type",
        "content_id",
        "category",
        "description",
        "created_at",
        "updated_at",
    ]
    raw_id_fields = ["resolved_by"]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Report Details",
            {
                "fields": (
                    "id",
                    "reporter",
                    "reported_user",
                    "content_type",
                    "content_id",
                    "category",
                    "description",
                    "created_at",
                ),
            },
        ),
        (
            "Moderation",
            {
                "fields": (
                    "status",
                    "moderator_notes",
                    "resolved_by",
                    "resolved_at",
                ),
            },
        ),
    )

    actions = [
        "mark_reviewing",
        "mark_resolved",
        "mark_dismissed",
        "suspend_reported_users",
    ]

    @admin.display(description="Report ID")
    def id_short(self, obj):
        return str(obj.id)[:8]

    @admin.action(description="Mark as Under Review")
    def mark_reviewing(self, request, queryset):
        count = queryset.filter(status="pending").update(status="reviewing")
        self.message_user(request, f"{count} report(s) marked as under review.")

    @admin.action(description="Mark as Resolved")
    def mark_resolved(self, request, queryset):
        count = queryset.exclude(status="resolved").update(
            status="resolved",
            resolved_at=timezone.now(),
            resolved_by=request.user,
        )
        self.message_user(request, f"{count} report(s) resolved.")

    @admin.action(description="Dismiss selected reports")
    def mark_dismissed(self, request, queryset):
        count = queryset.exclude(status="dismissed").update(
            status="dismissed",
            resolved_at=timezone.now(),
            resolved_by=request.user,
        )
        self.message_user(request, f"{count} report(s) dismissed.")

    @admin.action(description="⚠️ Suspend reported users' accounts")
    def suspend_reported_users(self, request, queryset):
        count = 0
        for report in queryset:
            user = report.reported_user
            if not user.is_suspended:
                user.suspend()
                count += 1
                report.status = "resolved"
                report.moderator_notes += (
                    f"\n[AUTO] User suspended by {request.user.email} on " f"{timezone.now().isoformat()}"
                )
                report.resolved_at = timezone.now()
                report.resolved_by = request.user
                report.save()
        self.message_user(request, f"{count} user(s) suspended and report(s) resolved.")
