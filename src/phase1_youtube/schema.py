from typing import Any, Dict


SCHEMA_VERSION = "1.0"

TRANSCRIPT_STATUSES = (
    "official_ok",
    "official_unavailable",
    "asr_ok",
    "asr_failed",
    "skipped_quota",
)

REQUIRED_FIELDS = (
    "schema_version",
    "region",
    "rank",
    "video_id",
    "title",
    "description",
    "transcript_status",
    "transcript_provenance",
    "transcript_text",
)

CANONICAL_RECORD_SCHEMA = {
    "type": "object",
    "required": list(REQUIRED_FIELDS),
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "region": {"type": "string"},
        "rank": {"type": "integer", "minimum": 1},
        "video_id": {"type": "string", "minLength": 1},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "transcript_status": {"enum": list(TRANSCRIPT_STATUSES)},
        "transcript_provenance": {"type": "string"},
        "transcript_text": {"type": "string"},
    },
    "additionalProperties": False,
}


def validate_record(record: Dict[str, Any]) -> None:
    for field in record:
        if field not in REQUIRED_FIELDS:
            raise ValueError("{0}: unexpected field".format(field))

    for field in REQUIRED_FIELDS:
        if field not in record:
            raise ValueError(f"{field}: missing required field")

    if record["schema_version"] != SCHEMA_VERSION:
        raise ValueError("schema_version: unsupported value")

    if not isinstance(record["region"], str):
        raise ValueError("region: expected string")

    if not isinstance(record["rank"], int) or isinstance(record["rank"], bool):
        raise ValueError("rank: expected integer")
    if record["rank"] < 1:
        raise ValueError("rank: must be >= 1")

    if not isinstance(record["video_id"], str):
        raise ValueError("video_id: expected string")
    if record["video_id"] == "":
        raise ValueError("video_id: must not be empty")

    if not isinstance(record["title"], str):
        raise ValueError("title: expected string")

    if not isinstance(record["description"], str):
        raise ValueError("description: expected string")

    if record["transcript_status"] not in TRANSCRIPT_STATUSES:
        raise ValueError("transcript_status: invalid enum value")

    if not isinstance(record["transcript_provenance"], str):
        raise ValueError("transcript_provenance: expected string")

    if not isinstance(record["transcript_text"], str):
        raise ValueError("transcript_text: expected string")
