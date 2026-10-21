import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models.dart';

class PerspectiveScreen extends StatelessWidget {
  final Perspective perspective;
  final List<Perspective> allPerspectives;
  final Summary summary;
  final List<Article> allArticles;

  const PerspectiveScreen({
    super.key,
    required this.perspective,
    required this.allPerspectives,
    required this.summary,
    required this.allArticles,
  });

  Future<void> _openUrl(String url, BuildContext context) async {
    try {
      final uri = Uri.parse(url);
      if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Could not open link')),
          );
        }
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not open link')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final otherPerspectives = allPerspectives
        .where((p) => p.name != perspective.name)
        .toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Perspective'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Chip(
                label: Text('AI-generated | ${perspective.name}'),
                backgroundColor: Colors.grey[200],
              ),
              const SizedBox(height: 24),
              Card(
                color: Colors.blue[50],
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Text(
                    perspective.summary,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Text(
                'Supporting coverage',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              ...List.generate(perspective.citedArticles.length, (index) {
                final citedArticle = perspective.citedArticles[index];
                return Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Card(
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Row(
                        children: [
                          Chip(
                            label: Text('[${index + 1}]'),
                            backgroundColor: Colors.grey[300],
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  citedArticle.title,
                                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                        fontWeight: FontWeight.bold,
                                      ),
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  citedArticle.publisher,
                                  style: Theme.of(context).textTheme.labelSmall,
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 8),
                          ElevatedButton(
                            onPressed: () => _openUrl(citedArticle.url, context),
                            child: const Text('Open'),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              }),
              const SizedBox(height: 24),
              if (otherPerspectives.isNotEmpty) ...[
                Text(
                  'Other perspectives',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                ...otherPerspectives.map((otherPerspective) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: () {
                          Navigator.pushReplacement(
                            context,
                            MaterialPageRoute(
                              builder: (_) => PerspectiveScreen(
                                perspective: otherPerspective,
                                allPerspectives: allPerspectives,
                                summary: summary,
                                allArticles: allArticles,
                              ),
                            ),
                          );
                        },
                        child: Text(otherPerspective.name),
                      ),
                    ),
                  );
                }),
              ],
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}
