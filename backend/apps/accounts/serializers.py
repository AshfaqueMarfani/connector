"""
Serializers for the accounts app.
Handles user registration, login, and profile retrieval.
"""

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Enforces EULA acceptance (App Store compliance).
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
        help_text="Minimum 8 characters.",
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )
    eula_accepted = serializers.BooleanField(required=True)

    class Meta:
        model = User
        fields = [
            "email",
            "full_name",
            "password",
            "password_confirm",
            "account_type",
            "eula_accepted",
        ]

    def validate_eula_accepted(self, value):
        if not value:
            raise serializers.ValidationError("You must accept the End User License Agreement to create an account.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        eula_accepted = validated_data.pop("eula_accepted")

        user = User.objects.create_user(
            password=password,
            **validated_data,
        )

        if eula_accepted:
            user.eula_accepted = True
            user.eula_accepted_at = timezone.now()
            user.save(update_fields=["eula_accepted", "eula_accepted_at"])

        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for user data.
    Used in profile views and explore results.
    """

    account_type_display = serializers.CharField(
        source="get_account_type_display",
        read_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "account_type",
            "account_type_display",
            "is_active",
            "date_joined",
        ]
        read_only_fields = fields


class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal user serializer for embedding in other serializers
    (e.g., chat messages, explore results).
    """

    class Meta:
        model = User
        fields = ["id", "full_name", "account_type"]
        read_only_fields = fields
