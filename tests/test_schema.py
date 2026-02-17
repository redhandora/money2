# pyright: reportMissingImports=false
import pytest

from phase1_youtube.schema import SCHEMA_VERSION, validate_record


def test_validate_record_accepts_valid_sample() -> None:
    record = {
        "schema_version": SCHEMA_VERSION,
        "region": "JP",
        "rank": 1,
        "video_id": "abc123",
        "title": "Sample title",
        "description": "Sample description",
        "transcript_status": "official_ok",
        "transcript_provenance": "official",
        "transcript_text": "hello world",
    }

    validate_record(record)


def test_validate_record_rejects_invalid_transcript_status() -> None:
    record = {
        "schema_version": SCHEMA_VERSION,
        "region": "US",
        "rank": 2,
        "video_id": "def456",
        "title": "Another title",
        "description": "Another description",
        "transcript_status": "broken_state",
        "transcript_provenance": "none",
        "transcript_text": "",
    }

    with pytest.raises(ValueError) as exc:
        validate_record(record)

    assert str(exc.value) == "transcript_status: invalid enum value"


def test_validate_record_rejects_unexpected_field() -> None:
    record = {
        "schema_version": SCHEMA_VERSION,
        "region": "US",
        "rank": 3,
        "video_id": "ghi789",
        "title": "Title",
        "description": "Description",
        "transcript_status": "official_unavailable",
        "transcript_provenance": "none",
        "transcript_text": "",
        "unexpected": "free-form",
    }

    with pytest.raises(ValueError) as exc:
        validate_record(record)

    assert str(exc.value) == "unexpected: unexpected field"
