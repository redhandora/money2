import argparse
import json
import sys

from phase1_youtube.schema import validate_record


def _load_records(input_path):
    records = []
    with open(input_path, "r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            payload = line.strip()
            if not payload:
                continue
            try:
                record = json.loads(payload)
            except ValueError as exc:
                raise ValueError(
                    "line {0}: invalid json ({1})".format(line_number, exc)
                )
            records.append(record)
    return records


def _is_sorted(records):
    previous_key = None
    for record in records:
        current_key = (record["region"], record["rank"], record["video_id"])
        if previous_key is not None and current_key < previous_key:
            return False
        previous_key = current_key
    return True


def validate_jsonl_output(input_path):
    records = _load_records(input_path)
    if not records:
        raise ValueError("input: no records found")

    for index, record in enumerate(records):
        try:
            validate_record(record)
        except ValueError as exc:
            raise ValueError("record[{0}]: {1}".format(index, exc))

    if not _is_sorted(records):
        raise ValueError("records: expected deterministic ordering by region,rank,video_id")

    return {
        "record_count": len(records),
        "regions": sorted({record["region"] for record in records}),
    }


def _build_parser():
    parser = argparse.ArgumentParser(
        description="Validate Phase 1 YouTube JSONL output"
    )
    parser.add_argument("--input", required=True, help="Input JSONL path")
    return parser


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        summary = validate_jsonl_output(args.input)
    except (OSError, ValueError) as exc:
        sys.stderr.write("ERROR: {0}\n".format(exc))
        return 1

    sys.stdout.write(
        "OK: validated {0} records across regions {1}\n".format(
            summary["record_count"],
            ",".join(summary["regions"]),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
