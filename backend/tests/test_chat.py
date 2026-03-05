"""
Phase 2 Tests: Chat, Connection Requests, Notifications.

Covers:
- Connection request lifecycle (send, accept, decline, cancel)
- Chat room creation upon acceptance
- Message sending via REST API
- Read receipts
- Notification creation and management
- Permission enforcement (only participants can access rooms)
- Block enforcement on connection requests
- WebSocket consumer unit tests
"""

from django.contrib.gis.geos import Point
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.chat.models import ChatRoom, ConnectionRequest, Message, Notification
from apps.moderation.models import Block


@override_settings(
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
)
class ConnectionRequestTests(TestCase):
    """Tests for the connection request lifecycle."""

    def setUp(self):
        self.client = APIClient()
        self.user_a = User.objects.create_user(
            email="alice@test.com",
            password="TestPass123!",
            full_name="Alice Test",
            account_type="individual",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )
        self.user_b = User.objects.create_user(
            email="bob@test.com",
            password="TestPass123!",
            full_name="Bob Test",
            account_type="individual",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )
        self.user_c = User.objects.create_user(
            email="carol@test.com",
            password="TestPass123!",
            full_name="Carol Test",
            account_type="business",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )
        self.client.force_authenticate(user=self.user_a)

    def test_send_connection_request(self):
        """Sending a connection request should succeed."""
        resp = self.client.post(
            "/api/v1/chat/connections/request/",
            {"to_user": str(self.user_b.id)},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(resp.data["success"])
        self.assertEqual(resp.data["data"]["status"], "pending")

    def test_cannot_connect_to_self(self):
        """Users cannot send a connection request to themselves."""
        resp = self.client.post(
            "/api/v1/chat/connections/request/",
            {"to_user": str(self.user_a.id)},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_send_duplicate_request(self):
        """Cannot send a second pending request to the same user."""
        self.client.post(
            "/api/v1/chat/connections/request/",
            {"to_user": str(self.user_b.id)},
            format="json",
        )
        resp = self.client.post(
            "/api/v1/chat/connections/request/",
            {"to_user": str(self.user_b.id)},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_blocked_user_cannot_connect(self):
        """Blocked users cannot send connection requests."""
        Block.objects.create(blocker=self.user_b, blocked=self.user_a)
        resp = self.client.post(
            "/api/v1/chat/connections/request/",
            {"to_user": str(self.user_b.id)},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_accept_connection_request(self):
        """Accepting a request should create a chat room."""
        cr = ConnectionRequest.objects.create(
            from_user=self.user_a, to_user=self.user_b
        )
        self.client.force_authenticate(user=self.user_b)
        resp = self.client.post(f"/api/v1/chat/connections/{cr.id}/accept/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        cr.refresh_from_db()
        self.assertEqual(cr.status, "accepted")
        self.assertIsNotNone(cr.chat_room)
        # Chat room should have both participants
        self.assertEqual(cr.chat_room.participants.count(), 2)

    def test_decline_connection_request(self):
        """Declining a request should update status."""
        cr = ConnectionRequest.objects.create(
            from_user=self.user_a, to_user=self.user_b
        )
        self.client.force_authenticate(user=self.user_b)
        resp = self.client.post(f"/api/v1/chat/connections/{cr.id}/decline/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        cr.refresh_from_db()
        self.assertEqual(cr.status, "declined")

    def test_cancel_connection_request(self):
        """Sender can cancel their own pending request."""
        cr = ConnectionRequest.objects.create(
            from_user=self.user_a, to_user=self.user_b
        )
        resp = self.client.post(f"/api/v1/chat/connections/{cr.id}/cancel/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        cr.refresh_from_db()
        self.assertEqual(cr.status, "cancelled")

    def test_only_recipient_can_accept(self):
        """Sender cannot accept their own request."""
        cr = ConnectionRequest.objects.create(
            from_user=self.user_a, to_user=self.user_b
        )
        resp = self.client.post(f"/api/v1/chat/connections/{cr.id}/accept/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_only_sender_can_cancel(self):
        """Recipient cannot cancel a received request."""
        cr = ConnectionRequest.objects.create(
            from_user=self.user_a, to_user=self.user_b
        )
        self.client.force_authenticate(user=self.user_b)
        resp = self.client.post(f"/api/v1/chat/connections/{cr.id}/cancel/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_connection_requests(self):
        """List should return all requests for the user."""
        ConnectionRequest.objects.create(
            from_user=self.user_a, to_user=self.user_b
        )
        ConnectionRequest.objects.create(
            from_user=self.user_c, to_user=self.user_a
        )
        resp = self.client.get("/api/v1/chat/connections/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)

    def test_list_filter_by_direction(self):
        """Filter by sent/received direction."""
        ConnectionRequest.objects.create(
            from_user=self.user_a, to_user=self.user_b
        )
        ConnectionRequest.objects.create(
            from_user=self.user_c, to_user=self.user_a
        )
        resp = self.client.get("/api/v1/chat/connections/?direction=sent")
        self.assertEqual(resp.data["count"], 1)
        resp = self.client.get("/api/v1/chat/connections/?direction=received")
        self.assertEqual(resp.data["count"], 1)

    def test_notification_created_on_request(self):
        """Sending a request should create a notification for the recipient."""
        self.client.post(
            "/api/v1/chat/connections/request/",
            {"to_user": str(self.user_b.id)},
            format="json",
        )
        notifs = Notification.objects.filter(user=self.user_b)
        self.assertEqual(notifs.count(), 1)
        self.assertEqual(notifs.first().notification_type, "connection_request")

    def test_notification_created_on_accept(self):
        """Accepting a request should notify the sender."""
        cr = ConnectionRequest.objects.create(
            from_user=self.user_a, to_user=self.user_b
        )
        self.client.force_authenticate(user=self.user_b)
        self.client.post(f"/api/v1/chat/connections/{cr.id}/accept/")
        notifs = Notification.objects.filter(
            user=self.user_a, notification_type="connection_accepted"
        )
        self.assertEqual(notifs.count(), 1)


@override_settings(
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
)
class ChatRoomTests(TestCase):
    """Tests for chat room endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user_a = User.objects.create_user(
            email="alice@chat.com",
            password="TestPass123!",
            full_name="Alice Chat",
            account_type="individual",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )
        self.user_b = User.objects.create_user(
            email="bob@chat.com",
            password="TestPass123!",
            full_name="Bob Chat",
            account_type="individual",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )
        self.user_c = User.objects.create_user(
            email="carol@chat.com",
            password="TestPass123!",
            full_name="Carol Chat",
            account_type="individual",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )
        # Create a chat room between A and B
        self.room = ChatRoom.objects.create()
        self.room.participants.add(self.user_a, self.user_b)
        self.client.force_authenticate(user=self.user_a)

    def test_list_chat_rooms(self):
        """Should list rooms the user is a participant of."""
        resp = self.client.get("/api/v1/chat/rooms/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_chat_room_detail(self):
        """Should return room details for participants."""
        resp = self.client.get(f"/api/v1/chat/rooms/{self.room.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["participants"]), 2)

    def test_non_participant_cannot_view_room(self):
        """Non-participants should get 403."""
        self.client.force_authenticate(user=self.user_c)
        resp = self.client.get(f"/api/v1/chat/rooms/{self.room.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_send_message_rest(self):
        """Sending a message via REST should work."""
        resp = self.client.post(
            f"/api/v1/chat/rooms/{self.room.id}/messages/send/",
            {"content": "Hello from REST!"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.filter(room=self.room).count(), 1)

    def test_non_participant_cannot_send(self):
        """Non-participants should not be able to send messages."""
        self.client.force_authenticate(user=self.user_c)
        resp = self.client.post(
            f"/api/v1/chat/rooms/{self.room.id}/messages/send/",
            {"content": "Should fail"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_messages(self):
        """Should list messages in order."""
        Message.objects.create(
            room=self.room,
            sender=self.user_a,
            content="First message",
        )
        Message.objects.create(
            room=self.room,
            sender=self.user_b,
            content="Second message",
        )
        resp = self.client.get(f"/api/v1/chat/rooms/{self.room.id}/messages/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)
        self.assertEqual(resp.data["results"][0]["content"], "First message")

    def test_mark_messages_read(self):
        """Marking messages as read should only affect other user's messages."""
        msg = Message.objects.create(
            room=self.room,
            sender=self.user_b,
            content="Read me",
        )
        own_msg = Message.objects.create(
            room=self.room,
            sender=self.user_a,
            content="My own message",
        )
        resp = self.client.post(f"/api/v1/chat/rooms/{self.room.id}/read/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        msg.refresh_from_db()
        own_msg.refresh_from_db()
        self.assertTrue(msg.is_read)
        self.assertFalse(own_msg.is_read)  # Own messages stay unread

    def test_message_creates_notification(self):
        """Sending a message via REST should notify the other participant."""
        self.client.post(
            f"/api/v1/chat/rooms/{self.room.id}/messages/send/",
            {"content": "Yo!"},
            format="json",
        )
        notifs = Notification.objects.filter(
            user=self.user_b, notification_type="new_message"
        )
        self.assertEqual(notifs.count(), 1)


@override_settings(
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
)
class NotificationTests(TestCase):
    """Tests for notification management endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="notif@test.com",
            password="TestPass123!",
            full_name="Notif User",
            account_type="individual",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )
        self.client.force_authenticate(user=self.user)

        # Create some notifications
        self.notif1 = Notification.objects.create(
            user=self.user,
            notification_type="connection_request",
            title="Request from Alice",
            body="Alice wants to connect.",
        )
        self.notif2 = Notification.objects.create(
            user=self.user,
            notification_type="new_message",
            title="New message",
            body="Hey!",
        )
        self.notif3 = Notification.objects.create(
            user=self.user,
            notification_type="system",
            title="Welcome",
            body="Welcome to Connector!",
            is_read=True,
        )

    def test_list_all_notifications(self):
        """Should return all notifications."""
        resp = self.client.get("/api/v1/notifications/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 3)

    def test_list_unread_only(self):
        """Filter to only unread notifications."""
        resp = self.client.get("/api/v1/notifications/?unread_only=true")
        self.assertEqual(resp.data["count"], 2)

    def test_mark_notification_read(self):
        """Mark a single notification as read."""
        resp = self.client.post(f"/api/v1/notifications/{self.notif1.id}/read/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.notif1.refresh_from_db()
        self.assertTrue(self.notif1.is_read)
        self.assertIsNotNone(self.notif1.read_at)

    def test_mark_all_read(self):
        """Mark all notifications as read."""
        resp = self.client.post("/api/v1/notifications/read-all/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        unread = Notification.objects.filter(user=self.user, is_read=False).count()
        self.assertEqual(unread, 0)

    def test_unread_count(self):
        """Get the count of unread notifications."""
        resp = self.client.get("/api/v1/notifications/unread-count/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["data"]["unread_count"], 2)


@override_settings(
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
)
class ConnectionRequestModelTests(TestCase):
    """Tests for ConnectionRequest model methods."""

    def setUp(self):
        self.user_a = User.objects.create_user(
            email="model_a@test.com",
            password="TestPass123!",
            full_name="Model A",
            account_type="individual",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )
        self.user_b = User.objects.create_user(
            email="model_b@test.com",
            password="TestPass123!",
            full_name="Model B",
            account_type="individual",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )

    def test_accept_creates_chat_room(self):
        """Accepting should create a ChatRoom with system message."""
        cr = ConnectionRequest.objects.create(
            from_user=self.user_a, to_user=self.user_b
        )
        room = cr.accept()
        self.assertIsNotNone(room)
        self.assertEqual(room.participants.count(), 2)
        self.assertEqual(room.messages.count(), 1)
        self.assertEqual(
            room.messages.first().message_type, Message.MessageType.SYSTEM
        )

    def test_accept_non_pending_raises(self):
        """Accepting a non-pending request should raise ValueError."""
        cr = ConnectionRequest.objects.create(
            from_user=self.user_a,
            to_user=self.user_b,
            status=ConnectionRequest.RequestStatus.DECLINED,
        )
        with self.assertRaises(ValueError):
            cr.accept()

    def test_decline_changes_status(self):
        """Declining should change status to declined."""
        cr = ConnectionRequest.objects.create(
            from_user=self.user_a, to_user=self.user_b
        )
        cr.decline()
        self.assertEqual(cr.status, "declined")

    def test_cancel_changes_status(self):
        """Cancelling should change status to cancelled."""
        cr = ConnectionRequest.objects.create(
            from_user=self.user_a, to_user=self.user_b
        )
        cr.cancel()
        self.assertEqual(cr.status, "cancelled")

    def test_notification_model_str(self):
        """Notification __str__ should be descriptive."""
        notif = Notification.objects.create(
            user=self.user_a,
            notification_type="system",
            title="Test notification",
        )
        self.assertIn("System", str(notif))
        self.assertIn("Test notification", str(notif))


@override_settings(
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
)
class FullConnectionFlowTest(TestCase):
    """End-to-end test: request → accept → chat → read."""

    def setUp(self):
        self.client = APIClient()
        self.user_a = User.objects.create_user(
            email="e2e_a@test.com",
            password="TestPass123!",
            full_name="E2E Alice",
            account_type="individual",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )
        self.user_b = User.objects.create_user(
            email="e2e_b@test.com",
            password="TestPass123!",
            full_name="E2E Bob",
            account_type="individual",
            eula_accepted_at="2026-01-01T00:00:00Z",
        )

    def test_full_connection_to_chat_flow(self):
        """
        Full E2E flow:
        1. Alice sends connection request to Bob
        2. Bob accepts
        3. Chat room is created
        4. Alice sends a message
        5. Bob reads the message
        6. Notifications are created at each step
        """
        # Step 1: Alice sends request
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.post(
            "/api/v1/chat/connections/request/",
            {"to_user": str(self.user_b.id), "message": "Hi Bob!"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        cr_id = resp.data["data"]["id"]

        # Bob should have a notification
        self.assertEqual(
            Notification.objects.filter(
                user=self.user_b, notification_type="connection_request"
            ).count(),
            1,
        )

        # Step 2: Bob accepts
        self.client.force_authenticate(user=self.user_b)
        resp = self.client.post(f"/api/v1/chat/connections/{cr_id}/accept/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        room_id = resp.data["data"]["chat_room"]
        self.assertIsNotNone(room_id)

        # Alice should have an acceptance notification
        self.assertEqual(
            Notification.objects.filter(
                user=self.user_a, notification_type="connection_accepted"
            ).count(),
            1,
        )

        # Step 3: Both users can see the chat room
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get("/api/v1/chat/rooms/")
        self.assertEqual(resp.data["count"], 1)

        self.client.force_authenticate(user=self.user_b)
        resp = self.client.get("/api/v1/chat/rooms/")
        self.assertEqual(resp.data["count"], 1)

        # Step 4: Alice sends a message
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.post(
            f"/api/v1/chat/rooms/{room_id}/messages/send/",
            {"content": "Hey Bob, thanks for connecting!"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Verify messages (system message + Alice's message)
        resp = self.client.get(f"/api/v1/chat/rooms/{room_id}/messages/")
        self.assertEqual(resp.data["count"], 2)  # system + text

        # Step 5: Bob marks messages as read
        self.client.force_authenticate(user=self.user_b)
        resp = self.client.post(f"/api/v1/chat/rooms/{room_id}/read/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Verify Alice's message is now marked as read
        alice_msg = Message.objects.filter(
            room_id=room_id, sender=self.user_a, message_type="text"
        ).first()
        self.assertTrue(alice_msg.is_read)
