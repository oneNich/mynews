# My News - News Story Grouping and AI Analysis

A multi-source news aggregation system that groups articles about the same event from different publishers, adds AI-generated summaries, and presents them through a Flutter mobile app.

## Overview

**My News** solves the problem of story fragmentation across multiple news sources. When a major event breaks, dozens of publishers cover it—often with different angles, emphasis, and terminology. This app:

1. **Ingests** RSS feeds from Fox News, NPR, and BBC World (hourly via GitHub Actions)
2. **Groups** articles about the same event using NLP similarity (0.40 threshold, cross-publisher only)
3. **Enriches** each story with Wikipedia background links and AI summaries
4. **Stores** everything in Postgres, exposed via a FastAPI read-only API
5. **Displays** stories in a Flutter Android app with offline caching

## Live API

```
https://mynews-fdgy.onrender.com
```

Documentation: [docs/API.md](docs/API.md)

## Architecture

```
RSS Feeds                    →  GitHub Actions (hourly)  →  Supabase Postgres
(Fox, NPR, BBC)                  ↓
                            worker.py
                            ├─ ingest.py (fetch, dedup)
                            ├─ grouping.py (similarity)
                            ├─ background.py (Wikipedia)
                            ├─ summarize.py (Claude API)
                            └─ retention.py (cleanup)
                                    ↓
                            FastAPI on Render
                            (read-only GET endpoints)
                                    ↓
                            Flutter App (offline cache)
```

**Data Flow:**
- RSS feeds → normalized URLs → article dedup
- Articles grouped by similarity (cross-publisher matches only)
- Wikipedia entity extraction for background links
- AI summaries (once per story, reused on client refresh)
- 7-day retention by publication time
- Clients read via API, cache locally

## Setup

### Backend

**Prerequisites:**
- Python 3.11+
- PostgreSQL (or Supabase via `postgresql://` URL)

**Steps:**

1. Clone and enter directory:
   ```bash
   cd backend
   ```

2. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Copy `.env.example` to `.env` and fill in:
   ```bash
   cp .env.example .env
   ```

   Required variables:
   - `DATABASE_URL` — Postgres connection string (e.g., `postgresql://user:pass@host:5432/db`)
   - `ANTHROPIC_API_KEY` — [Get from Anthropic Console](https://console.anthropic.com/)

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the hourly collection job:
   ```bash
   python worker.py
   ```

6. Start the API server:
   ```bash
   uvicorn main:app --reload  # dev: http://localhost:8000
   ```

### Flutter App

**Prerequisites:**
- Flutter 3.13+ and Dart
- Android SDK (for Android build)

**Steps:**

1. Enter app directory:
   ```bash
   cd app
   ```

2. Install dependencies:
   ```bash
   flutter pub get
   ```

3. Run in debug mode:
   ```bash
   flutter run --dart-define=API_URL=https://mynews-fdgy.onrender.com
   ```

4. Build release APK:
   ```bash
   flutter build apk --release --dart-define=API_URL=https://mynews-fdgy.onrender.com
   ```

5. Install on phone:
   ```bash
   adb install build/app/outputs/flutter-apk/app-release.apk
   ```

## Data Model

Five tables power the system:

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| **articles** | Raw articles fetched from RSS | `url_norm` (dedup key), `publisher`, `title`, `summary_text` (excerpt), `published_at`, `story_id` (foreign key) |
| **stories** | Grouped articles (one event) | `headline`, `created_at`, `updated_at` |
| **background_links** | Wikipedia context per story | `story_id`, `title`, `url`, `source` ("Wikipedia") |
| **summaries** | AI-generated analysis | `story_id`, `input_hash` (for reuse), `status` ("pending"/"failed"/"ok"), `overview`, `agreement`, `uncertainty`, `perspectives_json`, `model`, `prompt_version`, `generated_at` |
| **job_runs** | Hourly ingestion log | `trigger`, `articles_new`, `articles_expired`, `ai_calls`, `background_links_added`, `errors_json` |

## Core Behaviors

### Story Grouping

See [docs/GROUPING.md](docs/GROUPING.md) for full details.

**Summary:**
- Compare each unassigned article against all articles in the 7-day window
- **Cross-publisher-only rule:** Match only if best match is from a *different* publisher
- Similarity threshold: 0.40 (requires ≥2 shared capitalized terms)
- If match found with existing story, assign; else create new story

**Prevents false merges** (e.g., same outlet covering different angles on the same topic).

### Background Links

See [docs/BACKGROUND.md](docs/BACKGROUND.md) for full details.

**Summary:**
- Extract named entities (preferring 2-word phrases like "Ilhan Omar")
- Query Wikipedia for each entity
- Validate: page title words must appear in article text
- Cap: 3 links per story
- Error handling: logged, never crashes worker

### AI Summaries

- **Model:** Claude Haiku 5.5 via Anthropic API
- **Input:** Multi-publisher stories only, sorted newest first
- **Reuse:** Input hash (SHA256 of sorted article IDs, titles, excerpt) caches results
- **Per-run cap:** 25 API calls (cost control)
- **Failure handling:** Status set to "failed", error logged, no made-up text
- **Fields returned:** `overview`, `agreement`, `uncertainty`, `perspectives` (viewpoints with supporting articles), `insufficient_evidence` (boolean)

**Prompt file:** `backend/summarize.py` (hardcoded template; no external file)  
**Config:** No `ai_config.json`; parameters in `summarize.py` and Anthropic API key via environment

### Retention

- **Window:** Articles with `published_at >= now - 168 hours`
- **Missing/invalid dates:** Skipped during ingest, counted in job log
- **Orphaned stories:** Auto-deleted when their last article expires
- **Timing:** Runs at end of every `worker.py` execution

### Two-Client Reuse

When two clients request the same story:
1. Worker fetches articles, groups them, and stores story in DB
2. **First client:** Receives story ID (1234), may trigger summary job
3. **Second client:** Receives same story ID (1234) from API; client caches data locally
4. **Summary reuse:** Input hash ensures if summary regenerates (e.g., new article added), same hash = no re-API-call; existing summary shown

## Services & Costs

| Service | Provider | Tier | Expected Cost | Quotas |
|---------|----------|------|---|---|
| **API Hosting** | Render | Free | $0/mo | 750 hrs/mo execution; ~30s cold start |
| **Database** | Supabase | Free | $0/mo | 500MB storage; concurrent queries within free tier |
| **CI/CD** | GitHub Actions | Free | $0/mo | 2,000 min/mo per account |
| **AI Summaries** | Anthropic | Pay-as-you-go | $0.01–0.10/day | Claude Haiku 5.5; 25 calls/hr max by design |

**Known Limitations:**
- Render free tier: ~30s cold start on first API call after idle period
- Feed excerpts only: AI summaries use RSS `<summary>` fields, not full article text
- AI summaries regenerate hourly: Stories are re-summarized with new articles (controlled by `input_hash` reuse)

## Known Issues

1. **Database schema not migrated to production:** `models.py` has `insufficient_evidence` (bool) and `prompt_version` (string) on Summary, and `background_links_added` on JobRun, but deployed database may need migration. Will cause errors when deploying updated code without schema migration.

2. **Wikipedia rate limiting:** API returns 403 Forbidden from local development. Gracefully handled (empty results logged). Production OK.

3. **Flutter test infrastructure bug:** Flutter 3.47.5 has a test_core package issue preventing `flutter test` from running. Not a code issue; `flutter analyze` validates correctness.

4. **Test-only data:** "Test" publisher articles used only in in-memory test databases. `regroup.py` deletes any if they exist.

## Development

- **Backend tests:** `pytest backend/tests/`
- **Linting:** `flutter analyze` in `app/`
- **Release build:** See Setup → Flutter App → step 4

## Deployment

**Backend (Render):**
- Push to repo → GitHub Actions (`collect.yml`) runs `worker.py` hourly
- `main.py` uvicorn auto-starts on Render

**App (Mobile):**
- Build release APK with `flutter build apk --release`
- Install on test devices with `adb install`
- Update `--dart-define=API_URL` to production Render URL

## Feedback

Report issues on [GitHub Issues](https://github.com/yourusername/mynews/issues).
