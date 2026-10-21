import 'package:http/http.dart' as http;
import 'dart:convert';
import 'config.dart';
import 'models.dart';

class ApiException implements Exception {
  final String message;

  ApiException(this.message);

  @override
  String toString() => message;
}

class ApiClient {
  final String baseUrl;
  final Duration timeout;

  ApiClient({
    String? baseUrl,
    this.timeout = const Duration(seconds: 60),
  }) : baseUrl = baseUrl ?? Config.apiUrl;

  Future<StoriesResponse> getStories() async {
    try {
      final response = await http
          .get(
            Uri.parse('$baseUrl/stories'),
          )
          .timeout(timeout, onTimeout: () {
        throw ApiException('Request timed out. The server may be waking up...');
      });

      if (response.statusCode == 200) {
        return StoriesResponse.fromJson(
          json.decode(response.body) as Map<String, dynamic>,
        );
      } else {
        throw ApiException(
          'Failed to load stories (HTTP ${response.statusCode})',
        );
      }
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException('Failed to connect to server: $e');
    }
  }

  Future<StoryDetail> getStory(int id) async {
    try {
      final response = await http
          .get(
            Uri.parse('$baseUrl/stories/$id'),
          )
          .timeout(timeout, onTimeout: () {
        throw ApiException('Request timed out. The server may be waking up...');
      });

      if (response.statusCode == 200) {
        return StoryDetail.fromJson(
          json.decode(response.body) as Map<String, dynamic>,
        );
      } else if (response.statusCode == 404) {
        throw ApiException('Story not found or has expired');
      } else {
        throw ApiException(
          'Failed to load story (HTTP ${response.statusCode})',
        );
      }
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException('Failed to connect to server: $e');
    }
  }

  Future<Status> getStatus() async {
    try {
      final response = await http
          .get(
            Uri.parse('$baseUrl/status'),
          )
          .timeout(timeout, onTimeout: () {
        throw ApiException('Request timed out. The server may be waking up...');
      });

      if (response.statusCode == 200) {
        return Status.fromJson(
          json.decode(response.body) as Map<String, dynamic>,
        );
      } else {
        throw ApiException(
          'Failed to load status (HTTP ${response.statusCode})',
        );
      }
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException('Failed to connect to server: $e');
    }
  }
}
