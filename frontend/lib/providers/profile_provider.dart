import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../config/api_config.dart';
import '../core/api/api_client.dart';
import '../models/profile.dart';
import 'auth_provider.dart';

/// Manages user profile data: fetch, update, view other profiles.
class ProfileProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient();
  AuthProvider? _auth;

  void updateAuth(AuthProvider auth) => _auth = auth;

  Profile? _myProfile;
  Profile? _viewedProfile;
  bool _isLoading = false;
  String? _error;

  Profile? get myProfile => _myProfile;
  Profile? get viewedProfile => _viewedProfile;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// Fetch the authenticated user's own profile.
  Future<void> fetchMyProfile() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _api.get(ApiConfig.profileMe);
      _myProfile = Profile.fromJson(response.data['data'] ?? response.data);
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
    }

    _isLoading = false;
    notifyListeners();
  }

  /// Update my profile with partial data.
  Future<bool> updateProfile({
    String? displayName,
    String? bio,
    List<String>? skills,
    List<String>? interests,
    bool? isPublic,
    bool? liveTrackingEnabled,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final data = <String, dynamic>{};
      if (displayName != null) data['display_name'] = displayName;
      if (bio != null) data['bio'] = bio;
      if (skills != null) data['skills'] = skills;
      if (interests != null) data['interests'] = interests;
      if (isPublic != null) data['is_public'] = isPublic;
      if (liveTrackingEnabled != null) {
        data['live_tracking_enabled'] = liveTrackingEnabled;
      }

      final response = await _api.patch(ApiConfig.profileMe, data: data);
      _myProfile = Profile.fromJson(response.data['data'] ?? response.data);
      _isLoading = false;
      notifyListeners();
      return true;
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  /// Upload a new avatar image.
  Future<bool> uploadAvatar(String filePath) async {
    _isLoading = true;
    notifyListeners();

    try {
      final formData = FormData.fromMap({
        'avatar': await MultipartFile.fromFile(filePath),
      });
      final response = await _api.upload(ApiConfig.profileMe, formData: formData);
      _myProfile = Profile.fromJson(response.data['data'] ?? response.data);
      _isLoading = false;
      notifyListeners();
      return true;
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  /// Fetch another user's public profile.
  Future<void> fetchPublicProfile(String userId) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _api.get(ApiConfig.profileDetail(userId));
      _viewedProfile =
          Profile.fromPublicJson(response.data['data'] ?? response.data);
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
    }

    _isLoading = false;
    notifyListeners();
  }

  /// Trigger AI tag generation for my profile.
  Future<bool> generateAiTags() async {
    try {
      await _api.post(ApiConfig.aiGenerateTags);
      return true;
    } on DioException {
      return false;
    }
  }

  void clearViewedProfile() {
    _viewedProfile = null;
    notifyListeners();
  }
}
