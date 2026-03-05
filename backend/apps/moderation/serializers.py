"""
Serializers for the moderation app.
Handles Block and Report creation/retrieval.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Block, Report

User = get_user_model()


class BlockCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a block.
    The `blocker` is always the authenticated user (set in the view).
    """

    blocked = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        help_text="UUID of the user to block.",
    )

    class Meta:
        model = Block
        fields = ["blocked", "reason"]

    def validate_blocked(self, value):
        request = self.context.get("request")
        if request and value == request.user:
            raise serializers.ValidationError("You cannot block yourself.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        if request and Block.objects.filter(
            blocker=request.user, blocked=attrs["blocked"]
        ).exists():
            raise serializers.ValidationError(
                {"blocked": "You have already blocked this user."}
            )
        return attrs


class BlockSerializer(serializers.ModelSerializer):
    """Read serializer for blocks."""

    blocked_email = serializers.CharField(source="blocked.email", read_only=True)
    blocked_name = serializers.CharField(source="blocked.full_name", read_only=True)

    class Meta:
        model = Block
        fields = [
            "id",
            "blocked",
            "blocked_email",
            "blocked_name",
            "reason",
            "created_at",
        ]
        read_only_fields = fields


class ReportCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for filing a report.
    The `reporter` is always the authenticated user (set in the view).
    """

    reported_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        help_text="UUID of the user being reported.",
    )

    class Meta:
        model = Report
        fields = [
            "reported_user",
            "content_type",
            "content_id",
            "category",
            "description",
        ]

    def validate_reported_user(self, value):
        request = self.context.get("request")
        if request and value == request.user:
            raise serializers.ValidationError("You cannot report yourself.")
        return value


class ReportSerializer(serializers.ModelSerializer):
    """Read serializer for reports (user-facing — limited fields)."""

    class Meta:
        model = Report
        fields = [
            "id",
            "reported_user",
            "content_type",
            "category",
            "status",
            "created_at",
        ]
        read_only_fields = fields


class ReportAdminSerializer(serializers.ModelSerializer):
    """
    Full report serializer for the admin moderation dashboard.
    Includes moderator notes and resolution data.
    """

    reporter_email = serializers.CharField(source="reporter.email", read_only=True)
    reported_user_email = serializers.CharField(
        source="reported_user.email", read_only=True
    )

    class Meta:
        model = Report
        fields = [
            "id",
            "reporter",
            "reporter_email",
            "reported_user",
            "reported_user_email",
            "content_type",
            "content_id",
            "category",
            "description",
            "status",
            "moderator_notes",
            "resolved_at",
            "resolved_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "reporter",
            "reporter_email",
            "reported_user",
            "reported_user_email",
            "content_type",
            "content_id",
            "category",
            "description",
            "created_at",
            "updated_at",
        ]
