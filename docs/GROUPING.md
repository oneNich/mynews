# Story Grouping Method

## Overview

The story grouping system identifies when multiple articles from **different publishers** cover the same event and groups them into a single story. This allows readers to see different perspectives on the same news event from multiple sources. **Same-publisher articles are never grouped together** — each publisher's coverage of an event remains separate.

## Algorithm

1. **Identify ungrouped articles**: Find all articles with `story_id = NULL` (newly ingested articles)

2. **Find candidates**: For each ungrouped article, search for matching articles published in the last 7 days from **different publishers** that either:
   - Already belong to a story, OR
   - Are also ungrouped

3. **Cross-publisher-only rule**: Articles can ONLY be considered for grouping if their best match comes from a different publisher. Same-publisher matches are rejected and never cause a join.

4. **TF-IDF vectorization**: Convert the article's title and summary text into a TF-IDF vector using English stop words, comparing it to cross-publisher candidate articles

5. **Apply three filters** (ALL must pass to join):
   - **Similarity threshold**: Cosine similarity between the TF-IDF vectors must be >= 0.40
   - **Time window**: Articles must be published within 168 hours (7 days) of each other
   - **Named entity overlap**: The articles must share at least 2 capitalized non-stopword terms (names, places, organizations)

6. **Group or create**: If a match passes all filters, assign the article to that story's ID. Otherwise, create a new story with the article's title as the headline.

7. **Update headlines**: For each story, set its headline to the title of its most recently published article.

## Thresholds

- `SIMILARITY_THRESHOLD_CROSS_PUBLISHER = 0.40` – Minimum cosine similarity for cross-publisher matches
- `TIME_WINDOW_HOURS = 168` – Maximum hours (7 days) between article publication times to match
- `Minimum capitalized terms = 2` – Minimum shared names/places to confirm relevance

## Cross-Publisher-Only Rule Trade-off

**Benefit**: Prevents same-publisher false positives where a news outlet covers multiple unrelated aspects of the same person or location (e.g., Fox News articles about LeBron James' helicopter commute vs. Carmelo Anthony's opinion about LeBron).

**Trade-off**: A single publisher that provides the only coverage of an event will create a one-article story. Readers see that publisher alone for that story, not as part of a broader cross-publisher narrative. This is intentional—it preserves editorial independence and avoids artificially merging a publisher's different angles on the same topic.

## Known Limitations & Failure Modes

### Scenario: Single-publisher stories

If only one news outlet covers an event within the 7-day window, that event appears as a single-source story. This is by design—the cross-publisher-only rule prioritizes avoiding same-source false merges over multi-source coverage aggregation.

### Scenario: False negatives (cross-publisher events that should group but don't)

If two articles from different publishers use completely different named entities to describe the same event, they will fail to group. For example:

- Article A (Fox News): "Biden announces new climate initiative" (emphasizes "Biden")
- Article B (NPR): "White House unveils environmental protection plan" (emphasizes "White House" instead of "Biden")

These share only one capitalized term (or possibly none, if they use different names for the same entity), so they would not group despite covering the same event. The 2-term requirement was chosen to avoid false positives, but it means closely related stories with minimal entity overlap will remain separate.

### Scenario: False positives (different cross-publisher events grouped together)

If the TF-IDF similarity score happens to be high (>= 0.40) between two unrelated articles from different publishers mentioning the same person or place, they could incorrectly group. However, the 168-hour time window and requirement for multiple shared capitalized terms significantly reduces this risk in practice.

