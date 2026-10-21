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
- P9 Final API (tag p9-done)
- P10 Flutter app skeleton and story list (tag p10-done)
- P11 Story detail screen (tag p11-done)
- P12 AI analysis and perspective screens (tag p12-done)
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
- **Final API (P9)**: Three read-only endpoints implemented with FastAPI; GET /status returns last successful run time, last run status, and last 5 job runs; GET /stories returns list of stories sorted newest first with id, headline, latest_article_at, publisher_count, article_count, summary_status; GET /stories/{id} returns full story details with publishers grouped by name and their articles, background links, and AI summary; all timestamps as ISO 8601 UTC; expired articles (older than 168h) never appear; pending/failed summaries return status only with null text fields; 404 with JSON message for unknown/expired stories; no filtering/fetching of external data from API endpoints
- **P11 Story detail screen**: Separate file app/lib/screens/story_detail.dart; displays headline and updated_at time; 'Story overview' section shows AI summary with status handling (pending, failed, or ok with label); 'Original coverage' section with buttons per publisher (1 article opens URL in browser, multiple articles show bottom sheet); 'Background' section shows buttons per link or "No background resource available"; 'AI analysis' button shows SnackBar "Coming soon"; url_launcher with externalApplication mode; error handling for link failures shows SnackBar; added https VIEW intent to AndroidManifest.xml <queries>; all buttons have 48dp+ tap targets; screen scrolls to prevent clipping
- **P12 AI analysis and perspective screens**: Two new files - app/lib/screens/ai_analysis.dart and app/lib/screens/perspective.dart; AI analysis screen displays header chip with 'AI-generated | Updated <time>', sections for Overview, Agreement and uncertainty; perspective buttons (or "Insufficient evidence" message if insufficient_evidence=true); supporting articles numbered [1], [2]... with publisher name and title; each article has Open button using url_launcher; footer with "Input scope" text; handles pending/failed status with clear messaging and "Back to original coverage" button; perspective screen shows perspective name in header chip, perspective summary in tinted card (different from article titles), supporting coverage with cited articles numbered [n], other perspectives as buttons with pushReplacement for navigation; all text passed from already-loaded StoryDetail data (no new network calls); AI text styled as body text in Cards, article titles as bold; both screens scroll properly; error handling for URL opens shows SnackBar
## Known issues
- "Test" publisher articles only used in test data (in-memory databases), no production risk, but regroup.py deletes any if they exist
  - Found in backend/tests/test_ingest.py:132,143 and backend/tests/test_retention.py:30,37,67,107,148,156,196,220 (all test functions with in-memory SQLite)
- Wikipedia API returns 403 Forbidden when accessed from local development environment (likely rate-limiting). The background link processing gracefully handles this by recording empty results - this is expected behavior when Wikipedia blocks requests
- Production database schema is out of sync: models.py has insufficient_evidence column on Summary and prompt_version as String, and ai_calls + background_links_added on JobRun, but deployed database hasn't been migrated yet. This will cause errors when deploying P8 and P7 code to production without running migrations first
- Flutter test infrastructure has a known bug in version 3.47.5 (test_core package) that prevents `flutter test` from running in some environments. This is not a code issue - `flutter analyze` validates that all code is correct and follows Dart/Flutter best practices
## Deployed URLs
- API: https://mynews-fdgy.onrender.com/

