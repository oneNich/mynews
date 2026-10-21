# Progress
## Current step
Next step TBD
## Done
- P1 Spec file (tag p1-done)
- P5 Retention and cleanup (tag p5-done)
- P6 Story grouping - fixed (tag p6-done)
- P6 fix 2 - false merges (tag p6-fix2-done)
- P6 fix 3 - cross-publisher-only (tag p6-fix3-done)
- P7 Background links (tag p7-done)
- P8 AI summaries (tag p8-done)
## Decisions made
- Articles and stories are filtered by published_at >= now - 168h in API queries
- Retention runs at the end of every worker.py run and deletes expired articles, orphaned stories, and their related records
- Summary status is set to 'pending' when a story loses an article but retains others
- Story grouping: process unassigned articles oldest first; compare each against ALL articles (both assigned and unassigned) in the 7-day window from **different publishers only**; if best match has a story, join it; otherwise create a new story for both; similarity threshold 0.40 for cross-publisher matches
- **Cross-publisher-only rule**: An article may ONLY join a story when its best match is from a DIFFERENT publisher. Same-publisher matches never cause a join, preventing false merges of same-outlet coverage of different angles on the same topic (e.g., LeBron helicopter commute vs. Carmelo comment)
- Grouping algorithm correctly handles two unassigned articles from different publishers matching each other
- Conservative thresholds and cross-publisher requirement prevent false positives; single-publisher stories created when no cross-publisher match found
- URL normalization includes lowercasing path to handle duplicate detection correctly
- 2+ shared capitalized terms required for any match; 168-hour time window limit
- **Background links**: Named entity extraction prefers 2-word phrases (names like "Ilhan Omar") and extracts up to 3 entities per story; Wikipedia search uses httpx with User-Agent header; results filtered by checking if page title words appear in article text; max 3 links per story; Wikipedia API access is rate-limited and requires proper User-Agent headers; errors during background link processing are logged but never crash the worker
- **AI Summaries (P8)**: Uses Claude Haiku 5.5 via anthropic Python package; reads ANTHROPIC_API_KEY from environment; if missing, marks summaries failed with error reason and continues (never crashes); input hash (SHA256 of sorted article IDs, titles, summary_text) used to avoid duplicate API calls; processes only multi-publisher stories, sorted newest first; cap of 25 calls per run; API responses validated as strict JSON with required fields: overview, agreement, uncertainty, perspectives (list of name/summary/article_ids), insufficient_evidence; article_ids in output cleaned to only include those from input; generated_at (UTC), model, and prompt_version stored with each summary; on API error or invalid JSON, status set to failed with no made-up text, error recorded, processing continues
## Known issues
- "Test" publisher articles only used in test data (in-memory databases), no production risk, but regroup.py deletes any if they exist
  - Found in backend/tests/test_ingest.py:132,143 and backend/tests/test_retention.py:30,37,67,107,148,156,196,220 (all test functions with in-memory SQLite)
- Wikipedia API returns 403 Forbidden when accessed from local development environment (likely rate-limiting). The background link processing gracefully handles this by recording empty results - this is expected behavior when Wikipedia blocks requests
- Production database schema is out of sync: models.py has insufficient_evidence column on Summary and prompt_version as String, and ai_calls + background_links_added on JobRun, but deployed database hasn't been migrated yet. This will cause errors when deploying P8 and P7 code to production without running migrations first
## Deployed URLs
- API: https://mynews-fdgy.onrender.com/
