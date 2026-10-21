import pytest
import json
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock
from models import Base, Article, Story, Summary
from summarize import (
    compute_input_hash,
    format_articles_for_prompt,
    validate_and_clean_output,
    generate_summary_for_story,
    load_ai_config,
    load_prompt_template,
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


@pytest.fixture
def config():
    """Return a test config."""
    return {
        "model": "claude-haiku-5-5",
        "max_tokens": 1200,
        "temperature": 0.2,
        "prompt_version": "v1"
    }


@pytest.fixture
def prompt_template():
    """Return a simple test prompt template."""
    return "Summarize these articles:\n{articles_text}\n\nReturn JSON."


@pytest.fixture
def sample_articles(db):
    """Create sample articles in the database."""
    story = Story(headline="Test Story")
    db.add(story)
    db.commit()

    article1 = Article(
        url="https://npr.org/1",
        url_norm="https://npr.org/1",
        publisher="NPR",
        title="Article One",
        summary_text="This is the first article about the story",
        published_at=datetime.now(timezone.utc),
        story_id=story.id,
    )
    article2 = Article(
        url="https://bbc.com/1",
        url_norm="https://bbc.com/1",
        publisher="BBC",
        title="Article Two",
        summary_text="This is the second article about the story",
        published_at=datetime.now(timezone.utc),
        story_id=story.id,
    )
    db.add(article1)
    db.add(article2)
    db.commit()

    return story, [article1, article2]


def test_compute_input_hash_consistency():
    """Test that the same articles produce the same hash."""
    # Create mock articles
    class MockArticle:
        def __init__(self, id, title, summary_text):
            self.id = id
            self.title = title
            self.summary_text = summary_text

    articles1 = [
        MockArticle(1, "Title A", "Summary A"),
        MockArticle(2, "Title B", "Summary B"),
    ]
    articles2 = [
        MockArticle(1, "Title A", "Summary A"),
        MockArticle(2, "Title B", "Summary B"),
    ]

    hash1 = compute_input_hash(articles1)
    hash2 = compute_input_hash(articles2)
    assert hash1 == hash2


def test_compute_input_hash_changes_on_modified_content():
    """Test that hash changes when article content changes."""
    class MockArticle:
        def __init__(self, id, title, summary_text):
            self.id = id
            self.title = title
            self.summary_text = summary_text

    articles1 = [
        MockArticle(1, "Title A", "Summary A"),
        MockArticle(2, "Title B", "Summary B"),
    ]
    articles2 = [
        MockArticle(1, "Title A", "Summary A CHANGED"),
        MockArticle(2, "Title B", "Summary B"),
    ]

    hash1 = compute_input_hash(articles1)
    hash2 = compute_input_hash(articles2)
    assert hash1 != hash2


def test_format_articles_for_prompt(sample_articles, db):
    """Test article formatting for prompt."""
    story, articles = sample_articles
    formatted = format_articles_for_prompt(articles)
    assert "NPR" in formatted
    assert "BBC" in formatted
    assert "Article One" in formatted
    assert "Article Two" in formatted
    assert "[1]" in formatted
    assert "[2]" in formatted


def test_validate_output_valid_json():
    """Test validation of valid JSON output."""
    valid_output = json.dumps({
        "overview": "A story overview",
        "agreement": "They agree on this",
        "uncertainty": "But disagree on that",
        "perspectives": [],
        "insufficient_evidence": False
    })
    cleaned, error = validate_and_clean_output(valid_output, ["1", "2"])
    assert error is None
    assert cleaned is not None
    assert cleaned["overview"] == "A story overview"


def test_validate_output_invalid_json():
    """Test validation rejects invalid JSON."""
    invalid_output = "not valid json"
    cleaned, error = validate_and_clean_output(invalid_output, ["1", "2"])
    assert error is not None
    assert cleaned is None
    assert "Invalid JSON" in error


def test_validate_output_missing_fields():
    """Test validation rejects output with missing fields."""
    incomplete_output = json.dumps({
        "overview": "A story overview",
        # Missing other required fields
    })
    cleaned, error = validate_and_clean_output(incomplete_output, ["1", "2"])
    assert error is not None
    assert cleaned is None


def test_validate_output_cleans_article_ids():
    """Test that invalid article IDs are removed from perspectives."""
    output = json.dumps({
        "overview": "Overview",
        "agreement": "",
        "uncertainty": "",
        "perspectives": [
            {
                "name": "Perspective 1",
                "summary": "This perspective says X",
                "article_ids": [1, 2, 999]  # 999 is invalid
            }
        ],
        "insufficient_evidence": False
    })
    cleaned, error = validate_and_clean_output(output, ["1", "2"])
    assert error is None
    assert cleaned["perspectives"][0]["article_ids"] == [1, 2]


def test_generate_summary_same_input_one_call(db, config, prompt_template, sample_articles):
    """Test that the same input called twice makes only 1 API call."""
    story, articles = sample_articles
    call_count = 0

    def fake_call_ai(articles, config, prompt_template):
        nonlocal call_count
        call_count += 1
        output = {
            "overview": "Test overview",
            "agreement": "All agree",
            "uncertainty": "",
            "perspectives": [],
            "insufficient_evidence": False
        }
        return json.dumps(output), None

    # First call
    with patch("summarize.call_ai_api", side_effect=fake_call_ai):
        delta1, error1 = generate_summary_for_story(db, story.id, config, prompt_template, 0)

    assert delta1 == 1
    assert error1 is None
    assert call_count == 1

    # Second call with same content
    with patch("summarize.call_ai_api", side_effect=fake_call_ai):
        delta2, error2 = generate_summary_for_story(db, story.id, config, prompt_template, 1)

    assert delta2 == 0  # No new call
    assert error2 is None
    assert call_count == 1  # Still only 1 call


def test_generate_summary_changed_input_regenerates(db, config, prompt_template, sample_articles):
    """Test that changed input regenerates the summary."""
    story, articles = sample_articles
    call_count = 0

    def fake_call_ai(articles, config, prompt_template):
        nonlocal call_count
        call_count += 1
        output = {
            "overview": "Test overview",
            "agreement": "All agree",
            "uncertainty": "",
            "perspectives": [],
            "insufficient_evidence": False
        }
        return json.dumps(output), None

    # First call
    with patch("summarize.call_ai_api", side_effect=fake_call_ai):
        delta1, error1 = generate_summary_for_story(db, story.id, config, prompt_template, 0)

    assert delta1 == 1
    assert call_count == 1

    # Change an article's content
    article = db.query(Article).filter(Article.story_id == story.id).first()
    article.summary_text = "Modified summary text"
    db.commit()

    # Second call - should regenerate
    with patch("summarize.call_ai_api", side_effect=fake_call_ai):
        delta2, error2 = generate_summary_for_story(db, story.id, config, prompt_template, 1)

    assert delta2 == 1  # New call made
    assert call_count == 2


def test_generate_summary_invalid_json_marks_failed(db, config, prompt_template, sample_articles):
    """Test that invalid JSON from AI marks summary as failed."""
    story, articles = sample_articles

    def fake_call_ai(articles, config, prompt_template):
        # Return invalid JSON
        return "not valid json at all", None

    with patch("summarize.call_ai_api", side_effect=fake_call_ai):
        delta, error = generate_summary_for_story(db, story.id, config, prompt_template, 0)

    assert delta == 1
    assert error is not None
    assert "validation failed" in error.lower()

    # Check that summary was stored with failed status
    summary = db.query(Summary).filter(Summary.story_id == story.id).first()
    assert summary is not None
    assert summary.status == "failed"
    assert summary.overview is None


def test_generate_summary_api_error_marks_failed(db, config, prompt_template, sample_articles):
    """Test that API errors mark summary as failed."""
    story, articles = sample_articles

    def fake_call_ai(articles, config, prompt_template):
        # Return error
        return None, "API connection failed"

    with patch("summarize.call_ai_api", side_effect=fake_call_ai):
        delta, error = generate_summary_for_story(db, story.id, config, prompt_template, 0)

    assert delta == 1
    assert error is not None

    # Check that summary was stored with failed status
    summary = db.query(Summary).filter(Summary.story_id == story.id).first()
    assert summary is not None
    assert summary.status == "failed"


def test_generate_summary_insufficient_evidence_stored(db, config, prompt_template, sample_articles):
    """Test that insufficient_evidence flag is stored correctly."""
    story, articles = sample_articles

    def fake_call_ai(articles, config, prompt_template):
        output = {
            "overview": "Not enough info",
            "agreement": "",
            "uncertainty": "",
            "perspectives": [],
            "insufficient_evidence": True
        }
        return json.dumps(output), None

    with patch("summarize.call_ai_api", side_effect=fake_call_ai):
        delta, error = generate_summary_for_story(db, story.id, config, prompt_template, 0)

    assert delta == 1
    assert error is None

    # Check that summary was stored
    summary = db.query(Summary).filter(Summary.story_id == story.id).first()
    assert summary is not None
    assert summary.status == "ok"
    assert summary.insufficient_evidence is True


def test_generate_summary_stores_perspectives(db, config, prompt_template, sample_articles):
    """Test that perspectives are stored correctly."""
    story, articles = sample_articles

    def fake_call_ai(articles, config, prompt_template):
        output = {
            "overview": "Story overview",
            "agreement": "",
            "uncertainty": "",
            "perspectives": [
                {
                    "name": "Perspective A",
                    "summary": "This viewpoint holds X",
                    "article_ids": [1]
                }
            ],
            "insufficient_evidence": False
        }
        return json.dumps(output), None

    with patch("summarize.call_ai_api", side_effect=fake_call_ai):
        delta, error = generate_summary_for_story(db, story.id, config, prompt_template, 0)

    assert delta == 1
    assert error is None

    # Check that summary was stored
    summary = db.query(Summary).filter(Summary.story_id == story.id).first()
    assert summary is not None
    assert summary.status == "ok"
    assert summary.perspectives_json is not None
    assert len(summary.perspectives_json) == 1
    assert summary.perspectives_json[0]["name"] == "Perspective A"
