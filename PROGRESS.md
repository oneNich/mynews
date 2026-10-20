# Progress
## Current step
P7 (next step TBD)
## Done
- P1 Spec file (tag p1-done)
- P5 Retention and cleanup (tag p5-done)
- P6 Story grouping - fixed (tag p6-done)
## Decisions made
- Articles and stories are filtered by published_at >= now - 168h in API queries
- Retention runs at the end of every worker.py run and deletes expired articles, orphaned stories, and their related records
- Summary status is set to 'pending' when a story loses an article but retains others
- Story grouping: process unassigned articles oldest first; compare each against ALL articles (both assigned and unassigned) in the 7-day window; if best match has a story, join it; otherwise create a new story for both; similarity threshold 0.40 (was 0.30 causing false positives)
- Grouping algorithm now correctly handles two unassigned articles matching each other and grouping into the same story
- Conservative thresholds prevent false positives; single-source stories are created when no match found
- URL normalization includes lowercasing path to handle duplicate detection correctly
## Known issues
- "Test" publisher articles only used in test data (in-memory databases), no production risk, but regroup.py deletes any if they exist
  - Found in backend/tests/test_ingest.py:132,143 and backend/tests/test_retention.py:30,37,67,107,148,156,196,220 (all test functions with in-memory SQLite)
## Deployed URLs
- API: https://mynews-fdgy.onrender.com/
