import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../config/api_config.dart';
import '../core/api/api_client.dart';
import '../models/match_result.dart';
import 'auth_provider.dart';

/// Manages AI matching results: incoming, sent, dismiss.
class MatchingProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient();
  // ignore: unused_field
  AuthProvider? _auth;

  void updateAuth(AuthProvider auth) => _auth = auth;

  List<MatchResult> _matches = [];
  List<MatchResult> _sentMatches = [];
  bool _isLoading = false;
  String? _error;

  List<MatchResult> get matches => _matches;
  List<MatchResult> get sentMatches => _sentMatches;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// Fetch incoming match suggestions.
  Future<void> fetchMatches() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _api.get(ApiConfig.matches);
      final results =
          (response.data['results'] ?? response.data['data'] ?? []) as List;
      _matches = results
          .map((m) => MatchResult.fromJson(m as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
    }

    _isLoading = false;
    notifyListeners();
  }

  /// Fetch matches generated from my statuses.
  Future<void> fetchSentMatches() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _api.get(ApiConfig.matchesSent);
      final results =
          (response.data['results'] ?? response.data['data'] ?? []) as List;
      _sentMatches = results
          .map((m) => MatchResult.fromJson(m as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
    }

    _isLoading = false;
    notifyListeners();
  }

  /// Dismiss a match.
  Future<bool> dismissMatch(String matchId) async {
    try {
      await _api.post(ApiConfig.matchDismiss(matchId));
      _matches.removeWhere((m) => m.id == matchId);
      notifyListeners();
      return true;
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
      notifyListeners();
      return false;
    }
  }
}
