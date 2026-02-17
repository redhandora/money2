import json

import pytest

from phase1_youtube.schema import SCHEMA_VERSION
from phase1_youtube.sink import build_run_manifest, write_jsonl_and_manifest


def _sample_records():
    return [
        {
            "schema_version": SCHEMA_VERSION,
            "region": "JP",
            "rank": 1,
            "video_id": "jp001",
            "title": "日本語タイトル",
            "description": "説明",
            "transcript_status": "asr_ok",
            "transcript_provenance": "asr",
            "transcript_text": "こんにちは",
        },
        {
            "schema_version": SCHEMA_VERSION,
            "region": "US",
            "rank": 1,
            "video_id": "us001",
            "title": "US title",
            "description": "US description",
            "transcript_status": "official_ok",
            "transcript_provenance": "official",
            "transcript_text": "hello",
        },
    ]


def test_write_jsonl_and_manifest_writes_expected_line_count_and_required_keys(tmp_path):
    records = _sample_records()
    jsonl_path = tmp_path / "trending.jsonl"
    manifest_path = tmp_path / "run_manifest.json"

    manifest = write_jsonl_and_manifest(
        records=records,
        jsonl_path=str(jsonl_path),
        manifest_path=str(manifest_path),
        quota={"used": 250, "limit": 10000, "remaining": 9750},
        errors=[{"code": "jp_warning", "detail": "captions unavailable"}],
        run_id="run-001",
    )

    jsonl_lines = jsonl_path.read_text(encoding="utf-8").splitlines()
    assert len(jsonl_lines) == 2

    expected_first_line = json.dumps(records[0], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    expected_second_line = json.dumps(records[1], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert jsonl_lines == [expected_first_line, expected_second_line]

    persisted_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest == persisted_manifest

    assert set(manifest.keys()) == {
        "manifest_version",
        "schema_version",
        "run_id",
        "output_format",
        "counts",
        "quota",
        "error_count",
        "errors",
    }
    assert manifest["counts"]["total_records"] == 2
    assert manifest["counts"]["regions"] == {"JP": 1, "US": 1}
    assert manifest["quota"] == {"used": 250, "limit": 10000, "remaining": 9750}
    assert manifest["error_count"] == 1


def test_build_run_manifest_rejects_malformed_record_with_explicit_reason():
    malformed_records = _sample_records()
    del malformed_records[0]["video_id"]

    with pytest.raises(ValueError) as exc:
        build_run_manifest(records=malformed_records)

    assert str(exc.value) == "record[0]: video_id: missing required field"
