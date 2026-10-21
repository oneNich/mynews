class Story {
  final int id;
  final String headline;
  final DateTime latestArticleAt;
  final int publisherCount;
  final int articleCount;
  final String? summaryStatus;

  Story({
    required this.id,
    required this.headline,
    required this.latestArticleAt,
    required this.publisherCount,
    required this.articleCount,
    this.summaryStatus,
  });

  factory Story.fromJson(Map<String, dynamic> json) {
    return Story(
      id: json['id'] as int,
      headline: json['headline'] as String,
      latestArticleAt: DateTime.parse(json['latest_article_at'] as String),
      publisherCount: json['publisher_count'] as int,
      articleCount: json['article_count'] as int,
      summaryStatus: json['summary_status'] as String?,
    );
  }
}

class Article {
  final String title;
  final String url;
  final DateTime publishedAt;
  final String? excerpt;

  Article({
    required this.title,
    required this.url,
    required this.publishedAt,
    this.excerpt,
  });

  factory Article.fromJson(Map<String, dynamic> json) {
    return Article(
      title: json['title'] as String,
      url: json['url'] as String,
      publishedAt: DateTime.parse(json['published_at'] as String),
      excerpt: json['excerpt'] as String?,
    );
  }
}

class PublisherCoverage {
  final String publisher;
  final List<Article> articles;

  PublisherCoverage({
    required this.publisher,
    required this.articles,
  });

  factory PublisherCoverage.fromJson(Map<String, dynamic> json) {
    return PublisherCoverage(
      publisher: json['publisher'] as String,
      articles: (json['articles'] as List<dynamic>)
          .map((article) => Article.fromJson(article as Map<String, dynamic>))
          .toList(),
    );
  }
}

class BackgroundLink {
  final String title;
  final String url;
  final String source;

  BackgroundLink({
    required this.title,
    required this.url,
    required this.source,
  });

  factory BackgroundLink.fromJson(Map<String, dynamic> json) {
    return BackgroundLink(
      title: json['title'] as String,
      url: json['url'] as String,
      source: json['source'] as String,
    );
  }
}

class CitedArticle {
  final String title;
  final String publisher;
  final String url;

  CitedArticle({
    required this.title,
    required this.publisher,
    required this.url,
  });

  factory CitedArticle.fromJson(Map<String, dynamic> json) {
    return CitedArticle(
      title: json['title'] as String,
      publisher: json['publisher'] as String,
      url: json['url'] as String,
    );
  }
}

class Perspective {
  final String name;
  final String summary;
  final List<CitedArticle> citedArticles;

  Perspective({
    required this.name,
    required this.summary,
    required this.citedArticles,
  });

  factory Perspective.fromJson(Map<String, dynamic> json) {
    return Perspective(
      name: json['name'] as String,
      summary: json['summary'] as String,
      citedArticles: (json['cited_articles'] as List<dynamic>?)
              ?.map((article) => CitedArticle.fromJson(article as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}

class Summary {
  final String status;
  final String? label;
  final DateTime? generatedAt;
  final String? model;
  final String? inputScope;
  final String? overview;
  final String? agreement;
  final String? uncertainty;
  final List<Perspective>? perspectives;
  final bool? insufficientEvidence;

  Summary({
    required this.status,
    this.label,
    this.generatedAt,
    this.model,
    this.inputScope,
    this.overview,
    this.agreement,
    this.uncertainty,
    this.perspectives,
    this.insufficientEvidence,
  });

  factory Summary.fromJson(Map<String, dynamic> json) {
    return Summary(
      status: json['status'] as String,
      label: json['label'] as String?,
      generatedAt: json['generated_at'] != null ? DateTime.parse(json['generated_at'] as String) : null,
      model: json['model'] as String?,
      inputScope: json['input_scope'] as String?,
      overview: json['overview'] as String?,
      agreement: json['agreement'] as String?,
      uncertainty: json['uncertainty'] as String?,
      perspectives: (json['perspectives'] as List<dynamic>?)
          ?.map((p) => Perspective.fromJson(p as Map<String, dynamic>))
          .toList(),
      insufficientEvidence: json['insufficient_evidence'] as bool?,
    );
  }
}

class StoryDetail {
  final int id;
  final String headline;
  final DateTime updatedAt;
  final List<PublisherCoverage> publishers;
  final List<BackgroundLink> backgroundLinks;
  final Summary? summary;

  StoryDetail({
    required this.id,
    required this.headline,
    required this.updatedAt,
    required this.publishers,
    required this.backgroundLinks,
    this.summary,
  });

  factory StoryDetail.fromJson(Map<String, dynamic> json) {
    return StoryDetail(
      id: json['id'] as int,
      headline: json['headline'] as String,
      updatedAt: DateTime.parse(json['updated_at'] as String),
      publishers: (json['publishers'] as List<dynamic>)
          .map((p) => PublisherCoverage.fromJson(p as Map<String, dynamic>))
          .toList(),
      backgroundLinks: (json['background_links'] as List<dynamic>)
          .map((link) => BackgroundLink.fromJson(link as Map<String, dynamic>))
          .toList(),
      summary: json['summary'] != null ? Summary.fromJson(json['summary'] as Map<String, dynamic>) : null,
    );
  }
}

class Status {
  final DateTime? lastSuccessfulTime;
  final String? lastRunStatus;
  final List<JobRun> last5JobRuns;

  Status({
    this.lastSuccessfulTime,
    this.lastRunStatus,
    required this.last5JobRuns,
  });

  factory Status.fromJson(Map<String, dynamic> json) {
    return Status(
      lastSuccessfulTime: json['last_successful_time'] != null ? DateTime.parse(json['last_successful_time'] as String) : null,
      lastRunStatus: json['last_run_status'] as String?,
      last5JobRuns: (json['last_5_job_runs'] as List<dynamic>)
          .map((run) => JobRun.fromJson(run as Map<String, dynamic>))
          .toList(),
    );
  }
}

class JobRun {
  final DateTime startedAt;
  final String status;
  final String trigger;
  final int articlesNew;
  final int articlesExpired;
  final int aiCalls;

  JobRun({
    required this.startedAt,
    required this.status,
    required this.trigger,
    required this.articlesNew,
    required this.articlesExpired,
    required this.aiCalls,
  });

  factory JobRun.fromJson(Map<String, dynamic> json) {
    return JobRun(
      startedAt: DateTime.parse(json['started_at'] as String),
      status: json['status'] as String,
      trigger: json['trigger'] as String,
      articlesNew: json['articles_new'] as int,
      articlesExpired: json['articles_expired'] as int,
      aiCalls: json['ai_calls'] as int,
    );
  }
}

class StoriesResponse {
  final List<Story> stories;

  StoriesResponse({required this.stories});

  factory StoriesResponse.fromJson(Map<String, dynamic> json) {
    return StoriesResponse(
      stories: (json['stories'] as List<dynamic>)
          .map((story) => Story.fromJson(story as Map<String, dynamic>))
          .toList(),
    );
  }
}
