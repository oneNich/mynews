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

stories_with_publishers = db.query(
    Story.id,
    Story.headline,
    func.group_concat(Article.publisher, ", ").label("publishers")
).join(Article, Story.id == Article.story_id).group_by(Story.id).having(
    func.count(func.distinct(Article.publisher)) >= 2
).all()

print("\n=== Stories with 2+ Publishers ===")
if not stories_with_publishers:
    print("No stories with multiple publishers yet.")
else:
    for story_id, headline, publishers in stories_with_publishers:
        print(f"\nHeadline: {headline}")
        print(f"Publishers: {publishers}")

db.close()
