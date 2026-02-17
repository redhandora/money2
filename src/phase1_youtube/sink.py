import json

from phase1_youtube.schema import SCHEMA_VERSION, validate_record


MANIFEST_VERSION = "1.0"


def _validate_non_negative_int(value, field_name):
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("{0}: expected integer".format(field_name))
    if value < 0:
        raise ValueError("{0}: expected >= 0".format(field_name))
    return value


def _validate_records(records):
    if not isinstance(records, list):
        raise ValueError("records: expected list")

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError("record[{0}]: expected dict".format(index))

        try:
            validate_record(record)
        except ValueError as exc:
            raise ValueError("record[{0}]: {1}".format(index, exc))


def serialize_records_jsonl(records):
    _validate_records(records)
    lines = [json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False) for record in records]
    return "\n".join(lines)


def write_jsonl(records, output_path):
    jsonl_content = serialize_records_jsonl(records)
    with open(output_path, "w", encoding="utf-8") as handle:
        if jsonl_content:
            handle.write(jsonl_content)
            handle.write("\n")


def _build_region_counts(records):
    region_counts = {}
    for record in records:
        region = record["region"]
        region_counts[region] = region_counts.get(region, 0) + 1

    ordered = {}
    for region in sorted(region_counts.keys()):
        ordered[region] = region_counts[region]
    return ordered


def _normalize_quota(quota):
    if quota is None:
        return {
            "used": 0,
            "limit": 0,
            "remaining": 0,
        }

    if not isinstance(quota, dict):
        raise ValueError("quota: expected dict")

    required_keys = ("used", "limit", "remaining")
    normalized = {}
    for key in required_keys:
        if key not in quota:
            raise ValueError("quota.{0}: missing required field".format(key))
        normalized[key] = _validate_non_negative_int(quota[key], "quota.{0}".format(key))

    for key in quota:
        if key not in required_keys:
            raise ValueError("quota.{0}: unexpected field".format(key))

    return normalized


def _normalize_errors(errors):
    if errors is None:
        return []

    if not isinstance(errors, list):
        raise ValueError("errors: expected list")

    normalized = []
    for index, item in enumerate(errors):
        if not isinstance(item, dict):
            raise ValueError("errors[{0}]: expected dict".format(index))
        normalized.append(dict(item))
    return normalized


def build_run_manifest(records, quota=None, errors=None, run_id=""):
    _validate_records(records)
    normalized_quota = _normalize_quota(quota)
    normalized_errors = _normalize_errors(errors)

    if not isinstance(run_id, str):
        raise ValueError("run_id: expected string")

    return {
        "manifest_version": MANIFEST_VERSION,
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "output_format": "jsonl",
        "counts": {
            "total_records": len(records),
            "regions": _build_region_counts(records),
        },
        "quota": normalized_quota,
        "error_count": len(normalized_errors),
        "errors": normalized_errors,
    }


def write_manifest(manifest, output_path):
    if not isinstance(manifest, dict):
        raise ValueError("manifest: expected dict")

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
        handle.write("\n")


def write_jsonl_and_manifest(records, jsonl_path, manifest_path, quota=None, errors=None, run_id=""):
    write_jsonl(records=records, output_path=jsonl_path)
    manifest = build_run_manifest(records=records, quota=quota, errors=errors, run_id=run_id)
    write_manifest(manifest=manifest, output_path=manifest_path)
    return manifest
