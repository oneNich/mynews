from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from models import Article
from db import SessionLocal
import re

SIMILARITY_THRESHOLD = 0.30
TIME_WINDOW_HOURS = 48

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

def main():
    db = SessionLocal()

    # Get all articles from the last 7 days
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    articles = db.query(Article).filter(
        Article.published_at >= cutoff
    ).all()

    print(f"Total articles in 7-day window: {len(articles)}")
    print()

    # Count articles per publisher with empty summary_text
    publishers = {}
    for article in articles:
        if article.publisher not in publishers:
            publishers[article.publisher] = {"total": 0, "empty_summary": 0}
        publishers[article.publisher]["total"] += 1
        if not article.summary_text:
            publishers[article.publisher]["empty_summary"] += 1

    print("Articles per publisher with empty summary_text:")
    for pub in sorted(publishers.keys()):
        counts = publishers[pub]
        print(f"  {pub}: {counts['empty_summary']}/{counts['total']} empty")
    print()

    # Find all pairs from different publishers
    pairs = []

    # Build TF-IDF matrix for all articles
    texts = []
    for article in articles:
        article_text = f"{article.title} {article.summary_text or ''}"
        texts.append(article_text)

    if len(articles) < 2:
        print("Not enough articles to compare")
        db.close()
        return

    try:
        text_vec = TfidfVectorizer(stop_words='english', lowercase=True, max_features=100)
        tfidf_matrix = text_vec.fit_transform(texts)
        similarities = cosine_similarity(tfidf_matrix)
    except:
        print("Error computing TF-IDF")
        db.close()
        return

    # Extract pairs from different publishers
    for i in range(len(articles)):
        for j in range(i + 1, len(articles)):
            if articles[i].publisher != articles[j].publisher:
                score = similarities[i][j]

                if score >= SIMILARITY_THRESHOLD:
                    time_diff = abs((articles[i].published_at - articles[j].published_at).total_seconds() / 3600)

                    if time_diff <= TIME_WINDOW_HOURS:
                        text_i = f"{articles[i].title} {articles[i].summary_text or ''}"
                        text_j = f"{articles[j].title} {articles[j].summary_text or ''}"
                        shared_terms = get_shared_capitalized_terms(text_i, text_j)

                        if len(shared_terms) >= 2:
                            pairs.append({
                                'score': score,
                                'article_i': articles[i],
                                'article_j': articles[j],
                                'hours_apart': time_diff,
                                'shared_terms': shared_terms
                            })

    # Sort by score descending and take top 15
    pairs.sort(key=lambda p: p['score'], reverse=True)
    top_pairs = pairs[:15]

    print(f"Top 15 highest-scoring pairs from different publishers:")
    print()

    for idx, pair in enumerate(top_pairs, 1):
        print(f"{idx}. Similarity: {pair['score']:.4f}")
        print(f"   Hours apart: {pair['hours_apart']:.1f}")
        print(f"   Shared terms: {', '.join(sorted(pair['shared_terms']))}")
        print(f"   Article 1: {pair['article_i'].title}")
        print(f"              ({pair['article_i'].publisher})")
        print(f"   Article 2: {pair['article_j'].title}")
        print(f"              ({pair['article_j'].publisher})")
        print()

    db.close()

if __name__ == "__main__":
    main()
