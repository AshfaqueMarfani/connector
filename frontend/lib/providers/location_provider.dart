import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart';

import '../config/api_config.dart';
import '../core/api/api_client.dart';
import '../models/location.dart';
import 'auth_provider.dart';

/// Manages device location, GPS permissions, nearby search.
class LocationProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient();
  AuthProvider? _auth;

  void updateAuth(AuthProvider auth) => _auth = auth;

  UserLocation? _myLocation;
  List<NearbyUser> _nearbyUsers = [];
  bool _isLoading = false;
  String? _error;
  int _totalNearby = 0;
  int _searchRadius = 500;

  UserLocation? get myLocation => _myLocation;
  List<NearbyUser> get nearbyUsers => _nearbyUsers;
  bool get isLoading => _isLoading;
  String? get error => _error;
  int get totalNearby => _totalNearby;
  int get searchRadius => _searchRadius;

  set searchRadius(int value) {
    _searchRadius = value;
    notifyListeners();
  }

  /// Check and request location permissions.
  Future<bool> checkPermissions() async {
    final serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      _error = 'Location services are disabled. Please enable them.';
      notifyListeners();
      return false;
    }

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        _error = 'Location permission was denied.';
        notifyListeners();
        return false;
      }
    }

    if (permission == LocationPermission.deniedForever) {
      _error = 'Location permissions are permanently denied.';
      notifyListeners();
      return false;
    }

    return true;
  }

  /// Get current device position and send to backend.
  Future<bool> updateLocation() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final hasPermission = await checkPermissions();
      if (!hasPermission) {
        _isLoading = false;
        notifyListeners();
        return false;
      }

      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );

      final response = await _api.post(ApiConfig.locationUpdate, data: {
        'latitude': position.latitude,
        'longitude': position.longitude,
        'source': 'gps',
        'accuracy': position.accuracy,
        'altitude': position.altitude,
        'heading': position.heading,
        'speed': position.speed,
        'is_background': false,
      });

      _myLocation =
          UserLocation.fromJson(response.data['data'] ?? response.data);
      _isLoading = false;
      notifyListeners();
      return true;
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
      _isLoading = false;
      notifyListeners();
      return false;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  /// Fetch my current stored location.
  Future<void> fetchMyLocation() async {
    try {
      final response = await _api.get(ApiConfig.locationMe);
      _myLocation =
          UserLocation.fromJson(response.data['data'] ?? response.data);
      notifyListeners();
    } on DioException {
      // Location not set yet — not an error
    }
  }

  /// Search for nearby users with optional filters.
  Future<void> searchNearby({
    int? radius,
    String? type,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final queryParams = <String, dynamic>{
        'radius': radius ?? _searchRadius,
      };
      if (type != null && type.isNotEmpty) {
        queryParams['type'] = type;
      }

      final response = await _api.get(
        ApiConfig.exploreNearby,
        queryParameters: queryParams,
      );

      final data = response.data['data'] ?? response.data;
      _totalNearby = data['total_results'] as int? ?? 0;
      _searchRadius = data['radius_meters'] as int? ?? _searchRadius;

      final results = data['results'] as List? ?? [];
      _nearbyUsers =
          results.map((r) => NearbyUser.fromJson(r as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      _error = ApiException.fromDioError(e).message;
    }

    _isLoading = false;
    notifyListeners();
  }
}
