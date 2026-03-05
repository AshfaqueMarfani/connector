import 'package:flutter_test/flutter_test.dart';
import 'package:connector_app/core/utils/validators.dart';

void main() {
  group('Validators.email', () {
    test('returns error for null input', () {
      expect(Validators.email(null), isNotNull);
    });

    test('returns error for empty string', () {
      expect(Validators.email(''), 'Email is required');
    });

    test('returns error for invalid email', () {
      expect(Validators.email('not-an-email'), isNotNull);
      expect(Validators.email('missing@'), isNotNull);
      expect(Validators.email('@domain.com'), isNotNull);
    });

    test('returns null for valid email', () {
      expect(Validators.email('user@example.com'), isNull);
      expect(Validators.email('first.last@domain.org'), isNull);
      expect(Validators.email('test-user@sub.domain.co'), isNull);
    });
  });

  group('Validators.password', () {
    test('returns error for null input', () {
      expect(Validators.password(null), isNotNull);
    });

    test('returns error for empty string', () {
      expect(Validators.password(''), 'Password is required');
    });

    test('returns error for short password', () {
      expect(Validators.password('short'), isNotNull);
      expect(Validators.password('1234567'), isNotNull);
    });

    test('returns null for valid password', () {
      expect(Validators.password('12345678'), isNull);
      expect(Validators.password('StrongPassword123!'), isNull);
    });
  });

  group('Validators.confirmPassword', () {
    test('returns error when empty', () {
      expect(Validators.confirmPassword('', 'password'), isNotNull);
      expect(Validators.confirmPassword(null, 'password'), isNotNull);
    });

    test('returns error when passwords do not match', () {
      expect(Validators.confirmPassword('abc123', 'xyz789'), isNotNull);
    });

    test('returns null when passwords match', () {
      expect(Validators.confirmPassword('MyPass123!', 'MyPass123!'), isNull);
    });
  });

  group('Validators.required', () {
    test('returns error for null input', () {
      expect(Validators.required(null), isNotNull);
    });

    test('returns error for empty or whitespace-only', () {
      expect(Validators.required(''), isNotNull);
      expect(Validators.required('   '), isNotNull);
    });

    test('uses custom field name', () {
      expect(Validators.required('', 'Username'), 'Username is required');
    });

    test('returns null for valid input', () {
      expect(Validators.required('hello'), isNull);
    });
  });

  group('Validators.fullName', () {
    test('returns error for empty', () {
      expect(Validators.fullName(''), isNotNull);
      expect(Validators.fullName(null), isNotNull);
    });

    test('returns error for single character', () {
      expect(Validators.fullName('A'), isNotNull);
    });

    test('returns null for valid name', () {
      expect(Validators.fullName('Al'), isNull);
      expect(Validators.fullName('Alice Johnson'), isNull);
    });
  });

  group('Validators.statusText', () {
    test('returns error for empty', () {
      expect(Validators.statusText(''), isNotNull);
    });

    test('returns error for text under 10 chars', () {
      expect(Validators.statusText('too short'), isNotNull);
    });

    test('returns null for valid status text', () {
      expect(Validators.statusText('Need food assistance near Clifton area'), isNull);
    });
  });

  group('Validators.bio', () {
    test('returns null for normal bio', () {
      expect(Validators.bio('I love helping people'), isNull);
    });

    test('returns null for null', () {
      expect(Validators.bio(null), isNull);
    });

    test('returns error for bio over 500 chars', () {
      final longBio = 'x' * 501;
      expect(Validators.bio(longBio), isNotNull);
    });
  });
}
