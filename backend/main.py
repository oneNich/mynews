import os
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import func, and_
from db import engine, SessionLocal
from models import Base, Article, Story, BackgroundLink, Summary, JobRun
from worker import main as run_job

app = FastAPI()


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/status")
def get_status():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # Get last successful job run
        last_successful = db.query(JobRun).filter(
            JobRun.status == "ok"
        ).order_by(JobRun.started_at.desc()).first()

        last_successful_time = last_successful.started_at.isoformat() if last_successful else None

        # Get last run status
        last_run = db.query(JobRun).order_by(JobRun.started_at.desc()).first()
        last_run_status = last_run.status if last_run else None

        # Get last 5 job runs
        job_runs = db.query(JobRun).order_by(
            JobRun.started_at.desc()
        ).limit(5).all()

        job_runs_data = [
            {
                "started_at": jr.started_at.isoformat(),
                "status": jr.status,
                "trigger": jr.trigger,
                "articles_new": jr.articles_new,
                "articles_expired": jr.articles_expired,
                "ai_calls": jr.ai_calls,
            }
            for jr in job_runs
        ]

        return {
            "last_successful_time": last_successful_time,
            "last_run_status": last_run_status,
            "last_5_job_runs": job_runs_data,
        }
    finally:
        db.close()


@app.get("/stories")
def get_stories():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(hours=168)

        # Get all stories with articles in the 7-day window
        # Use a subquery to get stories with recent articles
        recent_article_ids = db.query(Article.story_id).filter(
            Article.published_at >= cutoff_time,
            Article.story_id.isnot(None)
        ).distinct()

        stories = db.query(Story).filter(
            Story.id.in_(recent_article_ids)
        ).all()

        # Sort stories by latest article date, newest first
        stories_data = []
        for story in stories:
            articles = db.query(Article).filter(
                Article.story_id == story.id,
                Article.published_at >= cutoff_time
            ).all()

            if not articles:
                continue

            latest_article_at = max(a.published_at for a in articles)
            publisher_count = len(set(a.publisher for a in articles))
            article_count = len(articles)

            # Get summary status
            summary = db.query(Summary).filter(Summary.story_id == story.id).first()
            summary_status = summary.status if summary else None

            stories_data.append({
                "id": story.id,
                "headline": story.headline,
                "latest_article_at": latest_article_at.isoformat(),
                "publisher_count": publisher_count,
                "article_count": article_count,
                "summary_status": summary_status,
            })

        # Sort by latest_article_at, newest first
        stories_data.sort(key=lambda x: x["latest_article_at"], reverse=True)

        return {"stories": stories_data}
    finally:
        db.close()


@app.get("/stories/{story_id}")
def get_story_detail(story_id: int):
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(hours=168)

        # Get the story
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")

        # Get articles for this story (only recent ones)
        articles = db.query(Article).filter(
            Article.story_id == story_id,
            Article.published_at >= cutoff_time
        ).all()

        if not articles:
            # Story has no recent articles - it's expired
            raise HTTPException(status_code=404, detail="Story expired")

        # Group articles by publisher
        publishers_dict = {}
        for article in articles:
            if article.publisher not in publishers_dict:
                publishers_dict[article.publisher] = []
            publishers_dict[article.publisher].append({
                "title": article.title,
                "url": article.url,
                "published_at": article.published_at.isoformat(),
                "excerpt": article.summary_text,
            })

        publishers_list = [
            {
                "publisher": publisher,
                "articles": articles_list
            }
            for publisher, articles_list in publishers_dict.items()
        ]

        # Get background links
        background_links = db.query(BackgroundLink).filter(
            BackgroundLink.story_id == story_id
        ).all()

        background_links_data = [
            {
                "title": link.title,
                "url": link.url,
                "source": link.source,
            }
            for link in background_links
        ]

        # Get summary
        summary = db.query(Summary).filter(Summary.story_id == story_id).first()

        summary_data = None
        if summary:
            summary_data = {
                "status": summary.status,
                "label": "AI-generated",
                "generated_at": summary.generated_at.isoformat() if summary.generated_at else None,
                "model": summary.model,
                "input_scope": "Feed excerpts only",
            }

            # Only include text fields if status is ok
            if summary.status == "ok":
                summary_data["overview"] = summary.overview
                summary_data["agreement"] = summary.agreement
                summary_data["uncertainty"] = summary.uncertainty
                summary_data["insufficient_evidence"] = summary.insufficient_evidence

                # Format perspectives with article details
                if summary.perspectives_json:
                    perspectives = []
                    for perspective in summary.perspectives_json:
                        perspective_copy = dict(perspective)
                        # Replace article_ids with full article details
                        cited_articles = []
                        for article_id in perspective.get("article_ids", []):
                            article = db.query(Article).filter(Article.id == article_id).first()
                            if article:
                                cited_articles.append({
                                    "title": article.title,
                                    "publisher": article.publisher,
                                    "url": article.url,
                                })
                        perspective_copy["cited_articles"] = cited_articles
                        del perspective_copy["article_ids"]
                        perspectives.append(perspective_copy)
                    summary_data["perspectives"] = perspectives
                else:
                    summary_data["perspectives"] = []
            else:
                # Pending or failed - return null text fields
                summary_data["overview"] = None
                summary_data["agreement"] = None
                summary_data["uncertainty"] = None
                summary_data["perspectives"] = None
                summary_data["insufficient_evidence"] = None

        return {
            "id": story.id,
            "headline": story.headline,
            "updated_at": story.updated_at.isoformat(),
            "publishers": publishers_list,
            "background_links": background_links_data,
            "summary": summary_data,
        }
    finally:
        db.close()


@app.post("/admin/collect")
def collect(x_admin_token: str = Header(None)):
    admin_token = os.getenv("ADMIN_TOKEN")
    if not admin_token or x_admin_token != admin_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    run_job(trigger="manual")
    return {"status": "ok"}
