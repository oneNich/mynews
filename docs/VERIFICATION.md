# Verification Checklist

This table documents the 12 verification checks for My News, how each was tested, and their results.

| Check | How I Tested | Actual Result | Evidence File |
|-------|-------------|---------------|---------------|
| **Repeated ingestion** | Run `worker.py` twice on the same RSS feeds; verify articles deduplicated by `url_norm` (case-normalized, path lowercased) | [FILL IN] | [FILL IN] |
| **Same event, different publishers** | Fetch articles about the same headline from Fox, NPR, BBC; verify grouping algorithm assigns all to same story | [FILL IN] | [FILL IN] |
| **Similar topic, different events** | Feed articles on different events (e.g., two unrelated elections); verify cross-publisher rule prevents false merge | [FILL IN] | [FILL IN] |
| **Hourly automation** | Check GitHub Actions `collect.yml` runs cron `'7 * * * *'` (7 min past each hour); verify `worker.py` completes within time window | [FILL IN] | [FILL IN] |
| **Seven-day boundary** | Create articles at 168h boundary; verify retention deletes those with `published_at < now - 168h` | [FILL IN] | [FILL IN] |
| **Source expiration inside a group** | Group story with 3 articles; expire one; verify story remains, summary pending, then set to ok after regeneration | [FILL IN] | [FILL IN] |
| **Shared AI output** | Request same story twice from API; verify both clients read identical summary (no duplicate API calls via `input_hash`) | [FILL IN] | [FILL IN] |
| **Provider failure (Wikipedia)** | Test with Wikipedia API off; verify background link generation fails gracefully (logged, no crash) | [FILL IN] | [FILL IN] |
| **Provider failure (Anthropic)** | Test with bad API key; verify summary status set to "failed", error logged, no made-up text | [FILL IN] | [FILL IN] |
| **Client connectivity failure** | Disable network on phone; tap story; verify offline banner with cached data, Retry button, note re: background links | [FILL IN] | [FILL IN] |
| **Physical-phone presentation** | Install APK on Android phone; verify all buttons ≥48dp, fonts readable, no endless spinners, story cards tap to detail | [FILL IN] | [FILL IN] |
| **Beta-readiness regression** | Run full workflow: fetch RSS → group → background → summary → API → Flutter; verify no crashes, all data present, UI responsive | [FILL IN] | [FILL IN] |
