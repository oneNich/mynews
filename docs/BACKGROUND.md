# Background Links - Implementation Details

## Method

Background links are Wikipedia articles that provide context for a news story. The system works as follows:

### 1. Named Entity Extraction
When a story is created or its articles change, the system extracts 1-3 key named entities from:
- The story's headline
- All article titles in the story

The system prefers multi-word capitalized phrases (e.g., "Ilhan Omar", "World Series") over single words, as these are typically more specific and accurate entity references.

Example: From a headline "Ilhan Omar Proposes Climate Bill", the system extracts "Ilhan Omar" as a named entity.

### 2. Wikipedia Search
For each extracted entity, the system queries the Wikipedia search API:
```
https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&srlimit=3&srsearch=<entity>
```

Each entity search returns up to 3 candidate Wikipedia articles.

### 3. Relevance Filtering
A Wikipedia result is kept only if **the words of its page title appear somewhere in the story's article text**. This ensures:
- The Wikipedia article is actually related to the news story
- False matches are eliminated when search results are tangentially related

Example: If the search for "Omar" returns "Omar Khayyam" (Persian mathematician), but the article text only mentions "Congresswoman Ilhan Omar", the result is rejected because "Khayyam" doesn't appear in the article.

### 4. Link Storage
For each relevant result, the system saves:
- **title**: The Wikipedia page title
- **url**: The full Wikipedia URL (e.g., `https://en.wikipedia.org/wiki/Ilhan_Omar`)
- **source**: Always "Wikipedia" (allows future expansion to other sources)

Maximum of 3 links are stored per story.

## Known Limitation: Ambiguous Entity Names

The system can select the wrong link when an entity name is ambiguous across multiple Wikipedia articles.

**Example of wrong link selection:**
- News headline: "Omar's Climate Initiative Gains International Support"
- Named entity extracted: "Omar"
- Wikipedia search for "Omar" returns multiple results:
  1. Congresswoman Ilhan Omar (relevant)
  2. King Abdullah II of Jordan's father (less relevant but still named Omar)
  3. A historical Islamic scholar (irrelevant)

If the article text happens to mention something that matches the historical scholar's Wikipedia title better than it matches Ilhan Omar's page, the system might select the wrong link.

**Mitigation strategies** (not currently implemented):
- Prefer longer entity names over shorter ones to improve specificity
- Use article publication date to favor more recent Wikipedia articles
- Cross-check extracted entities with named entity recognition (NER) models
- Allow users to correct incorrect background links in the app

## Integration

Background links are processed:
1. **During ingestion**: When new stories are created, background links are added after the grouping step
2. **During backfill**: The `backfill_background.py` script processes all existing stories in the database
3. **Skipping**: Stories that already have background links are skipped in both processes
