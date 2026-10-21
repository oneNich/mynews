# Defect Log

Tracking bugs, issues, and fixes for My News.

| ID | Severity | Description | Steps to Reproduce | Status | Fix Verified |
|----|----------|-------------|-------------------|--------|--------------|
| 001 | Major | Invented package version in requirements.txt | Pin `anthropic==0.7.11` in backend/requirements.txt and run `pip install -r requirements.txt` | Fixed | Yes - Changed to anthropic==1.16.0; Render deploy succeeded |
| 002 | Major | Outdated, conflicting package pins | Pin old fastapi==0.104.1 with anthropic==1.16.0; run `pip install -r requirements.txt` | Fixed | Yes - Removed exact version pins; pip resolves compatible versions |
| 003 | Major | Database silently fell back to SQLite instead of Supabase | Run worker.py without calling load_dotenv() in db.py; check engine.url | Fixed | Yes - Added `from dotenv import load_dotenv` and `load_dotenv()` to db.py |
| 004 | Major | Out-of-scope change: normalize_url lowercased URL path breaking spec | Run ingestion with URLs containing uppercase paths; check deduplication | Fixed | Yes - Reverted ingest.py; corrected test_dedup_upsert to match spec (lowercase host only) |
| 005 | Major | Grouping algorithm produced 0 multi-publisher stories; same-publisher false merges | Run P6 grouping on live Supabase data; query stories table for publisher_count and headlines | Fixed | Yes - Process unassigned articles oldest first; cross-publisher-only rule; threshold 0.40; fixed checker to use real database |
| 006 | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] | [FILL IN] |
