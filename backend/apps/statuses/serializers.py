"""
Serializers for the statuses app.
"""

from rest_framework import serializers

from apps.accounts.serializers import UserMinimalSerializer

from .models import Status


class StatusCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new status broadcast.
    AI fields (ai_parsed_intent, ai_tags) are populated
    asynchronously by Celery tasks and are read-only here.
    """

    class Meta:
        model = Status
        fields = [
            "id",
            "status_type",
            "text",
            "urgency",
        ]
        read_only_fields = ["id"]

    def validate_text(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Status text must be at least 10 characters."
            )
        return value.strip()


class StatusSerializer(serializers.ModelSerializer):
    """
    Full status serializer for reading status data.
    """

    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Status
        fields = [
            "id",
            "user",
            "status_type",
            "text",
            "urgency",
            "ai_parsed_intent",
            "ai_tags",
            "is_active",
            "expires_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
