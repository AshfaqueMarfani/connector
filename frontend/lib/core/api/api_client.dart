import 'dart:io';

import 'package:dio/dio.dart';
import 'package:logger/logger.dart';

import '../../config/api_config.dart';
import '../storage/secure_storage.dart';

final _logger = Logger(printer: PrettyPrinter(methodCount: 0));

/// Singleton HTTP client wrapping Dio with JWT auth, token refresh,
/// and standardized error handling.
class ApiClient {
  ApiClient._internal();
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

  late final Dio _dio;
  bool _initialized = false;

  Dio get dio {
    if (!_initialized) _init();
    return _dio;
  }

  void _init() {
    final baseUrl = _platformBaseUrl();
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: ApiConfig.connectTimeout,
      receiveTimeout: ApiConfig.receiveTimeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));

    _dio.interceptors.addAll([
      _AuthInterceptor(),
      _LoggingInterceptor(),
    ]);

    _initialized = true;
  }

  String _platformBaseUrl() {
    try {
      if (Platform.isAndroid) return ApiConfig.baseUrl;
      if (Platform.isIOS) return ApiConfig.iosBaseUrl;
    } catch (_) {
      // Web platform
    }
    return ApiConfig.webBaseUrl;
  }

  // ---- Convenience methods ----

  Future<Response> get(
    String path, {
    Map<String, dynamic>? queryParameters,
  }) =>
      dio.get(path, queryParameters: queryParameters);

  Future<Response> post(
    String path, {
    dynamic data,
  }) =>
      dio.post(path, data: data);

  Future<Response> patch(
    String path, {
    dynamic data,
  }) =>
      dio.patch(path, data: data);

  Future<Response> delete(String path) => dio.delete(path);

  Future<Response> upload(
    String path, {
    required FormData formData,
  }) =>
      dio.post(
        path,
        data: formData,
        options: Options(contentType: 'multipart/form-data'),
      );
}

/// Injects Authorization header and handles 401 → token refresh.
class _AuthInterceptor extends Interceptor {
  bool _isRefreshing = false;

  @override
  void onRequest(
      RequestOptions options, RequestInterceptorHandler handler) async {
    // Skip auth for login/register/refresh
    final noAuth = [
      ApiConfig.login,
      ApiConfig.register,
      ApiConfig.tokenRefresh,
    ];
    if (noAuth.any((path) => options.path.contains(path))) {
      return handler.next(options);
    }

    final token = await SecureStorage.getAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401 && !_isRefreshing) {
      _isRefreshing = true;
      try {
        final refreshToken = await SecureStorage.getRefreshToken();
        if (refreshToken == null) {
          _isRefreshing = false;
          return handler.next(err);
        }

        // Attempt token refresh
        final dio = Dio(BaseOptions(baseUrl: err.requestOptions.baseUrl));
        final response = await dio.post(
          ApiConfig.tokenRefresh,
          data: {'refresh': refreshToken},
        );

        final newAccess = response.data['access'] as String;
        await SecureStorage.setAccessToken(newAccess);

        // Retry the original request with new token
        final opts = err.requestOptions;
        opts.headers['Authorization'] = 'Bearer $newAccess';
        final retryResponse = await dio.fetch(opts);

        _isRefreshing = false;
        return handler.resolve(retryResponse);
      } on DioException {
        _isRefreshing = false;
        // Refresh failed → clear tokens (logout)
        await SecureStorage.clearAll();
        return handler.next(err);
      }
    }
    handler.next(err);
  }
}

/// Logs requests and responses in debug mode.
class _LoggingInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    _logger.d('→ ${options.method} ${options.path}');
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    _logger.d('← ${response.statusCode} ${response.requestOptions.path}');
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    _logger.e('✗ ${err.response?.statusCode} ${err.requestOptions.path}: '
        '${err.response?.data}');
    handler.next(err);
  }
}

/// Parse API error responses into user-friendly messages.
class ApiException implements Exception {
  final String message;
  final int? statusCode;
  final Map<String, dynamic>? errors;

  ApiException({required this.message, this.statusCode, this.errors});

  factory ApiException.fromDioError(DioException error) {
    final data = error.response?.data;
    String message = 'Something went wrong. Please try again.';

    if (data is Map<String, dynamic>) {
      if (data.containsKey('detail')) {
        message = data['detail'].toString();
      } else if (data.containsKey('message')) {
        message = data['message'].toString();
      } else if (data.containsKey('errors')) {
        final errors = data['errors'] as Map<String, dynamic>;
        message = errors.values
            .expand((v) => v is List ? v : [v])
            .map((e) => e.toString())
            .join('\n');
      } else {
        // Field-level errors
        final fieldErrors = <String>[];
        data.forEach((key, value) {
          if (value is List) {
            fieldErrors.addAll(value.map((e) => e.toString()));
          } else if (value is String) {
            fieldErrors.add(value);
          }
        });
        if (fieldErrors.isNotEmpty) {
          message = fieldErrors.join('\n');
        }
      }
    }

    switch (error.response?.statusCode) {
      case 401:
        message = 'Session expired. Please login again.';
        break;
      case 403:
        message = 'You don\'t have permission to do this.';
        break;
      case 404:
        message = 'Not found.';
        break;
      case 429:
        message = 'Too many requests. Please wait a moment.';
        break;
    }

    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout) {
      message = 'Connection timed out. Check your network.';
    } else if (error.type == DioExceptionType.connectionError) {
      message = 'No internet connection.';
    }

    return ApiException(
      message: message,
      statusCode: error.response?.statusCode,
      errors: data is Map<String, dynamic> ? data : null,
    );
  }

  @override
  String toString() => message;
}
