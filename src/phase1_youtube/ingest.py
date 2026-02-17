import argparse
import os
import sys

from phase1_youtube.config import ConfigError, load_config
from phase1_youtube.fixture_harness import load_json_fixture
from phase1_youtube.normalizer import normalize_trending_records
from phase1_youtube.sink import write_jsonl_and_manifest
from phase1_youtube.transcript_resolver import resolve_transcripts
from phase1_youtube.trending_fetcher import fetch_most_popular_by_regions
from phase1_youtube.youtube_client import YouTubeVideosClient


SUPPORTED_REGIONS = ("JP", "US")


def _parse_regions(value):
    if not isinstance(value, str):
        raise ValueError("regions: expected comma-separated string")

    raw_tokens = value.split(",")
    regions = []
    for token in raw_tokens:
        normalized = token.strip().upper()
        if not normalized:
            continue
        if normalized not in SUPPORTED_REGIONS:
            raise ValueError(
                "regions: unsupported region '{0}' (supported: {1})".format(
                    normalized,
                    ",".join(SUPPORTED_REGIONS),
                )
            )
        if normalized not in regions:
            regions.append(normalized)

    if not regions:
        raise ValueError("regions: at least one region is required")

    return regions


def _build_manifest_errors(errors_by_region):
    errors = []
    for region in sorted(errors_by_region.keys()):
        errors.append(
            {
                "code": "fetch_error",
                "region": region,
                "detail": errors_by_region[region],
            }
        )
    return errors


def _ensure_parent_dir(file_path):
    parent_dir = os.path.dirname(file_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)


def _canonicalize_records(resolved_records):
    canonical_records = []
    for record in resolved_records:
        canonical_records.append(
            {
                "schema_version": record["schema_version"],
                "region": record["region"],
                "rank": record["rank"],
                "video_id": record["video_id"],
                "title": record["title"],
                "description": record["description"],
                "transcript_status": record["transcript_status"],
                "transcript_provenance": record["transcript_provenance"],
                "transcript_text": record["transcript_text"],
            }
        )
    return canonical_records


class _OfflineFixtureVideosClient(object):
    def __init__(self, fixtures_dir):
        self._fixtures_dir = fixtures_dir

    def videos_list(self, **kwargs):
        region = kwargs.get("regionCode")
        if region is None:
            raise ValueError("videos_list: missing required argument 'regionCode'")

        fixture_name = "youtube_videos_list_{0}.json".format(region.lower())
        return load_json_fixture(self._fixtures_dir, fixture_name)


def _build_live_videos_client():
    try:
        from googleapiclient.discovery import build
    except ImportError:
        raise RuntimeError("google-api-python-client is required for live mode")

    config = load_config()
    service = build(
        "youtube",
        "v3",
        developerKey=config["youtube_api_key"],
    )
    return YouTubeVideosClient(
        service=service,
        timeout_seconds=config["youtube_timeout_seconds"],
    )


def _build_run_id(regions, top_n, offline_mode):
    mode = "offline" if offline_mode else "live"
    return "{0}_{1}_top{2}".format(mode, "-".join(regions).lower(), top_n)


def run_pipeline(regions, top_n, out_path, offline_fixtures=None):
    if top_n < 1:
        raise ValueError("top_n must be >= 1")

    videos_client = (
        _OfflineFixtureVideosClient(offline_fixtures)
        if offline_fixtures
        else _build_live_videos_client()
    )

    fetch_result = fetch_most_popular_by_regions(
        videos_client=videos_client,
        regions=regions,
        top_n=top_n,
    )
    normalized_records = normalize_trending_records(fetch_result["records_by_region"])
    resolved_records = resolve_transcripts(normalized_records)
    canonical_records = _canonicalize_records(resolved_records)

    _ensure_parent_dir(out_path)
    manifest_path = "{0}.manifest.json".format(out_path)
    manifest = write_jsonl_and_manifest(
        records=canonical_records,
        jsonl_path=out_path,
        manifest_path=manifest_path,
        quota=None,
        errors=_build_manifest_errors(fetch_result["errors_by_region"]),
        run_id=_build_run_id(regions, top_n, bool(offline_fixtures)),
    )

    return {
        "records": canonical_records,
        "manifest": manifest,
        "jsonl_path": out_path,
        "manifest_path": manifest_path,
    }


def _build_parser():
    parser = argparse.ArgumentParser(
        description="Run YouTube JP/US trending Shorts ingestion pipeline"
    )
    parser.add_argument("--regions", required=True, help="Comma-separated region list")
    parser.add_argument("--top-n", type=int, default=20, help="Top-N videos per region")
    parser.add_argument("--out", required=True, help="Output JSONL file path")
    parser.add_argument(
        "--offline-fixtures",
        default=None,
        help="Fixture directory for offline mode",
    )
    return parser


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        regions = _parse_regions(args.regions)
        run_pipeline(
            regions=regions,
            top_n=args.top_n,
            out_path=args.out,
            offline_fixtures=args.offline_fixtures,
        )
    except (ConfigError, RuntimeError, ValueError) as exc:
        sys.stderr.write("ERROR: {0}\n".format(exc))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
