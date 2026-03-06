"""
WebSocket consumers for real-time chat and presence.

Chat flow:
1. Client connects to ws/v1/chat/<room_id>/?token=<jwt>
2. Server validates JWT + room membership
3. Messages are broadcast to room group in real-time
4. Read receipts and typing indicators are supported
5. Location sharing (exact coords) is allowed only in accepted connections
"""

import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from .models import ChatRoom, Message

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for P2P chat within an accepted ChatRoom.

    Supports message types:
    - chat.message: Send/receive text messages
    - chat.typing: Typing indicator
    - chat.read: Mark messages as read
    - chat.location: Share exact location (only in connected rooms)
    - chat.system: System broadcasts
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_id = None
        self.room_group_name = None
        self.user = None

    async def connect(self):
        """Authenticate user and join the chat room group."""
        self.user = self.scope.get("user", AnonymousUser())
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"

        # Reject unauthenticated connections
        if isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            logger.warning(f"WebSocket rejected – unauthenticated user for room {self.room_id}")
            await self.close(code=4001)
            return

        # Verify the user is a participant of this room
        is_member = await self._is_room_member()
        if not is_member:
            logger.warning(f"WebSocket rejected – user {self.user.email} not in room {self.room_id}")
            await self.close(code=4003)
            return

        # Join the room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        # Update presence
        await self._set_online(True)

        # Notify room that user is online
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user.presence",
                "user_id": str(self.user.id),
                "is_online": True,
            },
        )

        logger.info(f"WebSocket connected: user={self.user.email} room={self.room_id}")

    async def disconnect(self, close_code):
        """Leave the chat room group and update presence."""
        if self.room_group_name:
            # Notify room that user went offline
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user.presence",
                    "user_id": str(self.user.id),
                    "is_online": False,
                },
            )

            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        if self.user and self.user.is_authenticated:
            await self._set_online(False)

        logger.info(
            f"WebSocket disconnected: user={getattr(self.user, 'email', '?')} " f"room={self.room_id} code={close_code}"
        )

    async def receive_json(self, content, **kwargs):
        """
        Handle incoming WebSocket messages.

        Expected format:
        {
            "type": "chat.message" | "chat.typing" | "chat.read" | "chat.location",
            "content": "...",        # for chat.message
            "message_id": "...",     # for chat.read
            "latitude": ...,         # for chat.location
            "longitude": ...,        # for chat.location
        }
        """
        msg_type = content.get("type", "")

        if msg_type == "chat.message":
            await self._handle_message(content)
        elif msg_type == "chat.typing":
            await self._handle_typing(content)
        elif msg_type == "chat.read":
            await self._handle_read_receipt(content)
        elif msg_type == "chat.location":
            await self._handle_location_share(content)
        else:
            await self.send_json({"type": "error", "message": f"Unknown message type: {msg_type}"})

    # ── Message handlers ────────────────────────────────────────────

    async def _handle_message(self, content):
        """Persist a text message and broadcast to the room."""
        text = content.get("content", "").strip()
        if not text:
            await self.send_json({"type": "error", "message": "Empty message."})
            return

        if len(text) > 2000:
            await self.send_json({"type": "error", "message": "Message too long (max 2000 chars)."})
            return

        # Persist to database
        message = await self._save_message(message_type=Message.MessageType.TEXT, content=text)

        # Broadcast to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "message_id": str(message.id),
                "sender_id": str(self.user.id),
                "sender_name": self.user.full_name,
                "content": text,
                "message_type": "text",
                "timestamp": message.created_at.isoformat(),
            },
        )

    async def _handle_typing(self, content):
        """Broadcast typing indicator to other participants."""
        is_typing = content.get("is_typing", True)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.typing",
                "user_id": str(self.user.id),
                "user_name": self.user.full_name,
                "is_typing": is_typing,
            },
        )

    async def _handle_read_receipt(self, content):
        """Mark messages as read and notify sender."""
        message_id = content.get("message_id")
        if not message_id:
            return

        updated = await self._mark_message_read(message_id)
        if updated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.read",
                    "message_id": message_id,
                    "reader_id": str(self.user.id),
                    "read_at": timezone.now().isoformat(),
                },
            )

    async def _handle_location_share(self, content):
        """
        Share exact location with chat partner.

        Per LOCATION_AND_PRIVACY_TOS: Exact location is ONLY unlocked
        and shared in the P2P chat after a connection request is
        explicitly accepted by both parties.
        """
        latitude = content.get("latitude")
        longitude = content.get("longitude")

        if latitude is None or longitude is None:
            await self.send_json({"type": "error", "message": "latitude and longitude required."})
            return

        try:
            latitude = float(latitude)
            longitude = float(longitude)
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                raise ValueError("Coordinates out of range")
        except (TypeError, ValueError):
            await self.send_json({"type": "error", "message": "Invalid coordinates."})
            return

        # Save as location message
        location_content = json.dumps({"latitude": latitude, "longitude": longitude})
        message = await self._save_message(
            message_type=Message.MessageType.LOCATION,
            content=location_content,
        )

        # Broadcast to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.location",
                "message_id": str(message.id),
                "sender_id": str(self.user.id),
                "sender_name": self.user.full_name,
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": message.created_at.isoformat(),
            },
        )

    # ── Group event handlers (called by channel_layer.group_send) ───

    async def chat_message(self, event):
        """Send chat message to the WebSocket client."""
        # Don't echo back to the sender (client already has optimistic UI)
        # Actually, we do send to all — the client can filter by sender_id
        await self.send_json(event)

    async def chat_typing(self, event):
        """Send typing indicator to the WebSocket client."""
        # Don't send typing indicator back to the typer
        if event.get("user_id") != str(self.user.id):
            await self.send_json(event)

    async def chat_read(self, event):
        """Send read receipt to the WebSocket client."""
        await self.send_json(event)

    async def chat_location(self, event):
        """Send location share to the WebSocket client."""
        await self.send_json(event)

    async def user_presence(self, event):
        """Send presence update to the WebSocket client."""
        if event.get("user_id") != str(self.user.id):
            await self.send_json(event)

    async def chat_system(self, event):
        """Send system message to the WebSocket client."""
        await self.send_json(event)

    # ── Database helpers (sync_to_async) ────────────────────────────

    @database_sync_to_async
    def _is_room_member(self):
        """Check if the current user is a participant of the chat room."""
        try:
            room = ChatRoom.objects.get(id=self.room_id, is_active=True)
            return room.participants.filter(id=self.user.id).exists()
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def _save_message(self, message_type, content):
        """Persist a message to the database."""
        return Message.objects.create(
            room_id=self.room_id,
            sender=self.user,
            message_type=message_type,
            content=content,
        )

    @database_sync_to_async
    def _mark_message_read(self, message_id):
        """Mark a message as read (only if the reader is not the sender)."""
        try:
            msg = Message.objects.get(
                id=message_id,
                room_id=self.room_id,
                is_read=False,
            )
            # Only the recipient can mark a message as read
            if msg.sender_id != self.user.id:
                msg.is_read = True
                msg.read_at = timezone.now()
                msg.save(update_fields=["is_read", "read_at"])
                return True
            return False
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def _set_online(self, online):
        """Update user's online status in their profile."""
        try:
            profile = self.user.profile
            profile.is_online = online
            if not online:
                profile.last_seen = timezone.now()
            profile.save(update_fields=["is_online", "last_seen"])
        except Exception:
            pass


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for user-specific notifications.

    Each authenticated user connects to their own notification channel
    to receive real-time alerts for:
    - New connection requests
    - Connection request accepted/declined
    - New messages (when not in the chat room)
    - AI matching alerts
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.notification_group = None

    async def connect(self):
        """Authenticate and join user-specific notification group."""
        self.user = self.scope.get("user", AnonymousUser())

        if isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.notification_group = f"notifications_{self.user.id}"

        await self.channel_layer.group_add(self.notification_group, self.channel_name)
        await self.accept()

        logger.info(f"Notification WS connected: user={self.user.email}")

    async def disconnect(self, close_code):
        """Leave the notification group."""
        if self.notification_group:
            await self.channel_layer.group_discard(self.notification_group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        """
        Handle incoming notification actions (e.g., mark as read).
        """
        action = content.get("action")

        if action == "mark_read":
            notif_id = content.get("notification_id")
            if notif_id:
                await self._mark_notification_read(notif_id)

    # ── Group event handlers ────────────────────────────────────────

    async def notification_new(self, event):
        """Push a new notification to the WebSocket client."""
        await self.send_json(event)

    async def notification_connection_request(self, event):
        """Push connection request notification."""
        await self.send_json(event)

    async def notification_connection_accepted(self, event):
        """Push connection accepted notification."""
        await self.send_json(event)

    async def notification_message(self, event):
        """Push new message notification."""
        await self.send_json(event)

    # ── Database helpers ────────────────────────────────────────────

    @database_sync_to_async
    def _mark_notification_read(self, notification_id):
        """Mark a notification as read."""
        from apps.chat.models import Notification

        try:
            notif = Notification.objects.get(id=notification_id, user=self.user, is_read=False)
            notif.is_read = True
            notif.read_at = timezone.now()
            notif.save(update_fields=["is_read", "read_at"])
        except Notification.DoesNotExist:
            pass
