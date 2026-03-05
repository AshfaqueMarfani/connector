import 'package:flutter_test/flutter_test.dart';
import 'package:connector_app/models/profile.dart';

void main() {
  group('Profile model', () {
    test('fromJson parses all fields correctly', () {
      final json = {
        'id': 'profile-001',
        'user': {
          'id': 'user-001',
          'full_name': 'Alice',
          'account_type': 'individual',
        },
        'display_name': 'Alice the Helper',
        'bio': 'I love volunteering',
        'avatar': 'https://example.com/avatar.jpg',
        'skills': ['cooking', 'tutoring'],
        'interests': ['community', 'education'],
        'tags': ['volunteer', 'food'],
        'is_public': false,
        'live_tracking_enabled': false,
        'is_online': true,
        'last_seen': '2024-06-15T10:00:00Z',
        'should_obfuscate_location': true,
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-06-15T10:00:00Z',
      };

      final profile = Profile.fromJson(json);

      expect(profile.id, 'profile-001');
      expect(profile.user.id, 'user-001');
      expect(profile.displayName, 'Alice the Helper');
      expect(profile.bio, 'I love volunteering');
      expect(profile.avatarUrl, 'https://example.com/avatar.jpg');
      expect(profile.skills, ['cooking', 'tutoring']);
      expect(profile.interests, ['community', 'education']);
      expect(profile.tags, ['volunteer', 'food']);
      expect(profile.isPublic, false);
      expect(profile.liveTrackingEnabled, false);
      expect(profile.isOnline, true);
      expect(profile.shouldObfuscateLocation, true);
    });

    test('fromJson handles null lists as empty', () {
      final json = {
        'id': 'profile-002',
        'user': {'id': 'user-002', 'full_name': 'Bob'},
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
      };

      final profile = Profile.fromJson(json);

      expect(profile.skills, isEmpty);
      expect(profile.interests, isEmpty);
      expect(profile.tags, isEmpty);
    });

    test('fromJson defaults to obfuscated location for private profiles', () {
      final json = {
        'id': 'profile-003',
        'user': {'id': 'user-003', 'full_name': 'Charlie'},
        'is_public': false,
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
      };

      final profile = Profile.fromJson(json);
      expect(profile.shouldObfuscateLocation, true);
    });

    test('public profile has exact location', () {
      final json = {
        'id': 'profile-004',
        'user': {'id': 'user-004', 'full_name': 'NGO Center'},
        'is_public': true,
        'should_obfuscate_location': false,
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
      };

      final profile = Profile.fromJson(json);
      expect(profile.isPublic, true);
      expect(profile.shouldObfuscateLocation, false);
    });
  });
}
