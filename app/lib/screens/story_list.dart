import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../api.dart';
import '../models.dart';
import 'story_detail.dart';

class StoryListScreen extends StatefulWidget {
  const StoryListScreen({super.key});

  @override
  State<StoryListScreen> createState() => _StoryListScreenState();
}

class _StoryListScreenState extends State<StoryListScreen> {
  late ApiClient _apiClient;
  late Future<StoriesResponse> _storiesFuture;
  late Future<Status> _statusFuture;
  String? _lastUpdateTime;

  @override
  void initState() {
    super.initState();
    _apiClient = ApiClient();
    _loadData();
  }

  void _loadData() {
    setState(() {
      _storiesFuture = _apiClient.getStories();
      _statusFuture = _apiClient.getStatus().then((status) {
        if (status.lastSuccessfulTime != null) {
          _lastUpdateTime = DateFormat('MMM d, yyyy h:mm a').format(status.lastSuccessfulTime!);
        }
        return status;
      });
    });
  }

  Future<void> _onRefresh() async {
    _loadData();
    await _storiesFuture;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My News'),
        elevation: 2,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _onRefresh,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: FutureBuilder<Status>(
        future: _statusFuture,
        builder: (context, statusSnapshot) {
          return FutureBuilder<StoriesResponse>(
            future: _storiesFuture,
            builder: (context, storiesSnapshot) {
              // Loading state
              if (storiesSnapshot.connectionState == ConnectionState.waiting &&
                  statusSnapshot.connectionState == ConnectionState.waiting) {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const CircularProgressIndicator(),
                      const SizedBox(height: 16),
                      const Text(
                        'Loading stories...',
                        style: TextStyle(fontSize: 16),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Waking up server...',
                        style: TextStyle(fontSize: 14, color: Colors.grey),
                      ),
                    ],
                  ),
                );
              }

              // Error state
              if (storiesSnapshot.hasError) {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline, size: 48, color: Colors.red),
                      const SizedBox(height: 16),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 24),
                        child: Text(
                          storiesSnapshot.error.toString(),
                          textAlign: TextAlign.center,
                          style: const TextStyle(fontSize: 16),
                        ),
                      ),
                      const SizedBox(height: 24),
                      ElevatedButton.icon(
                        onPressed: _onRefresh,
                        icon: const Icon(Icons.refresh),
                        label: const Text('Retry'),
                      ),
                    ],
                  ),
                );
              }

              // Empty state
              if (storiesSnapshot.hasData && storiesSnapshot.data!.stories.isEmpty) {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.newspaper, size: 48, color: Colors.grey),
                      const SizedBox(height: 16),
                      const Text(
                        'No stories yet',
                        style: TextStyle(fontSize: 18),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Check back later for news updates',
                        style: TextStyle(fontSize: 14, color: Colors.grey),
                      ),
                      const SizedBox(height: 24),
                      ElevatedButton.icon(
                        onPressed: _onRefresh,
                        icon: const Icon(Icons.refresh),
                        label: const Text('Refresh'),
                      ),
                    ],
                  ),
                );
              }

              // Success state
              final stories = storiesSnapshot.data?.stories ?? [];

              return RefreshIndicator(
                onRefresh: _onRefresh,
                child: SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (_lastUpdateTime != null)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 16),
                            child: Text(
                              'Updated $_lastUpdateTime',
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ),
                        ...stories.map((story) => _buildStoryCard(context, story)),
                      ],
                    ),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }

  Widget _buildStoryCard(BuildContext context, Story story) {
    final formattedTime = DateFormat('MMM d, h:mm a').format(story.latestArticleAt);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: () {
          // Navigate to story detail
          Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => StoryDetailScreen(storyId: story.id),
            ),
          );
        },
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                story.headline,
                style: Theme.of(context).textTheme.titleLarge,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '${story.publisherCount} publishers',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  Text(
                    formattedTime,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
