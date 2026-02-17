import json
from pathlib import Path


def load_json_fixture(fixtures_dir, file_name):
    fixture_path = Path(fixtures_dir) / file_name
    with fixture_path.open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def assert_videos_list_shape(payload):
    if not isinstance(payload, dict):
        raise AssertionError("payload must be an object")

    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise AssertionError("payload.items must be a non-empty array")

    first_item = items[0]
    if not isinstance(first_item, dict):
        raise AssertionError("payload.items[0] must be an object")

    if not isinstance(first_item.get("id"), str) or not first_item["id"]:
        raise AssertionError("payload.items[0].id must be a non-empty string")

    snippet = first_item.get("snippet")
    if not isinstance(snippet, dict):
        raise AssertionError("payload.items[0].snippet must be an object")

    if not isinstance(snippet.get("title"), str):
        raise AssertionError("payload.items[0].snippet.title must be a string")

    if not isinstance(snippet.get("description"), str):
        raise AssertionError("payload.items[0].snippet.description must be a string")

    content_details = first_item.get("contentDetails")
    if not isinstance(content_details, dict):
        raise AssertionError("payload.items[0].contentDetails must be an object")

    duration = content_details.get("duration")
    if not isinstance(duration, str) or not duration.startswith("PT"):
        raise AssertionError("payload.items[0].contentDetails.duration must be an ISO8601 string")
