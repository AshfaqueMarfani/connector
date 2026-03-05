import 'package:flutter_test/flutter_test.dart';
import 'package:connector_app/models/status.dart';

void main() {
  group('Status model', () {
    test('fromJson parses need status correctly', () {
      final json = {
        'id': 'status-001',
        'user': {
          'id': 'user-001',
          'full_name': 'Alice',
          'account_type': 'individual',
        },
        'status_type': 'need',
        'text': 'Need emergency food assistance near Clifton',
        'urgency': 'high',
        'ai_parsed_intent': 'food_assistance',
        'ai_tags': ['food', 'emergency', 'Clifton'],
        'is_active': true,
        'expires_at': '2024-06-16T10:00:00Z',
        'created_at': '2024-06-15T10:00:00Z',
        'updated_at': '2024-06-15T10:00:00Z',
      };

      final status = Status.fromJson(json);

      expect(status.id, 'status-001');
      expect(status.user.fullName, 'Alice');
      expect(status.statusType, 'need');
      expect(status.text, contains('emergency food'));
      expect(status.urgency, 'high');
      expect(status.aiParsedIntent, 'food_assistance');
      expect(status.aiTags, ['food', 'emergency', 'Clifton']);
      expect(status.isActive, true);
      expect(status.isNeed, true);
      expect(status.isOffer, false);
    });

    test('fromJson parses offer status correctly', () {
      final json = {
        'id': 'status-002',
        'user': {
          'id': 'user-002',
          'full_name': 'Business Corp',
          'account_type': 'business',
        },
        'status_type': 'offer',
        'text': 'Free tutoring available for children',
        'urgency': 'low',
        'created_at': '2024-06-15T10:00:00Z',
        'updated_at': '2024-06-15T10:00:00Z',
      };

      final status = Status.fromJson(json);
      expect(status.isOffer, true);
      expect(status.isNeed, false);
      expect(status.urgency, 'low');
    });

    test('fromJson handles missing optional fields', () {
      final json = {
        'id': 'status-003',
        'user': {'id': 'user-003', 'full_name': 'Bob'},
        'status_type': 'need',
        'text': 'Looking for help',
        'created_at': '2024-06-15T10:00:00Z',
        'updated_at': '2024-06-15T10:00:00Z',
      };

      final status = Status.fromJson(json);
      expect(status.aiParsedIntent, '');
      expect(status.aiTags, isEmpty);
      expect(status.urgency, 'low');
      expect(status.expiresAt, isNull);
    });
  });
}
