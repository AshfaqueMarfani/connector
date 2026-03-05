"""
WebSocket URL routing for Django Channels.

Defines the WebSocket endpoints for:
- P2P Chat: ws/v1/chat/<room_id>/
- User Notifications: ws/v1/notifications/
"""

from django.urls import re_path

from .consumers import ChatConsumer, NotificationConsumer

websocket_urlpatterns = [
    re_path(
        r"ws/v1/chat/(?P<room_id>[0-9a-f\-]+)/$",
        ChatConsumer.as_asgi(),
    ),
    re_path(
        r"ws/v1/notifications/$",
        NotificationConsumer.as_asgi(),
    ),
]
