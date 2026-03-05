"""
URL configuration for the chat app.

Provides REST API endpoints for:
- Connection requests
- Chat rooms and messages
- Notifications
"""

from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    # ── Connection Requests ──────────────────────────────────────────
    path(
        "chat/connections/request/",
        views.ConnectionRequestCreateView.as_view(),
        name="connection-request-create",
    ),
    path(
        "chat/connections/",
        views.ConnectionRequestListView.as_view(),
        name="connection-request-list",
    ),
    path(
        "chat/connections/<uuid:pk>/accept/",
        views.ConnectionRequestRespondView.as_view(),
        {"action": "accept"},
        name="connection-request-accept",
    ),
    path(
        "chat/connections/<uuid:pk>/decline/",
        views.ConnectionRequestRespondView.as_view(),
        {"action": "decline"},
        name="connection-request-decline",
    ),
    path(
        "chat/connections/<uuid:pk>/cancel/",
        views.ConnectionRequestRespondView.as_view(),
        {"action": "cancel"},
        name="connection-request-cancel",
    ),
    # ── Chat Rooms ───────────────────────────────────────────────────
    path(
        "chat/rooms/",
        views.ChatRoomListView.as_view(),
        name="chat-room-list",
    ),
    path(
        "chat/rooms/<uuid:room_id>/",
        views.ChatRoomDetailView.as_view(),
        name="chat-room-detail",
    ),
    # ── Messages ─────────────────────────────────────────────────────
    path(
        "chat/rooms/<uuid:room_id>/messages/",
        views.MessageListView.as_view(),
        name="message-list",
    ),
    path(
        "chat/rooms/<uuid:room_id>/messages/send/",
        views.MessageCreateView.as_view(),
        name="message-create",
    ),
    path(
        "chat/rooms/<uuid:room_id>/read/",
        views.MarkMessagesReadView.as_view(),
        name="messages-mark-read",
    ),
    # ── Notifications ────────────────────────────────────────────────
    path(
        "notifications/",
        views.NotificationListView.as_view(),
        name="notification-list",
    ),
    path(
        "notifications/<uuid:pk>/read/",
        views.NotificationMarkReadView.as_view(),
        name="notification-mark-read",
    ),
    path(
        "notifications/read-all/",
        views.NotificationMarkAllReadView.as_view(),
        name="notification-mark-all-read",
    ),
    path(
        "notifications/unread-count/",
        views.NotificationUnreadCountView.as_view(),
        name="notification-unread-count",
    ),
]
