import 'package:flutter_test/flutter_test.dart';
import 'package:connector_app/models/match_result.dart';

void main() {
  group('MatchResult model', () {
    test('fromJson parses full match result', () {
      final json = {
        'id': 'match-001',
        'score': 0.87,
        'reason': 'Profile tags overlap: food, volunteer',
        'matched_tags': ['food', 'volunteer'],
        'distance_meters': 350.5,
        'match_status': 'pending',
        'created_at': '2024-06-15T10:00:00Z',
        'status_detail': {
          'id': 'status-001',
          'status_type': 'need',
          'text': 'Need food assistance',
          'urgency': 'high',
          'ai_tags': ['food', 'emergency'],
        },
        'matched_user_detail': {
          'id': 'user-001',
          'full_name': 'Alice',
          'account_type': 'individual',
        },
      };

      final match = MatchResult.fromJson(json);

      expect(match.id, 'match-001');
      expect(match.score, 0.87);
      expect(match.reason, contains('food'));
      expect(match.matchedTags, ['food', 'volunteer']);
      expect(match.distanceMeters, 350.5);
      expect(match.matchStatus, 'pending');
      expect(match.statusDetail, isNotNull);
      expect(match.statusDetail!.statusType, 'need');
      expect(match.matchedUserDetail, isNotNull);
      expect(match.matchedUserDetail!.fullName, 'Alice');
    });

    test('scorePercent formats correctly', () {
      final match = MatchResult(
        id: 'test',
        score: 0.953,
        reason: '',
        distanceMeters: 0,
        matchStatus: 'pending',
        createdAt: DateTime.now(),
      );
      expect(match.scorePercent, '95%');
    });

    test('distanceFormatted for meters', () {
      final match = MatchResult(
        id: 'test',
        score: 0.5,
        reason: '',
        distanceMeters: 450.0,
        matchStatus: 'pending',
        createdAt: DateTime.now(),
      );
      expect(match.distanceFormatted, '450m');
    });

    test('distanceFormatted for kilometers', () {
      final match = MatchResult(
        id: 'test',
        score: 0.5,
        reason: '',
        distanceMeters: 2500.0,
        matchStatus: 'pending',
        createdAt: DateTime.now(),
      );
      expect(match.distanceFormatted, '2.5km');
    });

    test('fromJson handles missing optional fields', () {
      final json = {
        'id': 'match-002',
        'created_at': '2024-06-15T10:00:00Z',
      };

      final match = MatchResult.fromJson(json);
      expect(match.score, 0);
      expect(match.reason, '');
      expect(match.matchedTags, isEmpty);
      expect(match.matchStatus, 'pending');
      expect(match.statusDetail, isNull);
      expect(match.matchedUserDetail, isNull);
    });
  });

  group('MatchStatusDetail model', () {
    test('fromJson parses correctly', () {
      final json = {
        'id': 'status-001',
        'status_type': 'need',
        'text': 'Need tutoring for math',
        'urgency': 'medium',
        'ai_tags': ['tutoring', 'math'],
      };

      final detail = MatchStatusDetail.fromJson(json);

      expect(detail.id, 'status-001');
      expect(detail.statusType, 'need');
      expect(detail.text, 'Need tutoring for math');
      expect(detail.urgency, 'medium');
      expect(detail.aiTags, ['tutoring', 'math']);
    });
  });
}
