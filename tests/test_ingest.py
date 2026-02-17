# pyright: reportMissingImports=false
import json
from pathlib import Path

from phase1_youtube import ingest


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
GOLDEN_DIR = FIXTURES_DIR / "golden"


def _load_jsonl_records(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _assert_jsonl_matches_golden(output_path, golden_name):
    output_lines = output_path.read_text(encoding="utf-8").splitlines()
    golden_lines = (GOLDEN_DIR / golden_name).read_text(encoding="utf-8").splitlines()
    assert output_lines == golden_lines


def test_main_offline_fixtures_writes_jsonl_and_manifest(tmp_path):
    output_path = tmp_path / "run.jsonl"

    exit_code = ingest.main(
        [
            "--regions",
            "JP,US",
            "--top-n",
            "2",
            "--offline-fixtures",
            str(FIXTURES_DIR),
            "--out",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()

    manifest_path = tmp_path / "run.jsonl.manifest.json"
    assert manifest_path.exists()

    records = _load_jsonl_records(output_path)
    assert len(records) == 4
    assert [(row["region"], row["rank"]) for row in records] == [
        ("JP", 1),
        ("JP", 2),
        ("US", 1),
        ("US", 2),
    ]

    for record in records:
        assert set(record.keys()) == {
            "schema_version",
            "region",
            "rank",
            "video_id",
            "title",
            "description",
            "transcript_status",
            "transcript_provenance",
            "transcript_text",
        }

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["counts"] == {
        "total_records": 4,
        "regions": {"JP": 2, "US": 2},
    }
    assert manifest["error_count"] == 0
    assert manifest["errors"] == []
    assert manifest["run_id"] == "offline_jp-us_top2"


def test_main_invalid_region_returns_nonzero_with_deterministic_error(tmp_path, capsys):
    output_path = tmp_path / "run.jsonl"

    exit_code = ingest.main(
        [
            "--regions",
            "JP,XX",
            "--top-n",
            "2",
            "--offline-fixtures",
            str(FIXTURES_DIR),
            "--out",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert (
        captured.err
        == "ERROR: regions: unsupported region 'XX' (supported: JP,US)\n"
    )
    assert not output_path.exists()


def test_main_offline_fixtures_matches_default_golden_jsonl_and_transcript_statuses(tmp_path):
    output_path = tmp_path / "run.jsonl"

    exit_code = ingest.main(
        [
            "--regions",
            "JP,US",
            "--top-n",
            "2",
            "--offline-fixtures",
            str(FIXTURES_DIR),
            "--out",
            str(output_path),
        ]
    )

    assert exit_code == 0
    _assert_jsonl_matches_golden(output_path, "offline_top2_default.jsonl")

    records = _load_jsonl_records(output_path)
    assert [record["transcript_status"] for record in records] == [
        "official_unavailable",
        "official_unavailable",
        "official_unavailable",
        "official_unavailable",
    ]
    assert [record["transcript_provenance"] for record in records] == [
        "none",
        "none",
        "none",
        "none",
    ]


def test_main_offline_fixtures_transcript_status_mix_matches_golden(tmp_path, monkeypatch):
    output_path = tmp_path / "run.jsonl"
    statuses_by_video = {
        "jp_video_001": {
            "transcript_status": "official_ok",
            "transcript_provenance": "official",
            "transcript_text": "Official JP transcript",
        },
        "jp_video_002": {
            "transcript_status": "asr_ok",
            "transcript_provenance": "asr",
            "transcript_text": "ASR JP transcript",
        },
        "us_video_001": {
            "transcript_status": "asr_failed",
            "transcript_provenance": "asr",
            "transcript_text": "",
        },
        "us_video_002": {
            "transcript_status": "skipped_quota",
            "transcript_provenance": "asr",
            "transcript_text": "",
        },
    }

    def fake_resolve_transcripts(records, **_kwargs):
        resolved = []
        for record in records:
            status_payload = statuses_by_video[record["video_id"]]
            resolved_record = dict(record)
            resolved_record.update(status_payload)
            resolved.append(resolved_record)
        return resolved

    monkeypatch.setattr(ingest, "resolve_transcripts", fake_resolve_transcripts)

    exit_code = ingest.main(
        [
            "--regions",
            "JP,US",
            "--top-n",
            "2",
            "--offline-fixtures",
            str(FIXTURES_DIR),
            "--out",
            str(output_path),
        ]
    )

    assert exit_code == 0
    _assert_jsonl_matches_golden(output_path, "offline_top2_status_mix.jsonl")

    records = _load_jsonl_records(output_path)
    assert [record["transcript_status"] for record in records] == [
        "official_ok",
        "asr_ok",
        "asr_failed",
        "skipped_quota",
    ]
