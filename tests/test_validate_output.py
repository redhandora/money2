# pyright: reportMissingImports=false
import json

from phase1_youtube import validate_output


def _record(region, rank, video_id):
    return {
        "schema_version": "1.0",
        "region": region,
        "rank": rank,
        "video_id": video_id,
        "title": "title-{0}".format(video_id),
        "description": "description-{0}".format(video_id),
        "transcript_status": "official_unavailable",
        "transcript_provenance": "none",
        "transcript_text": "",
    }


def _write_jsonl(path, records):
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True))
            handle.write("\n")


def test_main_valid_output_returns_zero_and_prints_ok(tmp_path, capsys):
    jsonl_path = tmp_path / "valid.jsonl"
    _write_jsonl(
        jsonl_path,
        [
            _record("JP", 1, "jp_video_001"),
            _record("JP", 2, "jp_video_002"),
            _record("US", 1, "us_video_001"),
        ],
    )

    exit_code = validate_output.main(["--input", str(jsonl_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "OK: validated 3 records across regions JP,US\n"
    assert captured.err == ""


def test_main_unsorted_output_returns_nonzero_with_error(tmp_path, capsys):
    jsonl_path = tmp_path / "invalid_order.jsonl"
    _write_jsonl(
        jsonl_path,
        [
            _record("US", 1, "us_video_001"),
            _record("JP", 1, "jp_video_001"),
        ],
    )

    exit_code = validate_output.main(["--input", str(jsonl_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert (
        captured.err
        == "ERROR: records: expected deterministic ordering by region,rank,video_id\n"
    )
