# My News - project spec
Goal: A Flutter app shows news "stories" (one event, grouped articles from several publishers) with background links and AI summaries. ALL ingestion, grouping, background lookup and AI generation run on a deployed backend. The Flutter app only reads my API.

Status: backend skeleton, RSS ingestion and deployment are already built and working. Build on the existing code; do not rewrite or reorganize it.

Layout:
- backend/  Python 3.11.9, FastAPI, SQLAlchemy 2, Postgres on Supabase
- backend/db.py  loads .env with python-dotenv, then reads DATABASE_URL
- backend/worker.py  hourly collection job, run by GitHub Actions (.github/workflows)
- app/  Flutter Android client
- docs/  API.md, evidence, defect log, release notes
- starter/  original JS starter app (reference only)

Deployment:
- API hosted on Render (free web service, root directory backend). URL is in PROGRESS.md.
- Database: Supabase Postgres via the transaction pooler (port 6543).

Sources (RSS, fetched directly by the server, no proxies):
- Fox News: https://moxie.foxnews.com/google-publisher/latest.xml?format=xml
- NPR: https://feeds.npr.org/1001/rss.xml
- BBC World: https://feeds.bbci.co.uk/news/world/rss.xml

Rules:
- Rolling 7-day window by PUBLICATION time (168 hours). Items with missing/invalid pub dates are skipped and counted in the job log.
- Dedup by normalized URL