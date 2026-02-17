from pathlib import Path

from phase1_youtube.fixture_harness import load_json_fixture
from phase1_youtube.trending_fetcher import fetch_most_popular_by_regions


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class _FakeVideosClient(object):
    def __init__(self, payload_by_region=None, error_by_region=None):
        self._payload_by_region = payload_by_region or {}
        self._error_by_region = error_by_region or {}
        self.calls = []

    def videos_list(self, **kwargs):
        self.calls.append(kwargs)
        region = kwargs.get("regionCode")

        if region in self._error_by_region:
            raise self._error_by_region[region]

        return self._payload_by_region[region]


def test_fetch_most_popular_by_regions_returns_ranked_records_per_region() -> None:
    jp_payload = load_json_fixture(FIXTURES_DIR, "youtube_videos_list_jp.json")
    us_payload = load_json_fixture(FIXTURES_DIR, "youtube_videos_list_us.json")
    videos_client = _FakeVideosClient(
        payload_by_region={"JP": jp_payload, "US": us_payload}
    )

    result = fetch_most_popular_by_regions(
        videos_client=videos_client,
        regions=["JP", "US"],
        top_n=2,
    )

    assert result["errors_by_region"] == {}

    jp_records = result["records_by_region"]["JP"]
    assert [record["rank"] for record in jp_records] == [1, 2]
    assert [record["video_id"] for record in jp_records] == ["jp_video_001", "jp_video_002"]
    assert all(record["region"] == "JP" for record in jp_records)
    assert jp_records[0]["raw_video"]["snippet"]["title"] == "JP Trending Short 1"
    assert jp_records[0]["duration"] == "PT42S"

    us_records = result["records_by_region"]["US"]
    assert [record["rank"] for record in us_records] == [1, 2]
    assert [record["video_id"] for record in us_records] == ["us_video_001", "us_video_002"]
    assert all(record["region"] == "US" for record in us_records)
    assert us_records[1]["raw_video"]["snippet"]["description"] == "Second deterministic US fixture video"

    assert videos_client.calls == [
        {
            "chart": "mostPopular",
            "regionCode": "JP",
            "maxResults": 2,
            "part": "snippet,contentDetails",
        },
        {
            "chart": "mostPopular",
            "regionCode": "US",
            "maxResults": 2,
            "part": "snippet,contentDetails",
        },
    ]


def test_fetch_most_popular_by_regions_isolates_jp_failure_from_us_success() -> None:
    us_payload = load_json_fixture(FIXTURES_DIR, "youtube_videos_list_us.json")
    videos_client = _FakeVideosClient(
        payload_by_region={"US": us_payload},
        error_by_region={"JP": RuntimeError("JP timeout")},
    )

    result = fetch_most_popular_by_regions(
        videos_client=videos_client,
        regions=["JP", "US"],
        top_n=2,
    )

    assert result["records_by_region"]["JP"] == []
    assert result["errors_by_region"] == {"JP": "JP timeout"}

    us_records = result["records_by_region"]["US"]
    assert [record["rank"] for record in us_records] == [1, 2]
    assert [record["video_id"] for record in us_records] == ["us_video_001", "us_video_002"]
