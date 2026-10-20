from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Article, Story, Summary, BackgroundLink


def run_retention(db: Session) -> int:
    """Delete expired articles and clean up orphaned stories.

    Returns the count of articles deleted.
    """
    now = datetime.utcnow()
    cutoff_time = now - timedelta(hours=168)

    # Find articles to delete
    expired_articles = db.query(Article).filter(
        Article.published_at < cutoff_time
    ).all()

    articles_expired = len(expired_articles)

    if articles_expired == 0:
        return 0

    # Get story IDs that had expired articles
    story_ids_affected = set()
    for article in expired_articles:
        if article.story_id:
            story_ids_affected.add(article.story_id)

    # Delete expired articles
    db.query(Article).filter(Article.published_at < cutoff_time).delete()
    db.commit()

    # For each affected story, check if it still has articles
    for story_id in story_ids_affected:
        remaining_articles = db.query(Article).filter_by(story_id=story_id).count()

        if remaining_articles == 0:
            # Delete story, its summary, and background links
            db.query(BackgroundLink).filter_by(story_id=story_id).delete()
            db.query(Summary).filter_by(story_id=story_id).delete()
            db.query(Story).filter_by(id=story_id).delete()
        else:
            # Story still has articles, set summary status to pending
            summary = db.query(Summary).filter_by(story_id=story_id).first()
            if summary:
                summary.status = "pending"

    db.commit()
    return articles_expired
