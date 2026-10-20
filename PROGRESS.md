# Progress
## Current step
P6 Story grouping (complete - ready for next step)
## Done
- P1 Spec file (tag p1-done)
- P5 Retention and cleanup (tag p5-done)
- P6 Story grouping (tag p6-done)
## Decisions made
- Articles and stories are filtered by published_at >= now - 168h in API queries
- Retention runs at the end of every worker.py run and deletes expired articles, orphaned stories, and their related records
- Summary status is set to 'pending' when a story loses an article but retains others
- Story grouping uses TF-IDF similarity (>= 0.30) + 48-hour time window + 2+ shared capitalized entities
- Conservative thresholds prevent false positives; single-source stories are created when no match found
- URL normalization includes lowercasing path to handle duplicate detection correctly
## Known issues
- none
## Deployed URLs
- API: https://mynews-fdgy.onrender.com/
