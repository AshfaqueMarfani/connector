import 'user.dart';

/// AI Match result model.
class MatchResult {
  final String id;
  final double score;
  final String reason;
  final List<String> matchedTags;
  final double distanceMeters;
  final String matchStatus;
  final DateTime createdAt;
  final MatchStatusDetail? statusDetail;
  final User? matchedUserDetail;
  final User? statusOwnerDetail;

  const MatchResult({
    required this.id,
    required this.score,
    required this.reason,
    this.matchedTags = const [],
    required this.distanceMeters,
    required this.matchStatus,
    required this.createdAt,
    this.statusDetail,
    this.matchedUserDetail,
    this.statusOwnerDetail,
  });

  factory MatchResult.fromJson(Map<String, dynamic> json) {
    return MatchResult(
      id: json['id'] as String,
      score: (json['score'] as num?)?.toDouble() ?? 0,
      reason: json['reason'] as String? ?? '',
      matchedTags: (json['matched_tags'] as List?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      distanceMeters: (json['distance_meters'] as num?)?.toDouble() ?? 0,
      matchStatus: json['match_status'] as String? ?? 'pending',
      createdAt: DateTime.parse(json['created_at'] as String),
      statusDetail: json['status_detail'] != null
          ? MatchStatusDetail.fromJson(
              json['status_detail'] as Map<String, dynamic>)
          : null,
      matchedUserDetail: json['matched_user_detail'] != null
          ? User.fromRef(
              json['matched_user_detail'] as Map<String, dynamic>)
          : null,
      statusOwnerDetail: json['status_owner_detail'] != null
          ? User.fromRef(
              json['status_owner_detail'] as Map<String, dynamic>)
          : null,
    );
  }

  /// Score as percentage string.
  String get scorePercent => '${(score * 100).round()}%';

  /// Formatted distance.
  String get distanceFormatted {
    if (distanceMeters < 1000) {
      return '${distanceMeters.round()}m';
    }
    return '${(distanceMeters / 1000).toStringAsFixed(1)}km';
  }
}

/// Embedded status info in a match result.
class MatchStatusDetail {
  final String id;
  final String statusType;
  final String text;
  final String urgency;
  final List<String> aiTags;

  const MatchStatusDetail({
    required this.id,
    required this.statusType,
    required this.text,
    required this.urgency,
    this.aiTags = const [],
  });

  factory MatchStatusDetail.fromJson(Map<String, dynamic> json) {
    return MatchStatusDetail(
      id: json['id'] as String,
      statusType: json['status_type'] as String,
      text: json['text'] as String,
      urgency: json['urgency'] as String? ?? 'low',
      aiTags: (json['ai_tags'] as List?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
    );
  }
}
