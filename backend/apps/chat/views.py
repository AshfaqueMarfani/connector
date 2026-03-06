"""
REST API views for the chat app.

Provides endpoints for:
- Connection requests (send, accept, decline, cancel, list)
- Chat rooms (list, detail)
- Messages (list within room, send via REST fallback)
- Notifications (list, mark read, mark all read)
"""

import logging

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.accounts.models import User
from apps.moderation.models import Block

from .models import ChatRoom, ConnectionRequest, Message, Notification
from .serializers import (
    ChatRoomSerializer,
    ConnectionRequestCreateSerializer,
    ConnectionRequestSerializer,
    MessageCreateSerializer,
    MessageSerializer,
    NotificationSerializer,
)
from .utils import send_realtime_notification

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# CONNECTION REQUESTS
# ═══════════════════════════════════════════════════════════════════════


class ConnectionRequestCreateView(APIView):
    """
    POST /api/v1/chat/connections/request/
    Send a connection request to another user.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ConnectionRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        to_user_id = serializer.validated_data["to_user"]

        # Validate target user exists
        try:
            to_user = User.objects.get(id=to_user_id, is_active=True)
        except User.DoesNotExist:
            return Response(
                {"success": False, "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Cannot connect to self
        if to_user == request.user:
            return Response(
                {"success": False, "message": "Cannot send connection request to yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if blocked (either direction)
        is_blocked = Block.objects.filter(
            Q(blocker=request.user, blocked=to_user) | Q(blocker=to_user, blocked=request.user)
        ).exists()
        if is_blocked:
            return Response(
                {"success": False, "message": "Cannot connect with this user."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check for existing pending request (either direction)
        existing = ConnectionRequest.objects.filter(
            Q(from_user=request.user, to_user=to_user) | Q(from_user=to_user, to_user=request.user),
            status=ConnectionRequest.RequestStatus.PENDING,
        ).first()
        if existing:
            return Response(
                {"success": False, "message": "A pending connection request already exists."},
                status=status.HTTP_409_CONFLICT,
            )

        # Check for existing accepted connection (already have a chat room)
        already_connected = ConnectionRequest.objects.filter(
            Q(from_user=request.user, to_user=to_user) | Q(from_user=to_user, to_user=request.user),
            status=ConnectionRequest.RequestStatus.ACCEPTED,
        ).exists()
        if already_connected:
            return Response(
                {"success": False, "message": "You are already connected with this user."},
                status=status.HTTP_409_CONFLICT,
            )

        # Create connection request
        conn_request = ConnectionRequest.objects.create(
            from_user=request.user,
            to_user=to_user,
            message=serializer.validated_data.get("message", ""),
        )

        # Create notification for the recipient
        notification = Notification.objects.create(
            user=to_user,
            notification_type=Notification.NotificationType.CONNECTION_REQUEST,
            title=f"{request.user.full_name} wants to connect",
            body=conn_request.message or "You have a new connection request.",
            data={
                "connection_request_id": str(conn_request.id),
                "from_user_id": str(request.user.id),
                "from_user_name": request.user.full_name,
            },
        )

        # Push real-time notification
        send_realtime_notification(to_user.id, notification)

        logger.info(f"Connection request sent: {request.user.email} → {to_user.email}")

        return Response(
            {
                "success": True,
                "message": "Connection request sent.",
                "data": ConnectionRequestSerializer(conn_request).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ConnectionRequestRespondView(APIView):
    """
    POST /api/v1/chat/connections/<uuid:pk>/accept/
    POST /api/v1/chat/connections/<uuid:pk>/decline/
    POST /api/v1/chat/connections/<uuid:pk>/cancel/

    Respond to a connection request.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, action):
        conn_request = get_object_or_404(ConnectionRequest, pk=pk)

        # Validate permissions
        if action in ("accept", "decline"):
            if conn_request.to_user != request.user:
                return Response(
                    {"success": False, "message": "Only the recipient can respond."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        elif action == "cancel":
            if conn_request.from_user != request.user:
                return Response(
                    {"success": False, "message": "Only the sender can cancel."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            return Response(
                {"success": False, "message": "Invalid action."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Execute the action
        try:
            if action == "accept":
                room = conn_request.accept()
                # Notify the requester
                notification = Notification.objects.create(
                    user=conn_request.from_user,
                    notification_type=Notification.NotificationType.CONNECTION_ACCEPTED,
                    title=f"{request.user.full_name} accepted your request",
                    body="You can now chat!",
                    data={
                        "connection_request_id": str(conn_request.id),
                        "chat_room_id": str(room.id),
                        "user_id": str(request.user.id),
                        "user_name": request.user.full_name,
                    },
                )
                send_realtime_notification(conn_request.from_user.id, notification)
                message = "Connection accepted. Chat room created."

            elif action == "decline":
                conn_request.decline()
                # Notify the requester
                notification = Notification.objects.create(
                    user=conn_request.from_user,
                    notification_type=Notification.NotificationType.CONNECTION_DECLINED,
                    title=f"{request.user.full_name} declined your request",
                    body="",
                    data={
                        "connection_request_id": str(conn_request.id),
                        "user_id": str(request.user.id),
                    },
                )
                send_realtime_notification(conn_request.from_user.id, notification)
                message = "Connection request declined."

            elif action == "cancel":
                conn_request.cancel()
                message = "Connection request cancelled."

        except ValueError as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(f"Connection {action}: {conn_request.from_user.email} → " f"{conn_request.to_user.email}")

        return Response(
            {
                "success": True,
                "message": message,
                "data": ConnectionRequestSerializer(conn_request).data,
            },
            status=status.HTTP_200_OK,
        )


class ConnectionRequestListView(generics.ListAPIView):
    """
    GET /api/v1/chat/connections/
    List all connection requests (sent and received).

    Query params:
    - direction: "sent" | "received" | "all" (default: "all")
    - status: "pending" | "accepted" | "declined" | "cancelled"
    """

    serializer_class = ConnectionRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        direction = self.request.query_params.get("direction", "all")
        req_status = self.request.query_params.get("status")

        if direction == "sent":
            qs = ConnectionRequest.objects.filter(from_user=user)
        elif direction == "received":
            qs = ConnectionRequest.objects.filter(to_user=user)
        else:
            qs = ConnectionRequest.objects.filter(Q(from_user=user) | Q(to_user=user))

        if req_status:
            qs = qs.filter(status=req_status)

        return qs.select_related("from_user", "to_user")


# ═══════════════════════════════════════════════════════════════════════
# CHAT ROOMS
# ═══════════════════════════════════════════════════════════════════════


class ChatRoomListView(generics.ListAPIView):
    """
    GET /api/v1/chat/rooms/
    List all chat rooms the authenticated user belongs to.
    """

    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            ChatRoom.objects.filter(participants=self.request.user, is_active=True)
            .prefetch_related("participants")
            .order_by("-updated_at")
        )


class ChatRoomDetailView(APIView):
    """
    GET /api/v1/chat/rooms/<uuid:room_id>/
    Get details of a specific chat room (must be a participant).
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, room_id):
        room = get_object_or_404(ChatRoom, id=room_id, is_active=True)
        if not room.participants.filter(id=request.user.id).exists():
            return Response(
                {"success": False, "message": "Not a participant."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(ChatRoomSerializer(room).data)


# ═══════════════════════════════════════════════════════════════════════
# MESSAGES
# ═══════════════════════════════════════════════════════════════════════


class MessageListView(generics.ListAPIView):
    """
    GET /api/v1/chat/rooms/<uuid:room_id>/messages/
    List messages in a chat room (paginated, newest last).
    Must be a participant.
    """

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        room_id = self.kwargs["room_id"]
        room = get_object_or_404(ChatRoom, id=room_id, is_active=True)

        if not room.participants.filter(id=self.request.user.id).exists():
            return Message.objects.none()

        return Message.objects.filter(room=room).select_related("sender").order_by("created_at")


class MessageCreateView(APIView):
    """
    POST /api/v1/chat/rooms/<uuid:room_id>/messages/
    Send a message via REST API (fallback for when WebSocket is unavailable).
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        room = get_object_or_404(ChatRoom, id=room_id, is_active=True)

        if not room.participants.filter(id=request.user.id).exists():
            return Response(
                {"success": False, "message": "Not a participant."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = Message.objects.create(
            room=room,
            sender=request.user,
            message_type=serializer.validated_data.get("message_type", Message.MessageType.TEXT),
            content=serializer.validated_data["content"],
        )

        # Update room timestamp
        room.save(update_fields=["updated_at"])

        # Notify other participant(s)
        other_users = room.participants.exclude(id=request.user.id)
        for other_user in other_users:
            notification = Notification.objects.create(
                user=other_user,
                notification_type=Notification.NotificationType.NEW_MESSAGE,
                title=f"New message from {request.user.full_name}",
                body=message.content[:100],
                data={
                    "chat_room_id": str(room.id),
                    "message_id": str(message.id),
                    "sender_id": str(request.user.id),
                },
            )
            send_realtime_notification(other_user.id, notification)

        logger.info(f"Message sent (REST): room={room_id} sender={request.user.email}")

        return Response(
            {
                "success": True,
                "message": "Message sent.",
                "data": MessageSerializer(message).data,
            },
            status=status.HTTP_201_CREATED,
        )


class MarkMessagesReadView(APIView):
    """
    POST /api/v1/chat/rooms/<uuid:room_id>/read/
    Mark all unread messages in a room as read (for the current user).
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        room = get_object_or_404(ChatRoom, id=room_id, is_active=True)

        if not room.participants.filter(id=request.user.id).exists():
            return Response(
                {"success": False, "message": "Not a participant."},
                status=status.HTTP_403_FORBIDDEN,
            )

        updated = (
            Message.objects.filter(
                room=room,
                is_read=False,
            )
            .exclude(sender=request.user)
            .update(
                is_read=True,
                read_at=timezone.now(),
            )
        )

        return Response(
            {
                "success": True,
                "message": f"{updated} message(s) marked as read.",
            }
        )


# ═══════════════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════


class NotificationListView(generics.ListAPIView):
    """
    GET /api/v1/notifications/
    List all notifications for the authenticated user.

    Query params:
    - unread_only: "true" to filter only unread
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user)
        if self.request.query_params.get("unread_only") == "true":
            qs = qs.filter(is_read=False)
        return qs


class NotificationMarkReadView(APIView):
    """
    POST /api/v1/notifications/<uuid:pk>/read/
    Mark a single notification as read.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        notification = get_object_or_404(Notification, id=pk, user=request.user)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])

        return Response({"success": True, "message": "Notification marked as read."})


class NotificationMarkAllReadView(APIView):
    """
    POST /api/v1/notifications/read-all/
    Mark all notifications as read.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )

        return Response(
            {
                "success": True,
                "message": f"{updated} notification(s) marked as read.",
            }
        )


class NotificationUnreadCountView(APIView):
    """
    GET /api/v1/notifications/unread-count/
    Get the count of unread notifications.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()

        return Response({"success": True, "data": {"unread_count": count}})
