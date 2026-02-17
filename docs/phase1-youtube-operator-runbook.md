# Phase 1 YouTube Operator Runbook

## Scope

- Pipeline entrypoint: `python -m phase1_youtube.ingest`
- Regions supported by CLI validation: `JP`, `US`
- Output format: JSONL records plus manifest JSON
- Current phase scope: YouTube only

## Prerequisites

- Python 3.6+
- Local execution from repository root
- `PYTHONPATH=src` for module resolution in this `src/` layout

## Environment Variables

### Required for live mode

- `YOUTUBE_API_KEY`

### Optional with defaults

- `YOUTUBE_QUOTA_DAILY_LIMIT` (default `10000`, integer >= 1)
- `YOUTUBE_QUOTA_BUDGET` (default `8000`, integer >= 1, must be <= `YOUTUBE_QUOTA_DAILY_LIMIT`)
- `YOUTUBE_TIMEOUT_SECONDS` (default `30`, integer >= 1)
- `ASR_TIMEOUT_SECONDS` (default `120`, integer >= 1)

### Optional pass-through config fields

- `YOUTUBE_OAUTH_CLIENT_ID`
- `YOUTUBE_OAUTH_CLIENT_SECRET`
- `YOUTUBE_OAUTH_REFRESH_TOKEN`
- `ASR_PROVIDER`
- `ASR_MODEL`

Note: Offline fixture mode does not call `load_config()`, so it does not require `YOUTUBE_API_KEY`.

## CLI Reference

Supported flags in `phase1_youtube.ingest`:

- `--regions` (required): comma-separated list, validated against `JP,US`
- `--top-n` (optional): integer >= 1, default `20`
- `--out` (required): output JSONL file path
- `--offline-fixtures` (optional): fixture directory path, enables offline mode

## Quickstart, Offline

Run:

```bash
PYTHONPATH=src python -m phase1_youtube.ingest --regions JP,US --top-n 2 --offline-fixtures tests/fixtures --out output/task13-offline.jsonl
```

Expected behavior:

- Exit code `0`
- `output/task13-offline.jsonl` created
- `output/task13-offline.jsonl.manifest.json` created
- Manifest `run_id` is `offline_jp-us_top2`

## Live Mode, Missing Key Error Reproduction

Run with no API key:

```bash
env -u YOUTUBE_API_KEY PYTHONPATH=src python -m phase1_youtube.ingest --regions JP,US --top-n 2 --out output/task13-live-no-key.jsonl
```

Expected behavior:

- Exit code `1`
- Stderr contains `ERROR: YOUTUBE_API_KEY: missing required environment variable`
- No output JSONL file created

## Transcript Status Semantics

Output record fields:

- `transcript_status`
- `transcript_provenance`
- `transcript_text`

Status enum and meaning:

- `official_ok`: official transcript resolved, text present
- `official_unavailable`: official transcript unavailable
- `asr_ok`: ASR fallback succeeded, text present
- `asr_failed`: ASR fallback attempted and failed
- `skipped_quota`: ASR skipped because ASR quota unavailable

Operational note for current CLI wiring:

- The CLI currently calls `resolve_transcripts()` without transcript fetcher or ASR transcriber integrations.
- In default runs, records resolve to `official_unavailable` with `transcript_provenance` set to `none` and empty `transcript_text`.

## Error and Quota Playbook

### CLI preflight and config errors

- Invalid region example: `ERROR: regions: unsupported region 'XX' (supported: JP,US)`
- Missing key example: `ERROR: YOUTUBE_API_KEY: missing required environment variable`
- Invalid numeric env example: `ERROR: YOUTUBE_TIMEOUT_SECONDS: expected integer, got 'not-a-number'`
- `--top-n` less than 1: `ERROR: top_n must be >= 1`

Recovery steps:

1. Fix CLI arguments or env values.
2. Re-run command.
3. Confirm exit code is `0`.

### Per-region API failures

- Region fetch failures do not stop other regions.
- Manifest includes one error object per failed region:
  - `code`: `fetch_error`
  - `region`: region code
  - `detail`: exception string from region fetch

Recovery steps:

1. Open `<out>.manifest.json`.
2. Review `errors` and `error_count`.
3. Re-run for affected region only, for example `--regions JP`.

### Quota signals

- Manifest always includes `quota` keys: `used`, `limit`, `remaining`.
- Current CLI writes `quota` as zeroed values because live quota accounting is not yet wired in orchestrator.
- Transcript status `skipped_quota` is supported by resolver semantics and indicates ASR quota gate denied fallback.

Recovery steps:

1. Treat `skipped_quota` rows as partial transcript coverage.
2. Re-run later when ASR quota is available.
3. Keep manifest and JSONL together for audit.

## Operator Checklist

1. Prefer offline fixture run after environment changes to confirm CLI health.
2. For live runs, export `YOUTUBE_API_KEY` first.
3. Validate both `<out>` and `<out>.manifest.json` exist after success.
4. Inspect manifest `error_count` before downstream use.
