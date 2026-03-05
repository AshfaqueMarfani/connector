"""
Admin configuration for the matching app.
"""

from django.contrib import admin

from apps.matching.models import AIMatchResult, DataIngestionJob


@admin.register(AIMatchResult)
class AIMatchResultAdmin(admin.ModelAdmin):
    list_display = [
        "id", "status_owner", "matched_user", "score",
        "match_status", "created_at",
    ]
    list_filter = ["match_status", "created_at"]
    search_fields = ["status_owner__email", "matched_user__email", "reason"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]


@admin.register(DataIngestionJob)
class DataIngestionJobAdmin(admin.ModelAdmin):
    list_display = [
        "id", "source_name", "job_status", "total_records",
        "processed_records", "failed_records", "created_at",
    ]
    list_filter = ["job_status", "created_at"]
    readonly_fields = ["id", "created_at", "completed_at"]
    ordering = ["-created_at"]
