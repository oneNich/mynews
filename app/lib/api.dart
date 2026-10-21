import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'config.dart';
import 'models.dart';

class ApiException implements Exception {
  final String message;
  final dynamic cachedData;
  final DateTime? cacheTime;

  ApiException(
    this.message, {
    this.cachedData,
    this.cacheTime,
  });

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

  Future<void> _cacheStoriesResponse(StoriesResponse data) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('stories_cache', json.encode({
        'data': data.stories.map((s) => {
          'id': s.id,
          'headline': s.headline,
          'latest_article_at': s.latestArticleAt.toIso8601String(),
          'publisher_count': s.publisherCount,
          'article_count': s.articleCount,
          'summary_status': s.summaryStatus,
        }).toList(),
        'sync_time': DateTime.now().toIso8601String(),
      }));
    } catch (_) {}
  }

  Future<(StoriesResponse?, DateTime?)> _loadStoriesCache() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final cachedJson = prefs.getString('stories_cache');
      if (cachedJson != null) {
        final decoded = json.decode(cachedJson) as Map<String, dynamic>;
        final syncTime = DateTime.parse(decoded['sync_time'] as String);
        final stories = (decoded['data'] as List<dynamic>)
            .map((s) => Story.fromJson(s as Map<String, dynamic>))
            .toList();

        final now = DateTime.now();
        final hundredSixtyEightHoursAgo = now.subtract(const Duration(hours: 168));
        stories.removeWhere((s) => s.latestArticleAt.isBefore(hundredSixtyEightHoursAgo));

        if (stories.isNotEmpty) {
          return (StoriesResponse(stories: stories), syncTime);
        }
      }
    } catch (_) {}
    return (null, null);
  }

  Future<void> _cacheStoryResponse(StoryDetail data) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('story_${data.id}_cache', json.encode({
        'data': data,
        'sync_time': DateTime.now().toIso8601String(),
      }));
    } catch (_) {}
  }

  Future<(StoryDetail?, DateTime?)> _loadStoryCache(int id) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final cachedJson = prefs.getString('story_${id}_cache');
      if (cachedJson != null) {
        final decoded = json.decode(cachedJson) as Map<String, dynamic>;
        final syncTime = DateTime.parse(decoded['sync_time'] as String);
        final story = StoryDetail.fromJson(decoded['data'] as Map<String, dynamic>);
        return (story, syncTime);
      }
    } catch (_) {}
    return (null, null);
  }

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
        final data = StoriesResponse.fromJson(
          json.decode(response.body) as Map<String, dynamic>,
        );
        await _cacheStoriesResponse(data);
        return data;
      } else {
        throw ApiException(
          'Failed to load stories (HTTP ${response.statusCode})',
        );
      }
    } on ApiException {
      rethrow;
    } catch (e) {
      final (cachedData, cacheTime) = await _loadStoriesCache();
      if (cachedData != null) {
        throw ApiException(
          'Failed to connect to server: $e',
          cachedData: cachedData,
          cacheTime: cacheTime,
        );
      }
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
        final data = StoryDetail.fromJson(
          json.decode(response.body) as Map<String, dynamic>,
        );
        await _cacheStoryResponse(data);
        return data;
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
      final (cachedData, cacheTime) = await _loadStoryCache(id);
      if (cachedData != null) {
        throw ApiException(
          'Failed to connect to server: $e',
          cachedData: cachedData,
          cacheTime: cacheTime,
        );
      }
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
