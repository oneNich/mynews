import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, urlunparse
import feedparser
import httpx
from sqlalchemy.orm import Session
from models import Article, Story

FEEDS = {
    "Fox News": "https://moxie.foxnews.com/google-publisher/latest.xml?format=xml",
    "NPR": "https://feeds.npr.org/1001/rss.xml",
    "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
}

TIMEOUT_SECONDS = 10
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
HOURS_WINDOW = 168


def strip_html(html_text):
    if not html_text:
        return ""
    return re.sub(r"<[^>]+>", "", html_text).strip()


def normalize_url(url):
    """Normalize URL: lowercase host, drop query/fragment, drop trailing slash."""
    try:
        parsed = urlparse(url)
        normalized = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            "",
            "",
            "",
        ))
        return normalized if normalized else url
    except:
        return url


def parse_published_date(entry):
    """Extract and parse published date, return UTC datetime or None."""
    for date_field in ["published", "updated"]:
        if date_field in entry and entry[date_field]:
            try:
                dt = entry[date_field + "_parsed"]
                if dt:
                    return datetime(*dt[:6], tzinfo=timezone.utc)
            except:
                pass
    return None


def article_from_feed_item(entry, publisher):
    """Normalize a feedparser entry to article data."""
    title = entry.get("title", "").strip()
    url = entry.get("link", "").strip()

    if not title or not url:
        return None

    published_at = parse_published_date(entry)
    if not published_at:
        return None

    now = datetime.now(timezone.utc)
    if now - published_at > timedelta(hours=HOURS_WINDOW):
        return None

    summary_text = ""
    for field in ["summary", "description"]:
        if field in entry and entry[field]:
            summary_text = strip_html(entry[field])
            break

    return {
        "url": url,
        "url_norm": normalize_url(url),
        "publisher": publisher,
        "title": title,
        "summary_text": summary_text,
        "published_at": published_at,
    }


def fetch_feed(publisher, feed_url):
    """Fetch and parse a single feed. Returns list of normalized articles or empty list on error."""
    try:
        headers = {"User-Agent": USER_AGENT}
        response = httpx.get(feed_url, timeout=TIMEOUT_SECONDS, headers=headers)
        response.raise_for_status()

        feed = feedparser.parse(response.text)
        articles = []
        skipped = 0

        for entry in feed.get("entries", []):
            article = article_from_feed_item(entry, publisher)
            if article:
                articles.append(article)
            else:
                skipped += 1

        return articles, skipped, None
    except Exception as e:
        return [], 0, str(e)


def ingest(db: Session):
    """Ingest all feeds, upsert articles, return stats."""
    stats = {
        "articles_fetched": 0,
        "articles_new": 0,
        "articles_expired": 0,
        "errors": {},
    }

    for publisher, feed_url in FEEDS.items():
        articles, skipped, error = fetch_feed(publisher, feed_url)
        stats["articles_fetched"] += len(articles) + skipped

        if error:
            stats["errors"][publisher] = error
            continue

        for article_data in articles:
            existing = db.query(Article).filter_by(url_norm=article_data["url_norm"]).first()

            if existing:
                existing.title = article_data["title"]
                existing.summary_text = article_data["summary_text"]
            else:
                new_article = Article(**article_data)
                db.add(new_article)
                stats["articles_new"] += 1

        db.commit()

    return stats
