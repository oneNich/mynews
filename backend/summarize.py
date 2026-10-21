import json
import os
import hashlib
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import Article, Story, Summary
import anthropic


def load_ai_config():
    """Load AI configuration from ai_config.json."""
    config_path = os.path.join(os.path.dirname(__file__), "ai_config.json")
    with open(config_path, "r") as f:
        return json.load(f)


def load_prompt_template():
    """Load the prompt template from file."""
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "summary_v1.txt")
    with open(prompt_path, "r") as f:
        return f.read()


def compute_input_hash(articles):
    """Compute SHA256 hash of sorted article IDs, titles, and summary_text."""
    if not articles:
        return None

    # Sort by ID to ensure consistent ordering
    sorted_articles = sorted(articles, key=lambda a: a.id)

    # Create a normalized string from article data
    parts = []
    for article in sorted_articles:
        # Include id, title, and summary_text
        part = f"{article.id}|{article.title}|{article.summary_text or ''}"
        parts.append(part)

    combined = "|".join(parts)
    return hashlib.sha256(combined.encode()).hexdigest()


def format_articles_for_prompt(articles):
    """Format articles into the prompt template."""
    if not articles:
        return ""

    # Sort by ID for consistent ordering
    sorted_articles = sorted(articles, key=lambda a: a.id)

    lines = []
    for i, article in enumerate(sorted_articles, 1):
        lines.append(f"[{i}] {article.publisher}")
        lines.append(f"    Title: {article.title}")
        lines.append(f"    Published: {article.published_at}")
        lines.append(f"    {article.summary_text or 'No summary available'}")
        lines.append("")

    return "\n".join(lines)


def validate_and_clean_output(output_json, article_ids):
    """Validate JSON output and ensure all article_ids are from input.

    Returns tuple of (cleaned_output, error_message).
    If output is valid, returns (output, None).
    If output is invalid, returns (None, error_message).
    """
    try:
        data = json.loads(output_json)
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {str(e)}"

    # Validate required fields
    required_fields = ["overview", "agreement", "uncertainty", "perspectives", "insufficient_evidence"]
    for field in required_fields:
        if field not in data:
            return None, f"Missing required field: {field}"

    # Convert article_ids to strings for comparison
    valid_ids_set = set(str(aid) for aid in article_ids)

    # Clean article_ids in perspectives
    if isinstance(data.get("perspectives"), list):
        for perspective in data["perspectives"]:
            if "article_ids" in perspective and isinstance(perspective["article_ids"], list):
                # Keep only article_ids that are in the input (convert to strings for comparison)
                valid_ids = [aid for aid in perspective["article_ids"] if str(aid) in valid_ids_set]
                perspective["article_ids"] = valid_ids

    return data, None


def call_ai_api(articles, config, prompt_template):
    """Call the Anthropic API to generate a summary.

    Returns tuple of (json_output, error_message).
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None, "ANTHROPIC_API_KEY environment variable not set"

    try:
        client = anthropic.Anthropic(api_key=api_key)

        # Format articles for the prompt
        articles_text = format_articles_for_prompt(articles)

        # Fill in the template
        prompt = prompt_template.replace("{articles_text}", articles_text)

        # Call the API
        message = client.messages.create(
            model=config["model"],
            max_tokens=config["max_tokens"],
            temperature=config["temperature"],
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Extract the response text
        response_text = message.content[0].text
        return response_text, None

    except anthropic.APIError as e:
        return None, f"API error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"


def generate_summary_for_story(db: Session, story_id, config, prompt_template, api_call_count):
    """Generate a summary for a story if needed.

    Returns tuple of (api_call_count_delta, error_message).
    If successful, error_message is None.
    If failed, error_message describes the error.
    """
    # Get the story and its articles
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        return 0, f"Story {story_id} not found"

    articles = db.query(Article).filter(Article.story_id == story_id).all()
    if not articles:
        return 0, f"Story {story_id} has no articles"

    # Compute input hash
    new_hash = compute_input_hash(articles)
    article_ids = [str(a.id) for a in articles]

    # Get or create summary
    summary = db.query(Summary).filter(Summary.story_id == story_id).first()
    if not summary:
        summary = Summary(
            story_id=story_id,
            input_hash=new_hash,
            status="pending",
        )
        db.add(summary)
        db.flush()

    # Check if we need to regenerate
    needs_regeneration = (
        summary.status == "pending" or
        summary.status == "failed" or
        summary.input_hash != new_hash
    )

    if not needs_regeneration:
        # Skip - no API call needed
        return 0, None

    # Call the API
    response_text, error_msg = call_ai_api(articles, config, prompt_template)

    if error_msg:
        summary.status = "failed"
        summary.input_hash = new_hash
        db.commit()
        return 1, error_msg

    # Validate and clean the output
    cleaned_output, validation_error = validate_and_clean_output(response_text, article_ids)

    if validation_error:
        summary.status = "failed"
        summary.input_hash = new_hash
        db.commit()
        return 1, f"Output validation failed: {validation_error}"

    # Store the summary
    summary.status = "ok"
    summary.input_hash = new_hash
    summary.overview = cleaned_output.get("overview")
    summary.agreement = cleaned_output.get("agreement") or None
    summary.uncertainty = cleaned_output.get("uncertainty") or None
    summary.insufficient_evidence = cleaned_output.get("insufficient_evidence", False)

    # Store perspectives as JSON
    if cleaned_output.get("perspectives"):
        summary.perspectives_json = cleaned_output["perspectives"]
    else:
        summary.perspectives_json = None

    summary.generated_at = datetime.now(timezone.utc)
    summary.model = config["model"]
    summary.prompt_version = config["prompt_version"]

    db.commit()
    return 1, None


def get_multi_publisher_stories(db: Session):
    """Get all stories with articles from multiple publishers, sorted by newest first."""
    from sqlalchemy import func

    # Get stories with their publisher counts
    story_publisher_counts = db.query(
        Story.id,
        func.count(func.distinct(Article.publisher)).label('publisher_count'),
        func.max(Article.published_at).label('newest_article'),
    ).join(
        Article, Article.story_id == Story.id
    ).group_by(
        Story.id
    ).having(
        func.count(func.distinct(Article.publisher)) > 1
    ).order_by(
        func.max(Article.published_at).desc()
    ).all()

    return [row[0] for row in story_publisher_counts]


def process_summaries(db: Session):
    """Process summaries for stories.

    Returns tuple of (ai_calls_made, errors).
    """
    config = load_ai_config()
    prompt_template = load_prompt_template()

    # Get multi-publisher stories, sorted newest first
    multi_publisher_story_ids = get_multi_publisher_stories(db)

    ai_calls = 0
    errors = []
    max_calls = 25

    for story_id in multi_publisher_story_ids:
        if ai_calls >= max_calls:
            break

        call_delta, error_msg = generate_summary_for_story(
            db, story_id, config, prompt_template, ai_calls
        )
        ai_calls += call_delta
        if error_msg:
            errors.append(f"Story {story_id}: {error_msg}")

    return ai_calls, errors
