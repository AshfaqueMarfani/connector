/// User model matching the Django User serializer.
class User {
  final String id;
  final String email;
  final String fullName;
  final String accountType;
  final String accountTypeDisplay;
  final bool isActive;
  final DateTime dateJoined;

  const User({
    required this.id,
    required this.email,
    required this.fullName,
    required this.accountType,
    this.accountTypeDisplay = '',
    this.isActive = true,
    required this.dateJoined,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as String,
      email: json['email'] as String? ?? '',
      fullName: json['full_name'] as String? ?? '',
      accountType: json['account_type'] as String? ?? 'individual',
      accountTypeDisplay: json['account_type_display'] as String? ?? '',
      isActive: json['is_active'] as bool? ?? true,
      dateJoined: DateTime.parse(
          json['date_joined'] as String? ?? DateTime.now().toIso8601String()),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'full_name': fullName,
        'account_type': accountType,
      };

  /// Lightweight user reference from nested serializers
  factory User.fromRef(Map<String, dynamic> json) {
    return User(
      id: json['id'] as String,
      email: json['email'] as String? ?? '',
      fullName: json['full_name'] as String? ?? '',
      accountType: json['account_type'] as String? ?? 'individual',
      dateJoined: DateTime.now(),
    );
  }
}
