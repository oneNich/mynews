import json
from datetime import datetime, timezone
from db import SessionLocal, engine
from models import Base, JobRun
from ingest import ingest
from grouping import group_articles
from retention import run_retention
from background import process_background_links
from summarize import process_summaries


def main(trigger="manual"):
    """Run the ingestion job."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    job = JobRun(trigger=trigger, status="running")
    db.add(job)
    db.commit()

    try:
        stats = ingest(db)
        grouping_stats = group_articles(db)
        background_added, bg_errors = process_background_links(db)
        articles_expired = run_retention(db)
        ai_calls, summary_errors = process_summaries(db)

        job.status = "ok" if not stats["errors"] and not summary_errors else "partial"
        job.articles_fetched = stats["articles_fetched"]
        job.articles_new = stats["articles_new"]
        job.articles_expired = articles_expired
        job.ai_calls = ai_calls
        job.background_links_added = background_added
        all_errors = stats["errors"] + bg_errors + summary_errors
        if all_errors:
            job.errors_json = json.dumps(all_errors)

        job.finished_at = datetime.now(timezone.utc)
        db.commit()

        print(f"[{job.status.upper()}] Fetched: {job.articles_fetched}, New: {job.articles_new}, Expired: {job.articles_expired}, Stories Created: {grouping_stats['stories_created']}, Stories Joined: {grouping_stats['stories_joined']}, Background Links Added: {background_added}, AI Calls: {ai_calls}, Errors: {len(all_errors)}")

    except Exception as e:
        job.status = "failed"
        job.errors_json = json.dumps({"fatal": str(e)})
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        print(f"[FAILED] {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
