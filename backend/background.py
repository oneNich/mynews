import re
import httpx
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models import Story, BackgroundLink, Article


def extract_named_entities(text):
    """Extract 1-3 key named entities (capitalized words and phrases preferred)."""
    if not text:
        return []

    # Extract all capitalized words
    words = re.findall(r'\b[A-Z][a-z]+\b', text)

    if not words:
        return []

    # Count occurrences of each word (frequent words are likely entities)
    from collections import Counter
    word_counts = Counter(words)

    entities = []
    used_words = set()

    # First, try to extract a 2-word name from the beginning (like "Ilhan Omar")
    if len(words) >= 2:
        # Check if first two words form a name-like pattern
        first_pair = f"{words[0]} {words[1]}"
        # Only add if both words appear only once or twice (not verb-like patterns)
        if word_counts[words[0]] <= 3 and word_counts[words[1]] <= 3:
            entities.append(first_pair)
            used_words.add(words[0])
            used_words.add(words[1])

    # Add most common single words (that haven't been used)
    for word, count in word_counts.most_common(10):
        if len(entities) >= 3:
            break
        if word not in used_words:
            entities.append(word)
            used_words.add(word)

    return entities[:3]


def query_wikipedia(entity):
    """Query Wikipedia search API for an entity."""
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "format": "json",
            "srlimit": "3",
            "srsearch": entity,
        }
        headers = {
            "User-Agent": "MyNewsStudentProject/1.0 (Educational; +http://localhost)",
        }

        response = httpx.get(url, params=params, headers=headers, timeout=5.0)
        # Don't raise for 403 - just return empty results
        if response.status_code == 403:
            return []
        response.raise_for_status()
        data = response.json()

        results = data.get("query", {}).get("search", [])
        return results
    except Exception as e:
        return []


def filter_result_by_article_text(result, article_text):
    """Keep result only if words of page title appear in article text."""
    title = result.get("title", "")
    if not title:
        return False

    # Extract words from page title (lowercase for matching)
    title_words = set(re.findall(r'\b\w+\b', title.lower()))

    # Extract words from article text (lowercase for matching)
    text_words = set(re.findall(r'\b\w+\b', article_text.lower()))

    # Check if title words appear in article text
    # Require at least one word to match
    return bool(title_words & text_words)


def build_wikipedia_url(title):
    """Build Wikipedia URL from page title."""
    return f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"


def find_background_links(db: Session, story: Story, existing_links_count=0):
    """Find background links for a story using Wikipedia search."""
    if existing_links_count >= 3:
        return []

    # Get articles for this story
    articles = db.query(Article).filter(Article.story_id == story.id).all()
    if not articles:
        return []

    # Combine headline and article titles for entity extraction
    combined_text = story.headline + " " + " ".join(a.title for a in articles)

    # Extract named entities
    entities = extract_named_entities(combined_text)
    if not entities:
        return []

    # Combine all article text for filtering
    article_text = combined_text + " " + " ".join(a.summary_text or "" for a in articles)

    found_links = []
    processed_titles = set()

    for entity in entities:
        if len(found_links) >= 3:
            break

        results = query_wikipedia(entity)

        for result in results:
            if len(found_links) >= 3:
                break

            title = result.get("title", "")
            if not title or title in processed_titles:
                continue

            processed_titles.add(title)

            # Check if result matches article text
            if filter_result_by_article_text(result, article_text):
                url = build_wikipedia_url(title)
                found_links.append({
                    "title": title,
                    "url": url,
                    "source": "Wikipedia",
                })

    return found_links[:3 - existing_links_count]


def add_background_links(db: Session, story_id):
    """Add background links for a specific story if not already present."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        return 0

    # Check existing links
    existing_links = db.query(BackgroundLink).filter(BackgroundLink.story_id == story_id).all()

    # Find new links
    new_links = find_background_links(db, story, len(existing_links))

    # Save new links
    count = 0
    for link_data in new_links:
        link = BackgroundLink(
            story_id=story_id,
            title=link_data["title"],
            url=link_data["url"],
            source=link_data["source"],
        )
        db.add(link)
        count += 1

    if count > 0:
        db.commit()

    return count


def process_background_links(db: Session):
    """Process background links for new stories or those with changed articles.

    Returns count of links added.
    """
    total_added = 0
    errors = []

    try:
        # Get stories that don't have background links yet
        # (new stories or ones with changed articles since links were made)
        stories = db.query(Story).all()

        for story in stories:
            try:
                # Skip if story already has background links
                existing = db.query(BackgroundLink).filter(
                    BackgroundLink.story_id == story.id
                ).count()

                if existing > 0:
                    continue

                added = add_background_links(db, story.id)
                total_added += added
            except Exception as e:
                errors.append(f"Story {story.id}: {str(e)}")
    except Exception as e:
        errors.append(f"Fatal error in process_background_links: {str(e)}")

    return total_added, errors
