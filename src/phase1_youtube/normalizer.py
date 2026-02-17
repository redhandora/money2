import json

from phase1_youtube.schema import SCHEMA_VERSION, validate_record
from phase1_youtube.shorts_classifier import classify_shorts_duration


_SORT_KEY_FIELDS = ("region", "rank", "video_id")


def _to_non_empty_string(value, field_name):
    if not isinstance(value, str):
        raise ValueError("{0}: expected non-empty string".format(field_name))
    if value == "":
        raise ValueError("{0}: expected non-empty string".format(field_name))
    return value


def _to_string(value):
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return str(value)


def _to_positive_int(value, field_name):
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("{0}: expected integer".format(field_name))
    if value < 1:
        raise ValueError("{0}: expected >= 1".format(field_name))
    return value


def _stable_record_tiebreaker(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":"))


def _record_sort_key(record):
    return (
        record["region"],
        record["rank"],
        record["video_id"],
        _stable_record_tiebreaker(record),
    )


def normalize_trending_records(records_by_region):
    normalized_records = []

    for region, records in records_by_region.items():
        normalized_region = _to_non_empty_string(region, "region")
        if not isinstance(records, list):
            raise ValueError("records_by_region[{0}]: expected list".format(region))

        for record in records:
            if not isinstance(record, dict):
                raise ValueError("records_by_region[{0}]: expected dict record".format(region))

            duration = record.get("duration")
            classification = classify_shorts_duration(duration)
            if not classification["is_short"]:
                continue

            normalized_record = {
                "schema_version": SCHEMA_VERSION,
                "region": normalized_region,
                "rank": _to_positive_int(record.get("rank"), "rank"),
                "video_id": _to_non_empty_string(record.get("video_id"), "video_id"),
                "title": _to_string(record.get("title")),
                "description": _to_string(record.get("description")),
                "transcript_status": "official_unavailable",
                "transcript_provenance": "",
                "transcript_text": "",
            }
            validate_record(normalized_record)
            normalized_records.append(normalized_record)

    normalized_records.sort(key=_record_sort_key)
    return normalized_records


def serialize_normalized_records(records):
    lines = [json.dumps(record, sort_keys=True, separators=(",", ":")) for record in records]
    return "\n".join(lines)


def normalized_sort_fields():
    return _SORT_KEY_FIELDS
