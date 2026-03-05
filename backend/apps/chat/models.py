"""
Chat models for Connector.

P2P real-time messaging via Django Channels WebSockets.
Messages are encrypted in transit (WSS/HTTPS) and stored securely.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ChatRoom(models.Model):
    """
    A P2P chat room between two users.

    Created after a connection request is accepted by both parties.
    Exact location sharing is only unlocked inside accepted chat rooms.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="chat_rooms",
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("chat room")
        verbose_name_plural = _("chat rooms")
        ordering = ["-updated_at"]

    def __str__(self):
        emails = ", ".join(
            self.participants.values_list("email", flat=True)[:2]
        )
        return f"ChatRoom({emails})"

    @property
    def last_message(self):
        """Return the most recent message in this room."""
        return self.messages.order_by("-created_at").first()


class Message(models.Model):
    """
    A single chat message within a ChatRoom.

    Every message has a visible "Report" button in the UI
    (App Store UGC compliance).
    """

    class MessageType(models.TextChoices):
        TEXT = "text", _("Text")
        LOCATION = "location", _("Location Share")
        IMAGE = "image", _("Image")
        SYSTEM = "system", _("System Message")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    message_type = models.CharField(
        _("type"),
        max_length=15,
        choices=MessageType.choices,
        default=MessageType.TEXT,
    )
    content = models.TextField(
        _("content"),
        max_length=2000,
    )

    # Read receipt
    is_read = models.BooleanField(
        _("read"),
        default=False,
    )
    read_at = models.DateTimeField(
        _("read at"),
        null=True,
        blank=True,
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _("message")
        verbose_name_plural = _("messages")
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["room", "created_at"],
                name="idx_msg_room_created",
            ),
        ]

    def __str__(self):
        return f"{self.sender.email}: {self.content[:50]}"


class ConnectionRequest(models.Model):
    """
    A request from one user to connect with another.

    Both users must accept before a ChatRoom is created.
    Exact location unlocking only happens inside an accepted connection.
    """

    class RequestStatus(models.TextChoices):
        PENDING = "pending", _("Pending")
        ACCEPTED = "accepted", _("Accepted")
        DECLINED = "declined", _("Declined")
        CANCELLED = "cancelled", _("Cancelled")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="connection_requests_sent",
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="connection_requests_received",
    )
    message = models.TextField(
        _("intro message"),
        max_length=300,
        blank=True,
        default="",
        help_text=_("Optional message sent with the connection request."),
    )
    status = models.CharField(
        _("status"),
        max_length=15,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING,
        db_index=True,
    )
    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="connection_request",
        help_text=_("ChatRoom created when the request is accepted."),
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("connection request")
        verbose_name_plural = _("connection requests")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["from_user", "to_user"],
                name="unique_connection_request",
            ),
            models.CheckConstraint(
                check=~models.Q(from_user=models.F("to_user")),
                name="no_self_connection",
            ),
        ]

    def __str__(self):
        return (
            f"{self.from_user.email} → {self.to_user.email} "
            f"({self.get_status_display()})"
        )

    def accept(self):
        """
        Accept the connection request and create a ChatRoom.
        """
        if self.status != self.RequestStatus.PENDING:
            raise ValueError("Only pending requests can be accepted.")

        # Create the chat room
        room = ChatRoom.objects.create()
        room.participants.add(self.from_user, self.to_user)

        self.status = self.RequestStatus.ACCEPTED
        self.chat_room = room
        self.save(update_fields=["status", "chat_room", "updated_at"])

        # Create a system message
        Message.objects.create(
            room=room,
            sender=self.to_user,
            message_type=Message.MessageType.SYSTEM,
            content="Connection accepted. You can now chat!",
        )

        return room

    def decline(self):
        """Decline the connection request."""
        if self.status != self.RequestStatus.PENDING:
            raise ValueError("Only pending requests can be declined.")
        self.status = self.RequestStatus.DECLINED
        self.save(update_fields=["status", "updated_at"])

    def cancel(self):
        """Cancel the connection request (by the sender)."""
        if self.status != self.RequestStatus.PENDING:
            raise ValueError("Only pending requests can be cancelled.")
        self.status = self.RequestStatus.CANCELLED
        self.save(update_fields=["status", "updated_at"])


class Notification(models.Model):
    """
    In-app notification model.

    Delivered in real-time via WebSocket (NotificationConsumer)
    and persisted for offline retrieval via REST API.
    """

    class NotificationType(models.TextChoices):
        CONNECTION_REQUEST = "connection_request", _("Connection Request")
        CONNECTION_ACCEPTED = "connection_accepted", _("Connection Accepted")
        CONNECTION_DECLINED = "connection_declined", _("Connection Declined")
        NEW_MESSAGE = "new_message", _("New Message")
        AI_MATCH = "ai_match", _("AI Match")
        SYSTEM = "system", _("System")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text=_("The user who receives this notification."),
    )
    notification_type = models.CharField(
        _("type"),
        max_length=25,
        choices=NotificationType.choices,
    )
    title = models.CharField(
        _("title"),
        max_length=200,
    )
    body = models.TextField(
        _("body"),
        max_length=500,
        blank=True,
        default="",
    )
    data = models.JSONField(
        _("extra data"),
        default=dict,
        blank=True,
        help_text=_("JSON payload with IDs, links, etc. for the client."),
    )
    is_read = models.BooleanField(
        _("read"),
        default=False,
    )
    read_at = models.DateTimeField(
        _("read at"),
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _("notification")
        verbose_name_plural = _("notifications")
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "-created_at"],
                name="idx_notif_user_created",
            ),
            models.Index(
                fields=["user", "is_read"],
                name="idx_notif_user_unread",
            ),
        ]

    def __str__(self):
        return f"[{self.get_notification_type_display()}] {self.title} → {self.user.email}"
