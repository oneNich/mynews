# Progress
## Current step
P7 (next step TBD)
## Done
- P1 Spec file (tag p1-done)
- P5 Retention and cleanup (tag p5-done)
- P6 Story grouping - fixed (tag p6-done)
- P6 fix 2 - false merges (tag p6-fix2-done)
- P6 fix 3 - cross-publisher-only (tag p6-fix3-done)
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
## Known issues
- "Test" publisher articles only used in test data (in-memory databases), no production risk, but regroup.py deletes any if they exist
  - Found in backend/tests/test_ingest.py:132,143 and backend/tests/test_retention.py:30,37,67,107,148,156,196,220 (all test functions with in-memory SQLite)
## Deployed URLs
- API: https://mynews-fdgy.onrender.com/
