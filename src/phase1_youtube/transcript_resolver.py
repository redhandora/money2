class OfficialTranscriptUnavailable(RuntimeError):
    pass


def _empty_resolution(status, provenance, error_code, error_detail):
    return {
        "transcript_status": status,
        "transcript_provenance": provenance,
        "transcript_text": "",
        "transcript_error_code": error_code,
        "transcript_error_detail": error_detail,
    }


def _normalize_transcript_text(value):
    if not isinstance(value, str):
        return None

    normalized = value.strip()
    if not normalized:
        return None

    return normalized


def _error_detail_from_exception(exc):
    message = str(exc)
    if message:
        return message
    return exc.__class__.__name__


def resolve_transcript(
    video_record,
    official_transcript_fetcher=None,
    asr_transcriber=None,
    asr_quota_available=True,
):
    if not isinstance(video_record, dict):
        raise ValueError("video_record: expected dict")

    official_resolution = _empty_resolution(
        status="official_unavailable",
        provenance="none",
        error_code="official_unavailable",
        error_detail="official transcript unavailable",
    )

    if official_transcript_fetcher is not None:
        try:
            official_text = official_transcript_fetcher(video_record)
            normalized_official_text = _normalize_transcript_text(official_text)
            if normalized_official_text is not None:
                return {
                    "transcript_status": "official_ok",
                    "transcript_provenance": "official",
                    "transcript_text": normalized_official_text,
                    "transcript_error_code": "",
                    "transcript_error_detail": "",
                }
        except OfficialTranscriptUnavailable as exc:
            official_resolution["transcript_error_code"] = "official_unavailable"
            official_resolution["transcript_error_detail"] = _error_detail_from_exception(exc)
        except Exception as exc:
            official_resolution["transcript_error_code"] = "official_error"
            official_resolution["transcript_error_detail"] = _error_detail_from_exception(exc)

    if asr_transcriber is None:
        return official_resolution

    if not asr_quota_available:
        return _empty_resolution(
            status="skipped_quota",
            provenance="asr",
            error_code="asr_quota_unavailable",
            error_detail="asr quota unavailable",
        )

    try:
        asr_text = asr_transcriber(video_record)
        normalized_asr_text = _normalize_transcript_text(asr_text)
        if normalized_asr_text is None:
            return _empty_resolution(
                status="asr_failed",
                provenance="asr",
                error_code="asr_empty_transcript",
                error_detail="asr transcript empty",
            )

        return {
            "transcript_status": "asr_ok",
            "transcript_provenance": "asr",
            "transcript_text": normalized_asr_text,
            "transcript_error_code": "",
            "transcript_error_detail": "",
        }
    except Exception as exc:
        return _empty_resolution(
            status="asr_failed",
            provenance="asr",
            error_code="asr_error",
            error_detail=_error_detail_from_exception(exc),
        )


def resolve_transcripts(
    records,
    official_transcript_fetcher=None,
    asr_transcriber=None,
    asr_quota_available=True,
):
    if not isinstance(records, list):
        raise ValueError("records: expected list")

    resolved_records = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("records: expected dict items")

        resolved_record = dict(record)
        resolved_record.update(
            resolve_transcript(
                video_record=record,
                official_transcript_fetcher=official_transcript_fetcher,
                asr_transcriber=asr_transcriber,
                asr_quota_available=asr_quota_available,
            )
        )
        resolved_records.append(resolved_record)

    return resolved_records
