from phase1_youtube.transcript_resolver import (
    OfficialTranscriptUnavailable,
    resolve_transcript,
    resolve_transcripts,
)


def test_resolve_transcript_returns_official_ok_when_official_available():
    video_record = {"video_id": "jp_video_001"}

    def official_fetcher(_record):
        return "  Official caption text for jp_video_001  "

    result = resolve_transcript(
        video_record=video_record,
        official_transcript_fetcher=official_fetcher,
        asr_transcriber=None,
    )

    assert result == {
        "transcript_status": "official_ok",
        "transcript_provenance": "official",
        "transcript_text": "Official caption text for jp_video_001",
        "transcript_error_code": "",
        "transcript_error_detail": "",
    }


def test_resolve_transcript_returns_official_unavailable_when_no_asr_fallback():
    video_record = {"video_id": "us_video_001"}

    def official_fetcher(_record):
        raise OfficialTranscriptUnavailable("official transcript missing")

    result = resolve_transcript(
        video_record=video_record,
        official_transcript_fetcher=official_fetcher,
        asr_transcriber=None,
    )

    assert result == {
        "transcript_status": "official_unavailable",
        "transcript_provenance": "none",
        "transcript_text": "",
        "transcript_error_code": "official_unavailable",
        "transcript_error_detail": "official transcript missing",
    }


def test_resolve_transcript_falls_back_to_asr_when_official_unavailable():
    video_record = {"video_id": "jp_video_002"}

    def official_fetcher(_record):
        raise OfficialTranscriptUnavailable("official captions disabled")

    def asr_transcriber(_record):
        return "ASR transcript text for jp_video_002"

    result = resolve_transcript(
        video_record=video_record,
        official_transcript_fetcher=official_fetcher,
        asr_transcriber=asr_transcriber,
    )

    assert result == {
        "transcript_status": "asr_ok",
        "transcript_provenance": "asr",
        "transcript_text": "ASR transcript text for jp_video_002",
        "transcript_error_code": "",
        "transcript_error_detail": "",
    }


def test_resolve_transcript_returns_asr_failed_when_asr_raises():
    video_record = {"video_id": "us_video_002"}

    def official_fetcher(_record):
        raise OfficialTranscriptUnavailable("official captions disabled")

    def asr_transcriber(_record):
        raise RuntimeError("asr provider timeout")

    result = resolve_transcript(
        video_record=video_record,
        official_transcript_fetcher=official_fetcher,
        asr_transcriber=asr_transcriber,
    )

    assert result == {
        "transcript_status": "asr_failed",
        "transcript_provenance": "asr",
        "transcript_text": "",
        "transcript_error_code": "asr_error",
        "transcript_error_detail": "asr provider timeout",
    }


def test_resolve_transcript_returns_skipped_quota_when_asr_quota_unavailable():
    video_record = {"video_id": "jp_video_003"}

    def official_fetcher(_record):
        raise OfficialTranscriptUnavailable("official captions disabled")

    def asr_transcriber(_record):
        return "should not execute"

    result = resolve_transcript(
        video_record=video_record,
        official_transcript_fetcher=official_fetcher,
        asr_transcriber=asr_transcriber,
        asr_quota_available=False,
    )

    assert result == {
        "transcript_status": "skipped_quota",
        "transcript_provenance": "asr",
        "transcript_text": "",
        "transcript_error_code": "asr_quota_unavailable",
        "transcript_error_detail": "asr quota unavailable",
    }


def test_resolve_transcripts_does_not_raise_for_missing_transcripts():
    records = [
        {"video_id": "a", "title": "A"},
        {"video_id": "b", "title": "B"},
    ]

    def official_fetcher(record):
        if record["video_id"] == "a":
            return "official a"
        raise OfficialTranscriptUnavailable("missing official transcript")

    def asr_transcriber(_record):
        return ""

    resolved = resolve_transcripts(
        records=records,
        official_transcript_fetcher=official_fetcher,
        asr_transcriber=asr_transcriber,
        asr_quota_available=True,
    )

    assert [record["transcript_status"] for record in resolved] == [
        "official_ok",
        "asr_failed",
    ]
    assert resolved[1]["transcript_error_code"] == "asr_empty_transcript"
