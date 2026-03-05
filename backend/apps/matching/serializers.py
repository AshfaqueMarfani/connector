"""
Serializers for AI matching and data ingestion.
"""

from rest_framework import serializers

from apps.matching.models import AIMatchResult, DataIngestionJob


class AIMatchResultSerializer(serializers.ModelSerializer):
    """Serializer for AI match results."""

    status_detail = serializers.SerializerMethodField()
    matched_user_detail = serializers.SerializerMethodField()
    status_owner_detail = serializers.SerializerMethodField()

    class Meta:
        model = AIMatchResult
        fields = [
            "id",
            "score",
            "reason",
            "matched_tags",
            "distance_meters",
            "match_status",
            "created_at",
            "status_detail",
            "matched_user_detail",
            "status_owner_detail",
        ]

    def get_status_detail(self, obj):
        return {
            "id": str(obj.status.id),
            "status_type": obj.status.status_type,
            "text": obj.status.text,
            "urgency": obj.status.urgency,
            "ai_tags": obj.status.ai_tags,
        }

    def get_matched_user_detail(self, obj):
        user = obj.matched_user
        return {
            "id": str(user.id),
            "full_name": user.full_name,
            "account_type": user.account_type,
        }

    def get_status_owner_detail(self, obj):
        user = obj.status_owner
        return {
            "id": str(user.id),
            "full_name": user.full_name,
            "account_type": user.account_type,
        }


class DataIngestionRequestSerializer(serializers.Serializer):
    """Validates incoming data ingestion request."""

    source_name = serializers.CharField(
        max_length=255, required=False, default="API Upload",
    )
    entities = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=1000,
        help_text="List of entity objects to ingest.",
    )

    def validate_entities(self, value):
        """Each entity must have a ``name`` field."""
        for i, entity in enumerate(value):
            if "name" not in entity:
                raise serializers.ValidationError(
                    f"Entity at index {i} missing required field 'name'."
                )
        return value


class DataIngestionJobSerializer(serializers.ModelSerializer):
    """Serializer for data ingestion job records."""

    initiated_by_email = serializers.EmailField(
        source="initiated_by.email", read_only=True, default=None,
    )

    class Meta:
        model = DataIngestionJob
        fields = [
            "id",
            "source_name",
            "job_status",
            "total_records",
            "processed_records",
            "failed_records",
            "error_log",
            "initiated_by_email",
            "created_at",
            "completed_at",
        ]
