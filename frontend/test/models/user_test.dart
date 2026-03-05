import 'package:flutter_test/flutter_test.dart';
import 'package:connector_app/models/user.dart';

void main() {
  group('User model', () {
    test('fromJson parses all fields correctly', () {
      final json = {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'email': 'alice@example.com',
        'full_name': 'Alice Johnson',
        'account_type': 'individual',
        'account_type_display': 'Individual',
        'is_active': true,
        'date_joined': '2024-06-15T10:30:00Z',
      };

      final user = User.fromJson(json);

      expect(user.id, '123e4567-e89b-12d3-a456-426614174000');
      expect(user.email, 'alice@example.com');
      expect(user.fullName, 'Alice Johnson');
      expect(user.accountType, 'individual');
      expect(user.accountTypeDisplay, 'Individual');
      expect(user.isActive, true);
      expect(user.dateJoined, DateTime.utc(2024, 6, 15, 10, 30));
    });

    test('fromJson handles missing optional fields with defaults', () {
      final json = {
        'id': 'abc-123',
        'date_joined': '2024-01-01T00:00:00Z',
      };

      final user = User.fromJson(json);

      expect(user.email, '');
      expect(user.fullName, '');
      expect(user.accountType, 'individual');
      expect(user.accountTypeDisplay, '');
      expect(user.isActive, true);
    });

    test('fromRef creates lightweight reference', () {
      final json = {
        'id': 'ref-uuid',
        'full_name': 'Bob Smith',
        'account_type': 'business',
      };

      final user = User.fromRef(json);

      expect(user.id, 'ref-uuid');
      expect(user.fullName, 'Bob Smith');
      expect(user.accountType, 'business');
      expect(user.email, '');
    });

    test('toJson serializes correctly', () {
      final user = User(
        id: 'test-id',
        email: 'test@test.com',
        fullName: 'Test User',
        accountType: 'ngo',
        dateJoined: DateTime.utc(2024, 1, 1),
      );

      final json = user.toJson();

      expect(json['id'], 'test-id');
      expect(json['email'], 'test@test.com');
      expect(json['full_name'], 'Test User');
      expect(json['account_type'], 'ngo');
    });

    test('fromJson handles inactive user', () {
      final json = {
        'id': 'inactive-user',
        'email': 'suspended@example.com',
        'full_name': 'Suspended User',
        'account_type': 'individual',
        'is_active': false,
        'date_joined': '2024-01-01T00:00:00Z',
      };

      final user = User.fromJson(json);
      expect(user.isActive, false);
    });
  });
}
