"""
Serializers for the chat app.
"""

from rest_framework import serializers

from apps.accounts.serializers import UserMinimalSerializer

from .models import ChatRoom, ConnectionRequest, Message, Notification


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages."""

    sender = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "room",
            "sender",
            "message_type",
            "content",
            "is_read",
            "read_at",
            "created_at",
        ]
        read_only_fields = ["id", "room", "sender", "is_read", "read_at", "created_at"]


class MessageCreateSerializer(serializers.Serializer):
    """Serializer for sending a message via REST API."""

    content = serializers.CharField(max_length=2000)
    message_type = serializers.ChoiceField(
        choices=Message.MessageType.choices,
        default=Message.MessageType.TEXT,
        required=False,
    )


class ChatRoomSerializer(serializers.ModelSerializer):
    """Serializer for chat rooms."""

    participants = UserMinimalSerializer(many=True, read_only=True)
    last_message = MessageSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            "id",
            "participants",
            "is_active",
            "last_message",
            "unread_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_unread_count(self, obj):
        """Count of unread messages for the requesting user."""
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0


class ConnectionRequestCreateSerializer(serializers.Serializer):
    """Serializer for creating a connection request."""

    to_user = serializers.UUIDField(help_text="UUID of the user to connect with.")
    message = serializers.CharField(
        max_length=300,
        required=False,
        default="",
        allow_blank=True,
    )


class ConnectionRequestSerializer(serializers.ModelSerializer):
    """Serializer for reading connection requests."""

    from_user = UserMinimalSerializer(read_only=True)
    to_user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = ConnectionRequest
        fields = [
            "id",
            "from_user",
            "to_user",
            "message",
            "status",
            "chat_room",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications."""

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "body",
            "data",
            "is_read",
            "read_at",
            "created_at",
        ]
        read_only_fields = fields
