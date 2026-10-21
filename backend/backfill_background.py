#!/usr/bin/env python3
"""Backfill background links for all existing stories."""

from db import SessionLocal
from models import Story, BackgroundLink
from background import find_background_links


def main():
    """Run background link lookup for every existing story."""
    db = SessionLocal()

    try:
        stories = db.query(Story).all()
        total_added = 0

        for story in stories:
            # Check if story already has background links
            existing = db.query(BackgroundLink).filter(
                BackgroundLink.story_id == story.id
            ).count()

            if existing > 0:
                continue

            # Find and add background links
            links = find_background_links(db, story)

            for link_data in links:
                link = BackgroundLink(
                    story_id=story.id,
                    title=link_data["title"],
                    url=link_data["url"],
                    source=link_data["source"],
                )
                db.add(link)
                total_added += 1

        db.commit()
        print(f"Backfill complete. Added {total_added} background links.")

    except Exception as e:
        print(f"Error during backfill: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
