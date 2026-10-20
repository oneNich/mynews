import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Article
from ingest import (
    normalize_url,
    article_from_feed_item,
    ingest,
    parse_published_date,
    strip_html,
)


@pytest.fixture
def db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_normalize_url():
    """Test URL normalization."""
    assert normalize_url("https://Example.com/path?query=1#frag") == "https://example.com/path"
    assert normalize_url("https://example.com/path/") == "https://example.com/path"
    assert normalize_url("https://example.com") == "https://example.com"


def test_strip_html():
    """Test HTML stripping."""
    assert strip_html("<p>Hello <b>world</b></p>") == "Hello world"
    assert strip_html("No HTML here") == "No HTML here"
    assert strip_html(None) == ""


def test_article_from_feed_item():
    """Test article normalization from feed entry."""
    now = datetime.now(timezone.utc)
    old_date = (now - timedelta(hours=200)).timetuple()[:6]

    # Valid entry
    entry = {
        "title": "Test Article",
        "link": "https://example.com/article",
        "summary": "<p>Summary text</p>",
        "published": "2024-01-01T00:00:00Z",
        "published_parsed": now.timetuple()[:6],
    }
    article = article_from_feed_item(entry, "Test Publisher")
    assert article is not None
    assert article["title"] == "Test Article"
    assert article["publisher"] == "Test Publisher"
    assert article["summary_text"] == "Summary text"
    assert article["url_norm"] == "https://example.com/article"

    # Missing date
    entry_no_date = {"title": "Test", "link": "https://example.com"}
    assert article_from_feed_item(entry_no_date, "Test") is None

    # Too old
    entry_old = {
        "title": "Old Article",
        "link": "https://example.com/old",
        "published": "2023-01-01T00:00:00Z",
        "published_parsed": old_date,
    }
    assert article_from_feed_item(entry_old, "Test") is None


def test_dedup_upsert(db):
    """Test that upsert by url_norm prevents duplicates."""
    now = datetime.now(timezone.utc)
    now_tuple = now.timetuple()[:6]

    # Entry 1
    entry1 = {
        "title": "Article Title v1",
        "link": "https://EXAMPLE.COM/article?ref=feed",
        "summary": "Summary 1",
        "published": "2024-01-01T00:00:00Z",
        "published_parsed": now_tuple,
    }

    # Entry 2 - same URL with different normalization
    entry2 = {
        "title": "Article Title v2",
        "link": "https://EXAMPLE.COM/article?ref=feed",
        "summary": "Summary 2",
        "published": "2024-01-01T00:00:00Z",
        "published_parsed": now_tuple,
    }

    article1 = article_from_feed_item(entry1, "Test")
    article2 = article_from_feed_item(entry2, "Test")

    # Both should normalize to same url_norm
    assert article1["url_norm"] == article2["url_norm"]

    # Upsert first article
    db_article1 = Article(**article1)
    db.add(db_article1)
    db.commit()

    # Verify one row
    assert db.query(Article).count() == 1
    assert db.query(Article).first().title == "Article Title v1"

    # Upsert second article (should update existing)
    existing = db.query(Article).filter_by(url_norm=article2["url_norm"]).first()
    if existing:
        existing.title = article2["title"]
        existing.summary_text = article2["summary_text"]
    else:
        db_article2 = Article(**article2)
        db.add(db_article2)
    db.commit()

    # Still one row, updated
    assert db.query(Article).count() == 1
    assert db.query(Article).first().title == "Article Title v2"


def test_duplicate_url_norm_unique_constraint(db):
    """Test that database enforces url_norm uniqueness."""
    article = Article(
        url="https://example.com/article",
        url_norm="https://example.com/article",
        publisher="Test",
        title="Title",
        published_at=datetime.now(timezone.utc),
    )
    db.add(article)
    db.commit()

    # Try to insert same url_norm
    article2 = Article(
        url="https://example.com/article?ref=other",
        url_norm="https://example.com/article",
        publisher="Test2",
        title="Title 2",
        published_at=datetime.now(timezone.utc),
    )
    db.add(article2)

    with pytest.raises(Exception):
        db.commit()
