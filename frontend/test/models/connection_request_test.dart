import 'package:flutter_test/flutter_test.dart';
import 'package:connector_app/models/connection_request.dart';

void main() {
  group('ConnectionRequest model', () {
    test('fromJson parses pending request', () {
      final json = {
        'id': 'conn-001',
        'from_user': {
          'id': 'user-001',
          'full_name': 'Alice',
          'account_type': 'individual',
        },
        'to_user': {
          'id': 'user-002',
          'full_name': 'Bob',
          'account_type': 'business',
        },
        'message': 'Hi Bob, I need your services',
        'status': 'pending',
        'created_at': '2024-06-15T10:00:00Z',
        'updated_at': '2024-06-15T10:00:00Z',
      };

      final req = ConnectionRequest.fromJson(json);

      expect(req.id, 'conn-001');
      expect(req.fromUser.fullName, 'Alice');
      expect(req.toUser.fullName, 'Bob');
      expect(req.message, 'Hi Bob, I need your services');
      expect(req.status, 'pending');
      expect(req.isPending, true);
      expect(req.isAccepted, false);
      expect(req.chatRoomId, isNull);
    });

    test('fromJson parses accepted request with chat room', () {
      final json = {
        'id': 'conn-002',
        'from_user': {'id': 'user-001', 'full_name': 'Alice'},
        'to_user': {'id': 'user-002', 'full_name': 'Bob'},
        'status': 'accepted',
        'chat_room': 'room-001',
        'created_at': '2024-06-15T10:00:00Z',
        'updated_at': '2024-06-15T11:00:00Z',
      };

      final req = ConnectionRequest.fromJson(json);

      expect(req.isAccepted, true);
      expect(req.isPending, false);
      expect(req.chatRoomId, 'room-001');
    });

    test('fromJson defaults message to empty string', () {
      final json = {
        'id': 'conn-003',
        'from_user': {'id': 'user-001', 'full_name': 'X'},
        'to_user': {'id': 'user-002', 'full_name': 'Y'},
        'status': 'declined',
        'created_at': '2024-06-15T10:00:00Z',
        'updated_at': '2024-06-15T10:00:00Z',
      };

      final req = ConnectionRequest.fromJson(json);
      expect(req.message, '');
      expect(req.isPending, false);
      expect(req.isAccepted, false);
    });
  });
}
