# Release Notes

## Version 1.0.0+1

**Release Date:** [FILL IN]

### Features

- **News story grouping:** Automatically groups articles from Fox News, NPR, and BBC World about the same event using NLP similarity (cross-publisher matches only)
- **AI-generated summaries:** Claude Haiku 5.5 summaries per story with overview, agreement, uncertainty, and multiple perspectives
- **Background research:** Automatic Wikipedia entity extraction and link suggestions per story
- **7-day rolling window:** Articles automatically expire after 168 hours by publication time
- **Offline support:** Full offline mode with cached story data when network unavailable
- **Hourly updates:** GitHub Actions runs ingestion job automatically every hour
- **REST API:** Read-only FastAPI endpoints for stories, story details, and job status
- **Flutter app:** Android app with Material 3 design, story detail screens, AI analysis view, and perspective explorer

### Known Minor Issues

- **Render cold start:** API may respond slowly (~30 seconds) after idle period (Render free tier limitation)
- **Feed excerpts only:** AI summaries analyze RSS feed excerpts, not full article text (by design for cost control)
- **AI summary regeneration:** Summaries regenerate hourly as new articles added; previous summary shown if input unchanged (via `input_hash` caching)
- **Wikipedia rate limiting:** Background link generation may fail on local development (blocked by Wikipedia API rate limits); works in production
- **Flutter test infrastructure:** Flutter 3.47.5 has a framework bug preventing `flutter test` from running; `flutter analyze` validates code correctness

### Service Limitations

| Service | Limitation | Impact |
|---------|-----------|--------|
| **Render (free)** | 750 hrs/mo, ~30s cold start | Production API may be slow after idle |
| **Supabase (free)** | 500MB storage | Stories expire after 168h; ~1-2 weeks of 3-source coverage |
| **GitHub Actions (free)** | 2,000 min/mo | Hourly runs consume ~1 min each; room for 40+ other workflows |
| **Anthropic API** | Pay-as-you-go | ~$0.01–0.10/day for 25 summaries/hr |

### Beta Testing

To report issues:
1. Open [GitHub Issues](https://github.com/yourrepo/mynews/issues)
2. Include: what you were doing, what you expected, what actually happened
3. Attach logs if available (Android Logcat for app crashes; backend job logs)

### Installation

**App:**
```bash
flutter build apk --release --dart-define=API_URL=https://mynews-fdgy.onrender.com
adb install build/app/outputs/flutter-apk/app-release.apk
```

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
cp .env.example .env  # Fill DATABASE_URL and ANTHROPIC_API_KEY
pip install -r requirements.txt
python worker.py      # Run once to populate DB
uvicorn main:app      # Start API server
```

### Architecture

- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2, Postgres
- **App:** Flutter 3.13+, Dart, Android target
- **CI/CD:** GitHub Actions (hourly)
- **Hosting:** Render (API), Supabase (database)

See [README.md](../README.md) for full setup guide.
