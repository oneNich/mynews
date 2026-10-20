import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Article, Story, Summary, BackgroundLink
from retention import run_retention


@pytest.fixture
def db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_delete_expired_articles(db):
    """Test that articles older than 168h are deleted."""
    now = datetime.utcnow()
    recent = now - timedelta(hours=167)
    expired = now - timedelta(hours=169)

    # Add articles
    article_recent = Article(
        url="https://example.com/recent",
        url_norm="https://example.com/recent",
        publisher="Test",
        title="Recent Article",
        published_at=recent,
    )
    article_expired = Article(
        url="https://example.com/expired",
        url_norm="https://example.com/expired",
        publisher="Test",
        title="Expired Article",
        published_at=expired,
    )
    db.add(article_recent)
    db.add(article_expired)
    db.commit()

    # Run retention
    count = run_retention(db)

    # Verify one deleted
    assert count == 1
    assert db.query(Article).count() == 1
    assert db.query(Article).first().title == "Recent Article"


def test_delete_story_with_no_remaining_articles(db):
    """Test that stories with no remaining articles are deleted with their summaries."""
    now = datetime.utcnow()
    expired = now - timedelta(hours=169)

    # Add story and article
    story = Story(headline="Test Story")
    db.add(story)
    db.commit()

    article = Article(
        url="https://example.com/article",
        url_norm="https://example.com/article",
        publisher="Test",
        title="Article",
        published_at=expired,
        story_id=story.id,
    )
    db.add(article)

    # Add summary
    summary = Summary(
        story_id=story.id,
        input_hash="test_hash",
        status="completed",
        overview="Test overview",
    )
    db.add(summary)
    db.commit()

    # Run retention
    count = run_retention(db)

    # Story, article, and summary should be deleted
    assert count == 1
    assert db.query(Article).count() == 0
    assert db.query(Story).count() == 0
    assert db.query(Summary).count() == 0


def test_delete_story_background_links_with_story(db):
    """Test that background links are deleted when story is deleted."""
    now = datetime.utcnow()
    expired = now - timedelta(hours=169)

    # Add story and article
    story = Story(headline="Test Story")
    db.add(story)
    db.commit()

    article = Article(
        url="https://example.com/article",
        url_norm="https://example.com/article",
        publisher="Test",
        title="Article",
        published_at=expired,
        story_id=story.id,
    )
    db.add(article)

    # Add background links
    link = BackgroundLink(
        story_id=story.id,
        title="Background",
        url="https://example.com/background",
        source="Test",
    )
    db.add(link)
    db.commit()

    # Run retention
    count = run_retention(db)

    # Story and background link should be deleted
    assert count == 1
    assert db.query(Story).count() == 0
    assert db.query(BackgroundLink).count() == 0


def test_story_with_multiple_articles_one_expires(db):
    """Test that story keeps summary as 'pending' when losing one article but keeping others."""
    now = datetime.utcnow()
    expired = now - timedelta(hours=169)
    recent = now - timedelta(hours=167)

    # Add story
    story = Story(headline="Test Story")
    db.add(story)
    db.commit()

    # Add two articles, one expired and one recent
    article_expired = Article(
        url="https://example.com/expired",
        url_norm="https://example.com/expired",
        publisher="Test",
        title="Expired Article",
        published_at=expired,
        story_id=story.id,
    )
    article_recent = Article(
        url="https://example.com/recent",
        url_norm="https://example.com/recent",
        publisher="Test",
        title="Recent Article",
        published_at=recent,
        story_id=story.id,
    )
    db.add(article_expired)
    db.add(article_recent)

    # Add summary
    summary = Summary(
        story_id=story.id,
        input_hash="test_hash",
        status="completed",
        overview="Test overview",
    )
    db.add(summary)
    db.commit()

    # Run retention
    count = run_retention(db)

    # One article deleted, story and summary remain
    assert count == 1
    assert db.query(Article).count() == 1
    assert db.query(Article).first().title == "Recent Article"
    assert db.query(Story).count() == 1
    assert db.query(Summary).count() == 1
    # Summary status should be 'pending'
    assert db.query(Summary).first().status == "pending"


def test_no_expired_articles(db):
    """Test that nothing happens when there are no expired articles."""
    now = datetime.utcnow()
    recent = now - timedelta(hours=167)

    # Add recent article
    article = Article(
        url="https://example.com/recent",
        url_norm="https://example.com/recent",
        publisher="Test",
        title="Recent Article",
        published_at=recent,
    )
    db.add(article)
    db.commit()

    # Run retention
    count = run_retention(db)

    # Nothing deleted
    assert count == 0
    assert db.query(Article).count() == 1


def test_article_without_story_expired(db):
    """Test that articles without a story_id are also deleted if expired."""
    now = datetime.utcnow()
    expired = now - timedelta(hours=169)

    # Add article without story_id
    article = Article(
        url="https://example.com/article",
        url_norm="https://example.com/article",
        publisher="Test",
        title="Article",
        published_at=expired,
        story_id=None,
    )
    db.add(article)
    db.commit()

    # Run retention
    count = run_retention(db)

    # Article deleted
    assert count == 1
    assert db.query(Article).count() == 0
