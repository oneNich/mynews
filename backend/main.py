import os
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from db import engine, SessionLocal
from models import Base, Article, Story
from worker import main as run_job

app = FastAPI()


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/stories")
def get_stories():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(hours=168)

        # Get articles and stories published in the last 168 hours
        articles = db.query(Article).filter(
            Article.published_at >= cutoff_time
        ).all()

        stories = db.query(Story).filter(
            Story.id.in_(db.query(Article.story_id).filter(
                Article.published_at >= cutoff_time
            ).distinct())
        ).all() if articles else []

        return {"stories": stories, "articles": articles}
    finally:
        db.close()


@app.post("/admin/collect")
def collect(x_admin_token: str = Header(None)):
    admin_token = os.getenv("ADMIN_TOKEN")
    if not admin_token or x_admin_token != admin_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    run_job(trigger="manual")
    return {"status": "ok"}
