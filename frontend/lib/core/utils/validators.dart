/// Form validation helpers.
class Validators {
  Validators._();

  static String? email(String? value) {
    if (value == null || value.isEmpty) return 'Email is required';
    final regex = RegExp(r'^[\w\-.]+@([\w-]+\.)+[\w-]{2,4}$');
    if (!regex.hasMatch(value)) return 'Enter a valid email';
    return null;
  }

  static String? password(String? value) {
    if (value == null || value.isEmpty) return 'Password is required';
    if (value.length < 8) return 'Password must be at least 8 characters';
    return null;
  }

  static String? confirmPassword(String? value, String password) {
    if (value == null || value.isEmpty) return 'Please confirm your password';
    if (value != password) return 'Passwords do not match';
    return null;
  }

  static String? required(String? value, [String fieldName = 'This field']) {
    if (value == null || value.trim().isEmpty) return '$fieldName is required';
    return null;
  }

  static String? fullName(String? value) {
    if (value == null || value.trim().isEmpty) return 'Full name is required';
    if (value.trim().length < 2) return 'Name must be at least 2 characters';
    return null;
  }

  static String? statusText(String? value) {
    if (value == null || value.trim().isEmpty) return 'Status text is required';
    if (value.trim().length < 10) return 'Must be at least 10 characters';
    return null;
  }

  static String? bio(String? value) {
    if (value != null && value.length > 500) return 'Bio must be under 500 characters';
    return null;
  }

  static String? latitude(String? value) {
    if (value == null || value.isEmpty) return null;
    final lat = double.tryParse(value);
    if (lat == null || lat < -90 || lat > 90) return 'Invalid latitude';
    return null;
  }

  static String? longitude(String? value) {
    if (value == null || value.isEmpty) return null;
    final lng = double.tryParse(value);
    if (lng == null || lng < -180 || lng > 180) return 'Invalid longitude';
    return null;
  }
}
