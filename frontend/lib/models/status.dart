import 'user.dart';

/// Status (need/offer broadcast) model.
class Status {
  final String id;
  final User user;
  final String statusType;
  final String text;
  final String urgency;
  final String aiParsedIntent;
  final List<String> aiTags;
  final bool isActive;
  final DateTime? expiresAt;
  final DateTime createdAt;
  final DateTime updatedAt;

  const Status({
    required this.id,
    required this.user,
    required this.statusType,
    required this.text,
    required this.urgency,
    this.aiParsedIntent = '',
    this.aiTags = const [],
    this.isActive = true,
    this.expiresAt,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Status.fromJson(Map<String, dynamic> json) {
    return Status(
      id: json['id'] as String,
      user: User.fromRef(json['user'] as Map<String, dynamic>),
      statusType: json['status_type'] as String,
      text: json['text'] as String,
      urgency: json['urgency'] as String? ?? 'low',
      aiParsedIntent: json['ai_parsed_intent'] as String? ?? '',
      aiTags: (json['ai_tags'] as List?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      isActive: json['is_active'] as bool? ?? true,
      expiresAt: json['expires_at'] != null
          ? DateTime.parse(json['expires_at'] as String)
          : null,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  bool get isNeed => statusType == 'need';
  bool get isOffer => statusType == 'offer';
}
