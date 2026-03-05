import 'user.dart';

/// Profile model matching the Django Profile serializer.
class Profile {
  final String id;
  final User user;
  final String displayName;
  final String bio;
  final String? avatarUrl;
  final List<String> skills;
  final List<String> interests;
  final List<String> tags;
  final bool isPublic;
  final bool liveTrackingEnabled;
  final bool isOnline;
  final DateTime? lastSeen;
  final bool shouldObfuscateLocation;
  final DateTime createdAt;
  final DateTime updatedAt;

  const Profile({
    required this.id,
    required this.user,
    this.displayName = '',
    this.bio = '',
    this.avatarUrl,
    this.skills = const [],
    this.interests = const [],
    this.tags = const [],
    this.isPublic = false,
    this.liveTrackingEnabled = false,
    this.isOnline = false,
    this.lastSeen,
    this.shouldObfuscateLocation = true,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Profile.fromJson(Map<String, dynamic> json) {
    return Profile(
      id: json['id'] as String,
      user: User.fromRef(json['user'] as Map<String, dynamic>),
      displayName: json['display_name'] as String? ?? '',
      bio: json['bio'] as String? ?? '',
      avatarUrl: json['avatar'] as String?,
      skills: _parseStringList(json['skills']),
      interests: _parseStringList(json['interests']),
      tags: _parseStringList(json['tags']),
      isPublic: json['is_public'] as bool? ?? false,
      liveTrackingEnabled: json['live_tracking_enabled'] as bool? ?? false,
      isOnline: json['is_online'] as bool? ?? false,
      lastSeen: json['last_seen'] != null
          ? DateTime.parse(json['last_seen'] as String)
          : null,
      shouldObfuscateLocation:
          json['should_obfuscate_location'] as bool? ?? true,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  /// Public profile with a subset of fields.
  factory Profile.fromPublicJson(Map<String, dynamic> json) {
    return Profile(
      id: json['id'] as String,
      user: User.fromRef(json['user'] as Map<String, dynamic>),
      displayName: json['display_name'] as String? ?? '',
      bio: json['bio'] as String? ?? '',
      avatarUrl: json['avatar'] as String?,
      skills: _parseStringList(json['skills']),
      interests: _parseStringList(json['interests']),
      tags: _parseStringList(json['tags']),
      isPublic: json['is_public'] as bool? ?? false,
      isOnline: json['is_online'] as bool? ?? false,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );
  }

  static List<String> _parseStringList(dynamic value) {
    if (value == null) return [];
    if (value is List) return value.map((e) => e.toString()).toList();
    return [];
  }

  String get effectiveName =>
      displayName.isNotEmpty ? displayName : user.fullName;
}
