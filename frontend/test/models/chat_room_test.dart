import 'package:flutter_test/flutter_test.dart';
import 'package:connector_app/models/chat_room.dart';

void main() {
  group('ChatRoom model', () {
    test('fromJson parses room with last message', () {
      final json = {
        'id': 'room-001',
        'participants': [
          {'id': 'user-001', 'full_name': 'Alice', 'account_type': 'individual'},
          {'id': 'user-002', 'full_name': 'Bob', 'account_type': 'business'},
        ],
        'is_active': true,
        'last_message': {
          'id': 'msg-001',
          'room': 'room-001',
          'sender': {'id': 'user-001', 'full_name': 'Alice'},
          'message_type': 'text',
          'content': 'Hello Bob!',
          'is_read': false,
          'created_at': '2024-06-15T11:00:00Z',
        },
        'unread_count': 2,
        'created_at': '2024-06-15T10:00:00Z',
        'updated_at': '2024-06-15T11:00:00Z',
      };

      final room = ChatRoom.fromJson(json);

      expect(room.id, 'room-001');
      expect(room.participants.length, 2);
      expect(room.isActive, true);
      expect(room.lastMessage, isNotNull);
      expect(room.lastMessage!.content, 'Hello Bob!');
      expect(room.unreadCount, 2);
    });

    test('otherParticipant returns correct user', () {
      final json = {
        'id': 'room-002',
        'participants': [
          {'id': 'me-id', 'full_name': 'Me'},
          {'id': 'other-id', 'full_name': 'Other Person'},
        ],
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
      };

      final room = ChatRoom.fromJson(json);
      final other = room.otherParticipant('me-id');

      expect(other, isNotNull);
      expect(other!.id, 'other-id');
      expect(other.fullName, 'Other Person');
    });

    test('otherParticipant returns first when no match', () {
      final json = {
        'id': 'room-003',
        'participants': [
          {'id': 'user-a', 'full_name': 'User A'},
        ],
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
      };

      final room = ChatRoom.fromJson(json);
      final other = room.otherParticipant('unknown-id');
      expect(other!.id, 'user-a');
    });

    test('fromJson without last_message sets null', () {
      final json = {
        'id': 'room-004',
        'participants': [],
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
      };

      final room = ChatRoom.fromJson(json);
      expect(room.lastMessage, isNull);
      expect(room.unreadCount, 0);
    });
  });

  group('Message model', () {
    test('fromJson parses text message correctly', () {
      final json = {
        'id': 'msg-001',
        'room': 'room-001',
        'sender': {
          'id': 'sender-id',
          'full_name': 'Sender Name',
          'account_type': 'individual',
        },
        'message_type': 'text',
        'content': 'Hello, this is a test message.',
        'is_read': true,
        'read_at': '2024-06-15T12:00:00Z',
        'created_at': '2024-06-15T11:00:00Z',
      };

      final msg = Message.fromJson(json);

      expect(msg.id, 'msg-001');
      expect(msg.roomId, 'room-001');
      expect(msg.sender.id, 'sender-id');
      expect(msg.messageType, 'text');
      expect(msg.content, 'Hello, this is a test message.');
      expect(msg.isRead, true);
      expect(msg.readAt, isNotNull);
      expect(msg.isLocation, false);
      expect(msg.isSystem, false);
    });

    test('fromWs creates message from WebSocket data', () {
      final json = {
        'message_id': 'ws-msg-001',
        'sender_id': 'ws-sender',
        'sender_name': 'WS User',
        'message_type': 'text',
        'content': 'WebSocket message',
        'timestamp': '2024-06-15T11:00:00Z',
      };

      final msg = Message.fromWs(json);

      expect(msg.id, 'ws-msg-001');
      expect(msg.sender.id, 'ws-sender');
      expect(msg.sender.fullName, 'WS User');
      expect(msg.content, 'WebSocket message');
    });

    test('location message type detection', () {
      final json = {
        'id': 'msg-loc',
        'room': 'room-001',
        'sender': {'id': 's', 'full_name': 'S'},
        'message_type': 'location',
        'content': '24.8607,67.0011',
        'created_at': '2024-06-15T11:00:00Z',
      };

      final msg = Message.fromJson(json);
      expect(msg.isLocation, true);
      expect(msg.isSystem, false);
    });

    test('system message type detection', () {
      final json = {
        'id': 'msg-sys',
        'room': 'room-001',
        'sender': {'id': 'sys', 'full_name': 'System'},
        'message_type': 'system',
        'content': 'User joined the chat',
        'created_at': '2024-06-15T11:00:00Z',
      };

      final msg = Message.fromJson(json);
      expect(msg.isSystem, true);
      expect(msg.isLocation, false);
    });
  });
}
