import 'package:flutter_test/flutter_test.dart';
import 'package:connector_app/models/location.dart';

void main() {
  group('UserLocation model', () {
    test('fromJson parses exact coordinates', () {
      final json = {
        'exact_latitude': 24.8607,
        'exact_longitude': 67.0011,
        'obfuscated_latitude': 24.862,
        'obfuscated_longitude': 67.003,
        'source': 'gps',
        'accuracy_meters': 5.2,
        'altitude': 15.0,
        'heading': 180.0,
        'speed': 1.5,
        'is_background_tracking': false,
        'updated_at': '2024-06-15T10:00:00Z',
      };

      final loc = UserLocation.fromJson(json);

      expect(loc.latitude, 24.8607);
      expect(loc.longitude, 67.0011);
      expect(loc.obfuscatedLatitude, 24.862);
      expect(loc.obfuscatedLongitude, 67.003);
      expect(loc.source, 'gps');
      expect(loc.accuracyMeters, 5.2);
      expect(loc.altitude, 15.0);
      expect(loc.heading, 180.0);
      expect(loc.speed, 1.5);
      expect(loc.isBackgroundTracking, false);
    });

    test('fromJson falls back to latitude/longitude keys', () {
      final json = {
        'latitude': 24.86,
        'longitude': 67.00,
        'updated_at': '2024-06-15T10:00:00Z',
      };

      final loc = UserLocation.fromJson(json);
      expect(loc.latitude, 24.86);
      expect(loc.longitude, 67.00);
    });

    test('fromJson handles missing optional fields', () {
      final json = {
        'latitude': 0.0,
        'longitude': 0.0,
        'updated_at': '2024-01-01T00:00:00Z',
      };

      final loc = UserLocation.fromJson(json);
      expect(loc.obfuscatedLatitude, isNull);
      expect(loc.obfuscatedLongitude, isNull);
      expect(loc.accuracyMeters, isNull);
      expect(loc.altitude, isNull);
      expect(loc.heading, isNull);
      expect(loc.speed, isNull);
      expect(loc.isBackgroundTracking, false);
      expect(loc.source, 'gps');
    });
  });

  group('NearbyUser model', () {
    test('fromJson parses nearby user with location', () {
      final json = {
        'profile': {
          'id': 'profile-001',
          'display_name': 'Helping Hands NGO',
        },
        'location': {
          'latitude': 24.8607,
          'longitude': 67.0011,
          'is_exact': true,
          'source': 'gps',
          'accuracy_meters': 10.0,
          'updated_at': '2024-06-15T10:00:00Z',
        },
        'distance_meters': 250.5,
      };

      final nearby = NearbyUser.fromJson(json);

      expect(nearby.profileData['display_name'], 'Helping Hands NGO');
      expect(nearby.latitude, 24.8607);
      expect(nearby.longitude, 67.0011);
      expect(nearby.isExact, true);
      expect(nearby.distanceMeters, 250.5);
    });

    test('fromJson handles obfuscated (non-exact) location', () {
      final json = {
        'profile': {'id': 'profile-002'},
        'location': {
          'latitude': 24.862,
          'longitude': 67.003,
          'is_exact': false,
        },
        'distance_meters': 500.0,
      };

      final nearby = NearbyUser.fromJson(json);
      expect(nearby.isExact, false);
    });

    test('fromJson handles missing location gracefully', () {
      final json = {
        'profile': {'id': 'profile-003'},
        'distance_meters': 0.0,
      };

      final nearby = NearbyUser.fromJson(json);
      expect(nearby.latitude, 0);
      expect(nearby.longitude, 0);
      expect(nearby.isExact, false);
    });
  });
}
