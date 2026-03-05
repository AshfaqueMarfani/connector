"""
Django admin configuration for the chat app.
"""

from django.contrib import admin

from .models import ChatRoom, ConnectionRequest, Message, Notification


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ["id", "sender", "message_type", "content", "is_read", "created_at"]
    can_delete = False


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ["id_short", "get_participants", "is_active", "created_at"]
    list_filter = ["is_active"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [MessageInline]

    @admin.display(description="Room ID")
    def id_short(self, obj):
        return str(obj.id)[:8]

    @admin.display(description="Participants")
    def get_participants(self, obj):
        return ", ".join(obj.participants.values_list("email", flat=True)[:2])


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["sender", "room_short", "message_type", "content_short", "is_read", "created_at"]
    list_filter = ["message_type", "is_read"]
    search_fields = ["sender__email", "content"]
    readonly_fields = ["id", "created_at"]
    raw_id_fields = ["room", "sender"]

    @admin.display(description="Room")
    def room_short(self, obj):
        return str(obj.room.id)[:8]

    @admin.display(description="Content")
    def content_short(self, obj):
        return obj.content[:80] if obj.content else ""


@admin.register(ConnectionRequest)
class ConnectionRequestAdmin(admin.ModelAdmin):
    list_display = ["from_user", "to_user", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["from_user__email", "to_user__email"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["from_user", "to_user", "chat_room"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "id_short",
        "user",
        "notification_type",
        "title",
        "is_read",
        "created_at",
    ]
    list_filter = ["notification_type", "is_read"]
    search_fields = ["user__email", "title", "body"]
    readonly_fields = ["id", "created_at"]
    raw_id_fields = ["user"]

    @admin.display(description="ID")
    def id_short(self, obj):
        return str(obj.id)[:8]
