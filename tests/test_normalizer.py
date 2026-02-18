import hashlib

from phase1_youtube.normalizer import normalize_trending_records, serialize_normalized_records
from phase1_youtube.schema import validate_record


def test_normalize_trending_records_deterministic_output_is_byte_identical():
    records_by_region = {
        "US": [
            {
                "region": "US",
                "rank": 2,
                "video_id": "shared_video",
                "title": "Shared in US",
                "description": "US description",
                "duration": "PT30S",
                "raw_video": {"id": "shared_video"},
            },
            {
                "region": "US",
                "rank": 1,
                "video_id": "us_long",
                "title": "Not a short",
                "description": "should be dropped",
                "duration": "PT181S",
                "raw_video": {"id": "us_long"},
            },
        ],
        "JP": [
            {
                "region": "JP",
                "rank": 1,
                "video_id": "shared_video",
                "title": "Shared in JP",
                "description": "JP description",
                "duration": "PT45S",
                "raw_video": {"id": "shared_video"},
            },
            {
                "region": "JP",
                "rank": 3,
                "video_id": "jp_short",
                "title": "JP short",
                "description": "kept",
                "duration": "PT59S",
                "raw_video": {"id": "jp_short"},
            },
        ],
    }

    normalized_first = normalize_trending_records(records_by_region)
    normalized_second = normalize_trending_records(records_by_region)

    serialized_first = serialize_normalized_records(normalized_first)
    serialized_second = serialize_normalized_records(normalized_second)

    assert serialized_first == serialized_second
    assert hashlib.sha256(serialized_first.encode("utf-8")).hexdigest() == hashlib.sha256(
        serialized_second.encode("utf-8")
    ).hexdigest()

    assert [(row["region"], row["rank"], row["video_id"]) for row in normalized_first] == [
        ("JP", 1, "shared_video"),
        ("JP", 3, "jp_short"),
        ("US", 2, "shared_video"),
    ]

    for record in normalized_first:
        validate_record(record)


def test_normalize_trending_records_preserves_per_region_duplicates_deterministically():
    records_by_region = {
        "US": [
            {
                "region": "US",
                "rank": 2,
                "video_id": "dupe",
                "title": "alpha",
                "description": "same key duplicate",
                "duration": "PT20S",
                "raw_video": {"id": "dupe", "variant": "a"},
            },
            {
                "region": "US",
                "rank": 2,
                "video_id": "dupe",
                "title": "beta",
                "description": "same key duplicate",
                "duration": "PT20S",
                "raw_video": {"id": "dupe", "variant": "b"},
            },
            {
                "region": "US",
                "rank": 2,
                "video_id": "not_short",
                "title": "long in US",
                "description": "drops by duration",
                "duration": "PT181S",
                "raw_video": {"id": "not_short"},
            },
        ],
        "JP": [
            {
                "region": "JP",
                "rank": 1,
                "video_id": "dupe",
                "title": "cross-region",
                "description": "independent region copy",
                "duration": "PT20S",
                "raw_video": {"id": "dupe", "region": "JP"},
            }
        ]
    }

    normalized = normalize_trending_records(records_by_region)

    assert len(normalized) == 3
    assert [(row["region"], row["rank"], row["video_id"]) for row in normalized] == [
        ("JP", 1, "dupe"),
        ("US", 2, "dupe"),
        ("US", 2, "dupe"),
    ]
    assert [row["title"] for row in normalized] == ["cross-region", "alpha", "beta"]

    for record in normalized:
        validate_record(record)

    serialized = serialize_normalized_records(normalized)
    assert serialized.count("\n") == 2
