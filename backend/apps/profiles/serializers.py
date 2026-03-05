"""
Serializers for the profiles app.
"""

from rest_framework import serializers

from apps.accounts.serializers import UserMinimalSerializer

from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    """
    Full profile serializer for the profile owner (read/write).
    """

    user = UserMinimalSerializer(read_only=True)
    should_obfuscate_location = serializers.BooleanField(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "display_name",
            "bio",
            "avatar",
            "skills",
            "interests",
            "tags",
            "is_public",
            "live_tracking_enabled",
            "is_online",
            "last_seen",
            "should_obfuscate_location",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "is_online",
            "last_seen",
            "should_obfuscate_location",
            "created_at",
            "updated_at",
        ]

    def validate_skills(self, value):
        if len(value) > 20:
            raise serializers.ValidationError("Maximum 20 skills allowed.")
        return [skill.strip().lower() for skill in value if skill.strip()]

    def validate_interests(self, value):
        if len(value) > 20:
            raise serializers.ValidationError("Maximum 20 interests allowed.")
        return [interest.strip().lower() for interest in value if interest.strip()]

    def validate_tags(self, value):
        if len(value) > 30:
            raise serializers.ValidationError("Maximum 30 tags allowed.")
        return [tag.strip().lower() for tag in value if tag.strip()]


class ProfilePublicSerializer(serializers.ModelSerializer):
    """
    Public-facing profile serializer for explore/nearby results.
    Excludes sensitive fields.
    """

    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "display_name",
            "bio",
            "avatar",
            "skills",
            "interests",
            "tags",
            "is_public",
            "is_online",
        ]
        read_only_fields = fields
