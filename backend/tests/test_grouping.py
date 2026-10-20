import pytest
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Article, Story
from grouping import group_articles


@pytest.fixture
def db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def grouping_cases():
    """Load test cases from fixture file."""
    with open("tests/fixtures/grouping_cases.json") as f:
        return json.load(f)["cases"]


def test_same_event_different_publishers_must_group(db, grouping_cases):
    """Test that articles about the same event from different publishers are grouped."""
    case = grouping_cases[0]  # Ukraine aid vote case
    now = datetime.now(timezone.utc)

    articles_data = []
    for article_spec in case["articles"]:
        article = Article(
            url=f"https://{article_spec['publisher'].lower()}.com/{len(articles_data)}",
            url_norm=f"https://{article_spec['publisher'].lower()}.com/{len(articles_data)}",
            publisher=article_spec["publisher"],
            title=article_spec["title"],
            summary_text=article_spec["summary_text"],
            published_at=now - timedelta(hours=article_spec["hours_ago"]),
        )
        db.add(article)
        articles_data.append(article)

    db.commit()

    assert all(a.story_id is None for a in articles_data), "All articles should start with no story"

    group_articles(db)

    story_ids = [db.query(Article).filter(Article.id == a.id).first().story_id for a in articles_data]
    assert len(set(story_ids)) == 1, "All articles should be grouped into one story"
    assert all(sid is not None for sid in story_ids), "All articles should have a story_id"


def test_biden_different_events_must_stay_separate(db, grouping_cases):
    """Test that articles about Biden at different locations stay separate."""
    case = grouping_cases[1]  # Biden speech case
    now = datetime.now(timezone.utc)

    articles_data = []
    for article_spec in case["articles"]:
        article = Article(
            url=f"https://{article_spec['publisher'].lower()}.com/{len(articles_data)}",
            url_norm=f"https://{article_spec['publisher'].lower()}.com/{len(articles_data)}",
            publisher=article_spec["publisher"],
            title=article_spec["title"],
            summary_text=article_spec["summary_text"],
            published_at=now - timedelta(hours=article_spec["hours_ago"]),
        )
        db.add(article)
        articles_data.append(article)

    db.commit()

    group_articles(db)

    story_ids = [db.query(Article).filter(Article.id == a.id).first().story_id for a in articles_data]
    assert len(set(story_ids)) == 2, "Articles should be in separate stories"


def test_tesla_factory_different_publishers_must_group(db, grouping_cases):
    """Test that articles about Tesla factory expansion are grouped."""
    case = grouping_cases[2]  # Tesla Gigafactory case
    now = datetime.now(timezone.utc)

    articles_data = []
    for article_spec in case["articles"]:
        article = Article(
            url=f"https://{article_spec['publisher'].lower()}.com/{len(articles_data)}",
            url_norm=f"https://{article_spec['publisher'].lower()}.com/{len(articles_data)}",
            publisher=article_spec["publisher"],
            title=article_spec["title"],
            summary_text=article_spec["summary_text"],
            published_at=now - timedelta(hours=article_spec["hours_ago"]),
        )
        db.add(article)
        articles_data.append(article)

    db.commit()

    group_articles(db)

    story_ids = [db.query(Article).filter(Article.id == a.id).first().story_id for a in articles_data]
    assert len(set(story_ids)) == 1, "All articles should be grouped into one story"


def test_apple_different_stories_must_stay_separate(db, grouping_cases):
    """Test that articles about Apple but different stories stay separate."""
    case = grouping_cases[3]  # Apple different stories case
    now = datetime.now(timezone.utc)

    articles_data = []
    for article_spec in case["articles"]:
        article = Article(
            url=f"https://{article_spec['publisher'].lower()}.com/{len(articles_data)}",
            url_norm=f"https://{article_spec['publisher'].lower()}.com/{len(articles_data)}",
            publisher=article_spec["publisher"],
            title=article_spec["title"],
            summary_text=article_spec["summary_text"],
            published_at=now - timedelta(hours=article_spec["hours_ago"]),
        )
        db.add(article)
        articles_data.append(article)

    db.commit()

    group_articles(db)

    story_ids = [db.query(Article).filter(Article.id == a.id).first().story_id for a in articles_data]
    assert len(set(story_ids)) == 2, "Articles should be in separate stories"


def test_single_article_creates_story(db):
    """Test that a single article creates a new story."""
    now = datetime.now(timezone.utc)
    article = Article(
        url="https://example.com/article",
        url_norm="https://example.com/article",
        publisher="Example",
        title="Example Article",
        summary_text="This is an example article.",
        published_at=now,
    )
    db.add(article)
    db.commit()

    assert article.story_id is None

    group_articles(db)

    article = db.query(Article).filter(Article.id == article.id).first()
    assert article.story_id is not None
    story = db.query(Story).filter(Story.id == article.story_id).first()
    assert story is not None
    assert story.headline == "Example Article"


def test_story_headline_updated_to_most_recent(db):
    """Test that story headline is set to most recent article's title."""
    now = datetime.now(timezone.utc)

    article1 = Article(
        url="https://example.com/article1",
        url_norm="https://example.com/article1",
        publisher="Example",
        title="Older Article Title",
        summary_text="Congress and Senate vote on Ukraine aid package supporting Ukrainian defense efforts. Both chambers passed Ukraine assistance.",
        published_at=now - timedelta(hours=5),
    )
    article2 = Article(
        url="https://example.com/article2",
        url_norm="https://example.com/article2",
        publisher="Example",
        title="Newer Article Title",
        summary_text="Congress and Senate pass Ukraine military aid bill supporting defense against Russian forces. Ukraine assistance approved.",
        published_at=now - timedelta(hours=1),
    )
    db.add(article1)
    db.add(article2)
    db.commit()

    group_articles(db)

    story = db.query(Story).first()
    assert story.headline == "Newer Article Title"
