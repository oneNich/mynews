import json
from datetime import datetime, timezone
from db import SessionLocal, engine
from models import Base, JobRun
from ingest import ingest


def main(trigger="manual"):
    """Run the ingestion job."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    job = JobRun(trigger=trigger, status="running")
    db.add(job)
    db.commit()

    try:
        stats = ingest(db)

        job.status = "ok" if not stats["errors"] else "partial"
        job.articles_fetched = stats["articles_fetched"]
        job.articles_new = stats["articles_new"]
        job.articles_expired = stats.get("articles_expired", 0)
        job.ai_calls = 0
        if stats["errors"]:
            job.errors_json = json.dumps(stats["errors"])

        job.finished_at = datetime.now(timezone.utc)
        db.commit()

        print(f"[{job.status.upper()}] Fetched: {job.articles_fetched}, New: {job.articles_new}, Errors: {len(stats['errors'])}")

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
