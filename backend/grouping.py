from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from models import Article, Story
import re

SIMILARITY_THRESHOLD_SAME_PUBLISHER = 0.60
SIMILARITY_THRESHOLD_CROSS_PUBLISHER = 0.40
TIME_WINDOW_HOURS = 168

def extract_capitalized_terms(text):
    """Extract capitalized non-stopword terms (likely names/places)."""
    if not text:
        return set()
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
    return set(words)

def get_shared_capitalized_terms(text1, text2):
    """Find capitalized terms shared between two texts."""
    terms1 = extract_capitalized_terms(text1)
    terms2 = extract_capitalized_terms(text2)
    return terms1 & terms2

def find_best_matching_article(article, db: Session):
    """Find the best-matching article from the last 7 days for grouping."""
    if not article.published_at:
        return None

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    candidates = db.query(Article).filter(
        Article.id != article.id,
        Article.published_at >= cutoff,
    ).all()

    if not candidates:
        return None

    text_vec = TfidfVectorizer(stop_words='english', lowercase=True, max_features=100)
    article_text = f"{article.title} {article.summary_text or ''}"

    try:
        combined_texts = [article_text] + [
            f"{c.title} {c.summary_text or ''}" for c in candidates
        ]
        tfidf_matrix = text_vec.fit_transform(combined_texts)
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]

        best_idx = similarities.argmax()
        best_score = similarities[best_idx]
        best_candidate = candidates[best_idx]

        threshold = SIMILARITY_THRESHOLD_SAME_PUBLISHER if article.publisher == best_candidate.publisher else SIMILARITY_THRESHOLD_CROSS_PUBLISHER

        if best_score >= threshold:
            time_diff = abs((article.published_at - best_candidate.published_at).total_seconds() / 3600)
            if time_diff <= TIME_WINDOW_HOURS:
                shared_terms = get_shared_capitalized_terms(article_text,
                    f"{best_candidate.title} {best_candidate.summary_text or ''}")
                if len(shared_terms) >= 2:
                    return best_candidate

        return None
    except:
        return None

def group_articles(db: Session):
    """Group articles with NULL story_id to existing stories or create new ones."""
    stats = {
        "stories_created": 0,
        "stories_joined": 0,
    }

    ungrouped = db.query(Article).filter(Article.story_id.is_(None)).order_by(Article.published_at).all()

    for article in ungrouped:
        matching_article = find_best_matching_article(article, db)

        if matching_article:
            if matching_article.story_id:
                article.story_id = matching_article.story_id
                stats["stories_joined"] += 1
            else:
                new_story = Story(headline=article.title)
                db.add(new_story)
                db.flush()
                article.story_id = new_story.id
                matching_article.story_id = new_story.id
                stats["stories_created"] += 1
        else:
            new_story = Story(headline=article.title)
            db.add(new_story)
            db.flush()
            article.story_id = new_story.id
            stats["stories_created"] += 1

    db.commit()

    for story_id in db.query(Article.story_id).distinct():
        if story_id[0]:
            articles_in_story = db.query(Article).filter(Article.story_id == story_id[0]).all()
            if articles_in_story:
                most_recent = max(articles_in_story, key=lambda a: a.published_at or datetime.min)
                story = db.query(Story).filter(Story.id == story_id[0]).first()
                if story:
                    story.headline = most_recent.title
                    story.updated_at = most_recent.published_at or datetime.now(timezone.utc)

    db.commit()
    return stats
