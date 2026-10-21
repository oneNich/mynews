# MyNews API Documentation

## Base URL
```
https://mynews-fdgy.onrender.com
```

## Endpoints

### GET /health
Health check endpoint.

**Response:**
```json
{
  "ok": true
}
```

### GET /status
Get the current status of the news collection system and last 5 job runs.

**Response:**
```json
{
  "last_successful_time": "2026-10-21T20:35:25.717161+00:00",
  "last_run_status": "ok",
  "last_5_job_runs": [
    {
      "started_at": "2026-10-21T20:35:25.717161+00:00",
      "status": "ok",
      "trigger": "scheduled",
      "articles_new": 3,
      "articles_expired": 2,
      "ai_calls": 2
    }
  ]
}
```

**Fields:**
- `last_successful_time` (ISO 8601 UTC): Timestamp of the most recent successful job run, or null if none
- `last_run_status` (string): Status of the most recent job run ("ok", "partial", "failed", or null)
- `last_5_job_runs` (array): Last 5 job runs, newest first

### GET /stories
List all news stories with articles from the past 7 days (168 hours).

**Response:**
```json
{
  "stories": [
    {
      "id": 1,
      "headline": "Election Results Announced",
      "latest_article_at": "2026-10-21T19:35:25+00:00",
      "publisher_count": 3,
      "article_count": 5,
      "summary_status": "ok"
    },
    {
      "id": 2,
      "headline": "Technology Company Announces New Product",
      "latest_article_at": "2026-10-21T15:20:10+00:00",
      "publisher_count": 2,
      "article_count": 3,
      "summary_status": "pending"
    }
  ]
}
```

**Fields:**
- `id` (integer): Unique story identifier
- `headline` (string): Story headline
- `latest_article_at` (ISO 8601 UTC): Publication time of the newest article in this story
- `publisher_count` (integer): Number of distinct publishers covering this story
- `article_count` (integer): Total number of articles in this story
- `summary_status` (string): AI summary status ("ok", "pending", "failed", or null)

**Sorting:** Stories are sorted by `latest_article_at` in descending order (newest first).

### GET /stories/{id}
Get detailed information about a specific story, including all articles, background links, and AI summary.

**Parameters:**
- `id` (integer, path): The story ID

**Response:**
```json
{
  "id": 1,
  "headline": "Election Results Announced",
  "updated_at": "2026-10-21T20:30:00+00:00",
  "publishers": [
    {
      "publisher": "NPR",
      "articles": [
        {
          "title": "Candidate Wins Election",
          "url": "https://npr.org/news/election-results",
          "published_at": "2026-10-21T18:15:00+00:00",
          "excerpt": "The election has concluded with surprising results..."
        }
      ]
    },
    {
      "publisher": "BBC",
      "articles": [
        {
          "title": "Election Outcome Stuns Analysts",
          "url": "https://bbc.com/news/election",
          "published_at": "2026-10-21T19:35:25+00:00",
          "excerpt": "International observers react to the unexpected results..."
        }
      ]
    }
  ],
  "background_links": [
    {
      "title": "Voting System",
      "url": "https://en.wikipedia.org/wiki/Voting_system",
      "source": "Wikipedia"
    }
  ],
  "summary": {
    "status": "ok",
    "label": "AI-generated",
    "generated_at": "2026-10-21T20:00:00+00:00",
    "model": "claude-haiku-5-5",
    "input_scope": "Feed excerpts only",
    "overview": "A surprising election outcome has captured headlines across multiple news outlets. Key facts are widely reported, but outlets differ on the implications.",
    "agreement": "All sources confirm the election results and the candidate's margin of victory.",
    "uncertainty": "Analysts disagree on whether the results represent a shift in voter sentiment or reflect specific campaign dynamics.",
    "perspectives": [
      {
        "name": "Official Response",
        "summary": "Campaign officials attribute the victory to strong voter engagement and issues alignment.",
        "cited_articles": [
          {
            "title": "Candidate Wins Election",
            "publisher": "NPR",
            "url": "https://npr.org/news/election-results"
          }
        ]
      },
      {
        "name": "International Analysis",
        "summary": "International observers note this challenges conventional polling predictions.",
        "cited_articles": [
          {
            "title": "Election Outcome Stuns Analysts",
            "publisher": "BBC",
            "url": "https://bbc.com/news/election"
          }
        ]
      }
    ],
    "insufficient_evidence": false
  }
}
```

**Fields:**
- `id` (integer): Story ID
- `headline` (string): Story headline
- `updated_at` (ISO 8601 UTC): Last update time for this story
- `publishers` (array): Articles grouped by publisher
  - `publisher` (string): Publisher name
  - `articles` (array): Articles from this publisher
    - `title` (string): Article title
    - `url` (string): Article URL
    - `published_at` (ISO 8601 UTC): Publication time
    - `excerpt` (string or null): Article excerpt/summary
- `background_links` (array): Contextual background links
  - `title` (string): Link title (Wikipedia page name, etc.)
  - `url` (string): Link URL
  - `source` (string): Source (e.g., "Wikipedia")
- `summary` (object or null): AI-generated summary
  - `status` (string): "ok", "pending", or "failed"
  - `label` (string): "AI-generated"
  - `generated_at` (ISO 8601 UTC or null): When the summary was generated
  - `model` (string): AI model used (e.g., "claude-haiku-5-5")
  - `input_scope` (string): "Feed excerpts only" - describes what was analyzed
  - `overview` (string or null): High-level summary of the story
  - `agreement` (string or null): What sources agree on
  - `uncertainty` (string or null): Points of disagreement or uncertainty
  - `perspectives` (array or null): Different viewpoints in the coverage
    - `name` (string): Perspective label
    - `summary` (string): What this perspective claims
    - `cited_articles` (array): Articles supporting this perspective
      - `title` (string): Article title
      - `publisher` (string): Publisher name
      - `url` (string): Article URL
  - `insufficient_evidence` (boolean or null): True if summary could not be generated due to insufficient sources
  
  **Note:** When status is "pending" or "failed", all text fields (overview, agreement, uncertainty, perspectives, insufficient_evidence) are null.

**Errors:**
- `404 Not Found`: Story does not exist or has only expired articles (older than 168 hours)

## Data Filtering

- **Expired content**: Articles and stories older than 168 hours (7 days) from publication time are automatically excluded
- **Deduplication**: Articles are deduplicated by normalized URL
- **Time window**: All queries return content published in the last 7 days (168 hours)

## Timestamps

All timestamps are returned as ISO 8601 formatted strings in UTC timezone (e.g., `2026-10-21T20:35:25.717161+00:00`).

## AI Summary Generation

- AI summaries are generated asynchronously by the backend
- Summaries are only generated for stories with articles from multiple publishers
- Summary generation can fail (network, API errors, etc.) - the `status` field will be "failed"
- Summaries in progress have status "pending"
- The `input_scope` field indicates that summaries are based only on article excerpts from the RSS feed, not full article text
- Each summary includes the `model` (AI model used) and `prompt_version` for reproducibility

## Rate Limiting

The API does not enforce rate limiting for read operations. However, the background collection job is limited to 25 AI summary generations per run to manage API costs.

## Example cURL Requests

```bash
# Get status
curl https://mynews-fdgy.onrender.com/status

# List all stories
curl https://mynews-fdgy.onrender.com/stories

# Get a specific story
curl https://mynews-fdgy.onrender.com/stories/1
```
