import pytest
from pathlib import Path

from phase1_youtube.fixture_harness import assert_videos_list_shape, load_json_fixture
from phase1_youtube.schema import validate_record


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.mark.parametrize(
    "fixture_name,expected_first_video_id",
    [
        ("youtube_videos_list_jp.json", "jp_video_001"),
        ("youtube_videos_list_us.json", "us_video_001"),
    ],
)
def test_videos_list_fixtures_match_expected_shape(
    fixture_name, expected_first_video_id
) -> None:
    payload = load_json_fixture(FIXTURES_DIR, fixture_name)

    assert_videos_list_shape(payload)
    assert payload["items"][0]["id"] == expected_first_video_id


@pytest.mark.parametrize(
    "fixture_name",
    [
        "transcript_official_available.json",
        "transcript_official_unavailable.json",
        "transcript_asr_success.json",
        "transcript_asr_failure.json",
    ],
)
def test_transcript_fixtures_validate_against_canonical_schema(fixture_name) -> None:
    record = load_json_fixture(FIXTURES_DIR, fixture_name)
    validate_record(record)


def test_malformed_fixture_is_rejected_by_schema_validator() -> None:
    malformed_record = load_json_fixture(FIXTURES_DIR, "transcript_malformed.json")

    with pytest.raises(ValueError, match=r"^transcript_status:"):
        validate_record(malformed_record)


@pytest.mark.xfail(strict=True, reason="Malformed fixture should fail schema validation")
def test_malformed_fixture_failure_scenario_for_evidence_capture() -> None:
    malformed_record = load_json_fixture(FIXTURES_DIR, "transcript_malformed.json")
    validate_record(malformed_record)
