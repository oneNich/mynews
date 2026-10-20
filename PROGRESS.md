# Progress
## Current step
(check completed steps for current work status)
## Done
- P1 Spec file (tag p1-done)
- P5 Retention and cleanup (tag p5-done)
## Decisions made
- Articles and stories are filtered by published_at >= now - 168h in API queries
- Retention runs at the end of every worker.py run and deletes expired articles, orphaned stories, and their related records
- Summary status is set to 'pending' when a story loses an article but retains others
## Known issues
- none
## Deployed URLs
- API: https://mynews-fdgy.onrender.com/
