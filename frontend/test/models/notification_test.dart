import 'package:flutter_test/flutter_test.dart';
import 'package:connector_app/models/notification.dart';

void main() {
  group('AppNotification model', () {
    test('fromJson parses connection request notification', () {
      final json = {
        'id': 'notif-001',
        'notification_type': 'connection_request',
        'title': 'New Connection Request',
        'body': 'Alice wants to connect with you',
        'data': {'from_user_id': 'user-001'},
        'is_read': false,
        'created_at': '2024-06-15T10:00:00Z',
      };

      final notif = AppNotification.fromJson(json);

      expect(notif.id, 'notif-001');
      expect(notif.notificationType, 'connection_request');
      expect(notif.title, 'New Connection Request');
      expect(notif.body, contains('Alice'));
      expect(notif.isRead, false);
      expect(notif.isConnectionRequest, true);
      expect(notif.isConnectionAccepted, false);
      expect(notif.isNewMessage, false);
      expect(notif.isMatchAlert, false);
    });

    test('fromJson parses match alert notification', () {
      final json = {
        'id': 'notif-002',
        'notification_type': 'match_alert',
        'title': 'New Match!',
        'body': 'You matched with a nearby NGO',
        'data': {'match_id': 'match-001'},
        'is_read': true,
        'read_at': '2024-06-15T11:00:00Z',
        'created_at': '2024-06-15T10:00:00Z',
      };

      final notif = AppNotification.fromJson(json);
      expect(notif.isMatchAlert, true);
      expect(notif.isRead, true);
      expect(notif.readAt, isNotNull);
    });

    test('fromWs creates from WebSocket data', () {
      final json = {
        'notification_id': 'ws-notif-001',
        'notification_type': 'new_message',
        'title': 'New Message',
        'body': 'You have a new message from Bob',
        'data': {'room_id': 'room-001'},
      };

      final notif = AppNotification.fromWs(json);

      expect(notif.id, 'ws-notif-001');
      expect(notif.isNewMessage, true);
      expect(notif.body, contains('Bob'));
    });

    test('fromJson handles missing optional fields', () {
      final json = {
        'id': 'notif-003',
        'created_at': '2024-06-15T10:00:00Z',
      };

      final notif = AppNotification.fromJson(json);
      expect(notif.notificationType, '');
      expect(notif.title, '');
      expect(notif.body, '');
      expect(notif.data, isEmpty);
      expect(notif.isRead, false);
      expect(notif.readAt, isNull);
    });
  });
}
