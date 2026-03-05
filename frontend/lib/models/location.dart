/// User location data from the API.
class UserLocation {
  final double latitude;
  final double longitude;
  final double? obfuscatedLatitude;
  final double? obfuscatedLongitude;
  final String source;
  final double? accuracyMeters;
  final double? altitude;
  final double? heading;
  final double? speed;
  final bool isBackgroundTracking;
  final DateTime updatedAt;

  const UserLocation({
    required this.latitude,
    required this.longitude,
    this.obfuscatedLatitude,
    this.obfuscatedLongitude,
    this.source = 'gps',
    this.accuracyMeters,
    this.altitude,
    this.heading,
    this.speed,
    this.isBackgroundTracking = false,
    required this.updatedAt,
  });

  factory UserLocation.fromJson(Map<String, dynamic> json) {
    return UserLocation(
      latitude: (json['exact_latitude'] ?? json['latitude'] ?? 0).toDouble(),
      longitude: (json['exact_longitude'] ?? json['longitude'] ?? 0).toDouble(),
      obfuscatedLatitude:
          (json['obfuscated_latitude'] as num?)?.toDouble(),
      obfuscatedLongitude:
          (json['obfuscated_longitude'] as num?)?.toDouble(),
      source: json['source'] as String? ?? 'gps',
      accuracyMeters: (json['accuracy_meters'] as num?)?.toDouble(),
      altitude: (json['altitude'] as num?)?.toDouble(),
      heading: (json['heading'] as num?)?.toDouble(),
      speed: (json['speed'] as num?)?.toDouble(),
      isBackgroundTracking: json['is_background_tracking'] as bool? ?? false,
      updatedAt: DateTime.parse(
          json['updated_at'] as String? ?? DateTime.now().toIso8601String()),
    );
  }
}

/// Nearby user result from the explore endpoint.
class NearbyUser {
  final Map<String, dynamic> profileData;
  final double latitude;
  final double longitude;
  final bool isExact;
  final String source;
  final double? accuracyMeters;
  final DateTime? updatedAt;
  final double distanceMeters;

  const NearbyUser({
    required this.profileData,
    required this.latitude,
    required this.longitude,
    required this.isExact,
    this.source = '',
    this.accuracyMeters,
    this.updatedAt,
    required this.distanceMeters,
  });

  factory NearbyUser.fromJson(Map<String, dynamic> json) {
    final loc = json['location'] as Map<String, dynamic>? ?? {};
    return NearbyUser(
      profileData: json['profile'] as Map<String, dynamic>? ?? {},
      latitude: (loc['latitude'] as num?)?.toDouble() ?? 0,
      longitude: (loc['longitude'] as num?)?.toDouble() ?? 0,
      isExact: loc['is_exact'] as bool? ?? false,
      source: loc['source'] as String? ?? '',
      accuracyMeters: (loc['accuracy_meters'] as num?)?.toDouble(),
      updatedAt: loc['updated_at'] != null
          ? DateTime.parse(loc['updated_at'] as String)
          : null,
      distanceMeters: (json['distance_meters'] as num?)?.toDouble() ?? 0,
    );
  }

  /// The user's account type from profile data.
  String get accountType =>
      (profileData['user'] as Map<String, dynamic>?)?['account_type']
          as String? ??
      'individual';

  String get userId =>
      (profileData['user'] as Map<String, dynamic>?)?['id'] as String? ?? '';

  String get displayName =>
      profileData['display_name'] as String? ??
      (profileData['user'] as Map<String, dynamic>?)?['full_name']
          as String? ??
      'Unknown';
}
