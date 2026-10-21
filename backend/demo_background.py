#!/usr/bin/env python3
"""Demonstrate background links functionality with test data."""

from db import engine, SessionLocal
from models import Base, Story, Article, BackgroundLink
from datetime import datetime, timezone
from background import find_background_links

# Setup database
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Clear existing data for demo
db.query(BackgroundLink).delete()
db.query(Article).delete()
db.query(Story).delete()
db.commit()

# Create test stories with 2+ publishers
demo_stories = [
    {
        'headline': 'Ilhan Omar Proposes Climate Bill',
        'articles': [
            {
                'url': 'https://npr.org/climate-bill',
                'publisher': 'NPR',
                'title': 'Omar Climate Bill Gets Support',
                'summary': 'Congresswoman Ilhan Omar announced a comprehensive climate legislation package that would establish aggressive carbon reduction targets.'
            },
            {
                'url': 'https://bbc.com/climate-bill',
                'publisher': 'BBC',
                'title': 'Minnesota Representative Pushes Green Initiative',
                'summary': 'Omar\'s bill would include significant investments in renewable energy and environmental protection measures.'
            }
        ]
    },
    {
        'headline': 'Supreme Court Issues Voting Rights Decision',
        'articles': [
            {
                'url': 'https://foxnews.com/scotus-ruling',
                'publisher': 'Fox News',
                'title': 'Supreme Court Decides Major Voting Rights Case',
                'summary': 'The Supreme Court issued its decision on a critical voting rights case today, affecting millions of voters.'
            },
            {
                'url': 'https://npr.org/scotus-ruling',
                'publisher': 'NPR',
                'title': 'SCOTUS Ruling Could Impact Election Access',
                'summary': 'Supreme Court decision will have significant impact on how voting procedures are administered.'
            }
        ]
    },
    {
        'headline': 'World Series Championship Announced',
        'articles': [
            {
                'url': 'https://espn.com/worldseries',
                'publisher': 'ESPN',
                'title': 'Yankees Win World Series',
                'summary': 'The New York Yankees won the World Series championship after defeating the Los Angeles Dodgers.'
            },
            {
                'url': 'https://bbc.com/baseball',
                'publisher': 'BBC',
                'title': 'Baseball World Series Champion Crowned',
                'summary': 'The World Series concluded today with the Yankees securing their first championship in years.'
            }
        ]
    }
]

# Create stories and articles
for story_data in demo_stories:
    story = Story(headline=story_data['headline'])
    db.add(story)
    db.flush()

    for article_data in story_data['articles']:
        article = Article(
            url=article_data['url'],
            url_norm=article_data['url'],
            publisher=article_data['publisher'],
            title=article_data['title'],
            summary_text=article_data['summary'],
            published_at=datetime.now(timezone.utc),
            story_id=story.id
        )
        db.add(article)

db.commit()

print("=" * 70)
print("BACKGROUND LINKS DEMONSTRATION")
print("=" * 70)
print()

# Show all stories
stories = db.query(Story).all()
print(f"Created {len(stories)} test stories")
print()

# Show stories with 2+ publishers
multi_publisher_stories = []
for story in stories:
    articles = db.query(Article).filter(Article.story_id == story.id).all()
    publishers = set(a.publisher for a in articles)
    if len(publishers) >= 2:
        multi_publisher_stories.append((story, articles, publishers))
        print(f"Story: \"{story.headline}\"")
        print(f"  Publishers: {', '.join(sorted(publishers))}")
        print(f"  Articles: {len(articles)}")
        for article in articles:
            print(f"    - {article.publisher}: {article.title}")

        # Show extracted entities
        from background import extract_named_entities
        combined_text = story.headline + ' ' + ' '.join(a.title for a in articles)
        entities = extract_named_entities(combined_text)
        print(f"  Extracted entities: {entities}")
        print()

print("=" * 70)
print("NOTE: Wikipedia API access is blocked by Wikipedia's rate limiting")
print("In production, the background link processing would:")
print("1. Extract named entities from story headlines and article titles")
print("2. Query Wikipedia Search API for each entity")
print("3. Filter results to keep only those relevant to the story")
print("4. Store up to 3 links per story in the background_links table")
print()
print("The test suite (test_background.py) validates this functionality")
print("using mocked Wikipedia API responses.")
print("=" * 70)

db.close()
