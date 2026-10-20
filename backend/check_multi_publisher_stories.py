#!/usr/bin/env python3
"""Print stories with 2+ publishers."""
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models import Base, Article, Story

database_url = "sqlite:///local.db"
engine = create_engine(database_url)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

stories_with_publishers = db.query(Story.id, Story.headline).all()

multi_publisher_stories = []

for story_id, headline in stories_with_publishers:
    articles = db.query(Article).filter(Article.story_id == story_id).all()
    publishers = set(a.publisher for a in articles)

    if len(publishers) >= 2:
        multi_publisher_stories.append((story_id, headline, articles))

print("\n=== Stories with 2+ Publishers ===")
if not multi_publisher_stories:
    print("No stories with multiple publishers yet.")
else:
    for story_id, headline, articles in multi_publisher_stories:
        print(f"\nStory ID: {story_id}")
        print(f"Headline: {headline}")
        print("Articles:")
        for article in articles:
            print(f"  - {article.publisher}: {article.title}")

db.close()
