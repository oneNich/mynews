# Story Grouping Method

## Overview

The story grouping system identifies when multiple articles from different publishers cover the same event and groups them into a single story. This allows readers to see different perspectives on the same news event from multiple sources.

## Algorithm

1. **Identify ungrouped articles**: Find all articles with `story_id = NULL` (newly ingested articles)

2. **Find candidates**: For each ungrouped article, search for matching articles published in the last 7 days that already belong to a story

3. **TF-IDF vectorization**: Convert the article's title and summary text into a TF-IDF vector using English stop words, comparing it to candidate articles

4. **Apply three filters** (ALL must pass to join):
   - **Similarity threshold**: Cosine similarity between the TF-IDF vectors must be >= 0.30
   - **Time window**: Articles must be published within 48 hours of each other
   - **Named entity overlap**: The articles must share at least 2 capitalized non-stopword terms (names, places, organizations)

5. **Group or create**: If a match passes all filters, assign the article to that story's ID. Otherwise, create a new story with the article's title as the headline.

6. **Update headlines**: For each story, set its headline to the title of its most recently published article.

## Thresholds

- `SIMILARITY_THRESHOLD = 0.30` – Minimum cosine similarity to consider TF-IDF match
- `TIME_WINDOW_HOURS = 48` – Maximum hours between article publication times to match
- `Minimum capitalized terms = 2` – Minimum shared names/places to confirm relevance

## Known Limitations & Failure Modes

### Scenario: False negatives (events that should group but don't)

If two articles use completely different named entities to describe the same event, they will fail to group. For example:

- Article A: "Biden announces new climate initiative" (emphasizes "Biden")
- Article B: "White House unveils environmental protection plan" (emphasizes "White House" instead of "Biden")

These share only one capitalized term (or possibly none, if they use different names for the same entity), so they would not group despite covering the same event. The 2-term requirement was chosen to avoid false positives, but it means closely related stories with minimal entity overlap will remain separate.

### Scenario: False positives (different events grouped together)

If the TF-IDF similarity score happens to be high (>= 0.30) between two unrelated articles mentioning the same person or place, they could incorrectly group. However, the 48-hour time window and requirement for multiple shared capitalized terms significantly reduces this risk in practice.
