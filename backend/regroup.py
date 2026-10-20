#!/usr/bin/env python3
"""One-time script to reset and rerun grouping.
- Sets story_id to NULL on all articles
- Deletes all stories
- Deletes all articles where publisher = 'Test'
- Runs grouping
"""

from db import SessionLocal, engine
from models import Base, Article, Story
from grouping import group_articles

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("Deleting articles where publisher = 'Test'...")
    test_articles = db.query(Article).filter(Article.publisher == 'Test').all()
    for article in test_articles:
        db.delete(article)
    db.commit()
    print(f"  Deleted {len(test_articles)} Test articles")

    print("Deleting all stories...")
    db.query(Article).update({Article.story_id: None})
    db.flush()
    db.query(Story).delete()
    db.commit()
    print("  Stories deleted")

    print("Resetting story_id to NULL on all articles...")
    db.query(Article).update({Article.story_id: None})
    db.commit()
    articles_reset = db.query(Article).filter(Article.story_id.is_(None)).count()
    print(f"  Reset {articles_reset} articles to have no story")

    print("\nRunning grouping...")
    stats = group_articles(db)
    print(f"  Stories created: {stats['stories_created']}")
    print(f"  Stories joined: {stats['stories_joined']}")

    print("\nDone!")
    db.close()

if __name__ == "__main__":
    main()
