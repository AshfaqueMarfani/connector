"""
Utility functions for the chat app.

Provides helpers for pushing real-time notifications via Django Channels.
"""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def send_realtime_notification(user_id, notification):
    """
    Push a notification to the user's WebSocket notification channel.

    Args:
        user_id: UUID of the target user
        notification: Notification model instance
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.warning("Channel layer not available – skipping realtime notification")
        return

    group_name = f"notifications_{user_id}"

    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "notification.new",
                "notification_id": str(notification.id),
                "notification_type": notification.notification_type,
                "title": notification.title,
                "body": notification.body,
                "data": notification.data,
                "created_at": notification.created_at.isoformat(),
            },
        )
    except Exception as e:
        # Don't fail the request if the notification push fails
        logger.error(f"Failed to push realtime notification: {e}")


def send_chat_room_event(room_id, event_data):
    """
    Send an event to all participants in a chat room.

    Args:
        room_id: UUID of the chat room
        event_data: dict with 'type' and payload
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    group_name = f"chat_{room_id}"

    try:
        async_to_sync(channel_layer.group_send)(group_name, event_data)
    except Exception as e:
        logger.error(f"Failed to push chat room event: {e}")
