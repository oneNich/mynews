import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import '../api.dart';
import '../models.dart';
import 'ai_analysis.dart';

class StoryDetailScreen extends StatefulWidget {
  final int storyId;

  const StoryDetailScreen({
    super.key,
    required this.storyId,
  });

  @override
  State<StoryDetailScreen> createState() => _StoryDetailScreenState();
}

class _StoryDetailScreenState extends State<StoryDetailScreen> {
  late ApiClient _apiClient;
  late Future<StoryDetail> _storyFuture;

  @override
  void initState() {
    super.initState();
    _apiClient = ApiClient();
    _storyFuture = _apiClient.getStory(widget.storyId);
  }

  Future<void> _openUrl(String url) async {
    try {
      final uri = Uri.parse(url);
      if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Could not open link')),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not open link')),
        );
      }
    }
  }

  List<Article> _getAllArticles(List<PublisherCoverage> publishers) {
    final articles = <Article>[];
    for (final publisher in publishers) {
      articles.addAll(publisher.articles);
    }
    return articles;
  }

  void _showArticlesBottomSheet(BuildContext context, String publisher, List<Article> articles) {
    showModalBottomSheet(
      context: context,
      builder: (context) {
        return DraggableScrollableSheet(
          expand: false,
          builder: (context, scrollController) {
            return ListView.builder(
              controller: scrollController,
              itemCount: articles.length,
              itemBuilder: (context, index) {
                final article = articles[index];
                return ListTile(
                  title: Text(article.title),
                  subtitle: Text(
                    DateFormat('MMM d, h:mm a').format(article.publishedAt),
                  ),
                  onTap: () {
                    Navigator.pop(context);
                    _openUrl(article.url);
                  },
                );
              },
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Story Details'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: FutureBuilder<StoryDetail>(
        future: _storyFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text('Loading story...'),
                ],
              ),
            );
          }

          if (snapshot.hasError) {
            final error = snapshot.error;
            if (error is ApiException && error.cachedData != null) {
              final story = error.cachedData as StoryDetail;
              final cacheTime = error.cacheTime;
              final formattedCacheTime = cacheTime != null
                  ? DateFormat('MMM d, yyyy h:mm a').format(cacheTime)
                  : 'Unknown time';
              final formattedTime = DateFormat('MMM d, yyyy h:mm a').format(story.updatedAt);

              return Stack(
                children: [
                  SingleChildScrollView(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            story.headline,
                            style: Theme.of(context).textTheme.headlineSmall,
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Updated $formattedTime',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                          const SizedBox(height: 24),
                          if (story.summary != null) ...[
                            Text(
                              'Story overview',
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                            const SizedBox(height: 8),
                            _buildSummarySection(context, story.summary!),
                            const SizedBox(height: 24),
                          ],
                          Text(
                            'Original coverage',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: 8),
                          _buildOriginalCoverageSection(context, story.publishers),
                          const SizedBox(height: 24),
                          Text(
                            'Background',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: 8),
                          _buildBackgroundSection(context, story.backgroundLinks),
                          const SizedBox(height: 24),
                        ],
                      ),
                    ),
                  ),
                  Positioned(
                    top: 0,
                    left: 0,
                    right: 0,
                    child: Container(
                      color: Colors.orange[100],
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      'Offline - showing data from $formattedCacheTime',
                                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      'Publisher and background links need a connection',
                                      style: Theme.of(context).textTheme.bodySmall,
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(width: 8),
                              ElevatedButton(
                                onPressed: () {
                                  setState(() {
                                    _storyFuture = _apiClient.getStory(widget.storyId);
                                  });
                                },
                                child: const Text('Retry'),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              );
            }

            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 48, color: Colors.red),
                  const SizedBox(height: 16),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    child: Text(
                      snapshot.error.toString(),
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 16),
                    ),
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton.icon(
                    onPressed: () {
                      setState(() {
                        _storyFuture = _apiClient.getStory(widget.storyId);
                      });
                    },
                    icon: const Icon(Icons.refresh),
                    label: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          final story = snapshot.data!;
          final formattedTime = DateFormat('MMM d, yyyy h:mm a').format(story.updatedAt);

          return SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    story.headline,
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Updated $formattedTime',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  const SizedBox(height: 24),
                  if (story.summary != null) ...[
                    Text(
                      'Story overview',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    _buildSummarySection(context, story.summary!),
                    const SizedBox(height: 24),
                  ],
                  Text(
                    'Original coverage',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  _buildOriginalCoverageSection(context, story.publishers),
                  const SizedBox(height: 24),
                  Text(
                    'Background',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  _buildBackgroundSection(context, story.backgroundLinks),
                  const SizedBox(height: 24),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () {
                        if (story.summary != null) {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => AIAnalysisScreen(
                                summary: story.summary!,
                                allArticles: _getAllArticles(story.publishers),
                                storyHeadline: story.headline,
                              ),
                            ),
                          );
                        }
                      },
                      child: const Text('AI analysis'),
                    ),
                  ),
                  const SizedBox(height: 16),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildSummarySection(BuildContext context, Summary summary) {
    if (summary.status == 'pending') {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              const SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
              const SizedBox(height: 8),
              Text(
                'AI summary is being prepared',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ],
          ),
        ),
      );
    }

    if (summary.status == 'failed') {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text(
            'AI summary unavailable right now',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  summary.overview ?? '',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'AI-generated',
              style: Theme.of(context).textTheme.labelSmall,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOriginalCoverageSection(BuildContext context, List<PublisherCoverage> publishers) {
    return Column(
      children: publishers.map((publisher) {
        if (publisher.articles.length == 1) {
          final article = publisher.articles[0];
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => _openUrl(article.url),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(publisher.publisher),
                    const SizedBox(height: 4),
                    Text(
                      article.title,
                      style: Theme.of(context).textTheme.labelSmall,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
            ),
          );
        } else {
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => _showArticlesBottomSheet(context, publisher.publisher, publisher.articles),
                child: Text('${publisher.publisher} (${publisher.articles.length} articles)'),
              ),
            ),
          );
        }
      }).toList(),
    );
  }

  Widget _buildBackgroundSection(BuildContext context, List<BackgroundLink> links) {
    if (links.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text(
            'No background resource available',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ),
      );
    }

    return Column(
      children: links.map((link) {
        return Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => _openUrl(link.url),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(link.title),
                  const SizedBox(height: 4),
                  Text(
                    link.source,
                    style: Theme.of(context).textTheme.labelSmall,
                  ),
                ],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}
