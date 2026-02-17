import copy


DEFAULT_VIDEO_PART = "snippet,contentDetails"
DEFAULT_MAX_RESULTS = 50


def _normalize_top_n(top_n):
    if top_n < 1:
        raise ValueError("top_n must be >= 1")
    return top_n


def _normalize_max_results(top_n, max_results):
    if max_results < 1:
        raise ValueError("max_results must be >= 1")

    return min(max_results, max(top_n, 1))


def fetch_most_popular_by_regions(
    videos_client,
    regions,
    top_n,
    part=DEFAULT_VIDEO_PART,
    max_results=DEFAULT_MAX_RESULTS,
):
    normalized_top_n = _normalize_top_n(top_n)
    normalized_max_results = _normalize_max_results(normalized_top_n, max_results)

    records_by_region = {}
    errors_by_region = {}

    for region in regions:
        records_by_region[region] = []

        try:
            payload = videos_client.videos_list(
                chart="mostPopular",
                regionCode=region,
                maxResults=normalized_max_results,
                part=part,
            )
        except Exception as exc:
            errors_by_region[region] = str(exc)
            continue

        items = payload.get("items", [])
        if not isinstance(items, list):
            errors_by_region[region] = "videos.list payload.items must be a list"
            continue

        for index, item in enumerate(items[:normalized_top_n]):
            snippet = item.get("snippet") if isinstance(item, dict) else {}
            content_details = item.get("contentDetails") if isinstance(item, dict) else {}

            record = {
                "region": region,
                "rank": index + 1,
                "video_id": item.get("id") if isinstance(item, dict) else None,
                "title": snippet.get("title") if isinstance(snippet, dict) else "",
                "description": snippet.get("description")
                if isinstance(snippet, dict)
                else "",
                "duration": content_details.get("duration")
                if isinstance(content_details, dict)
                else None,
                "raw_video": copy.deepcopy(item),
            }
            records_by_region[region].append(record)

    return {
        "records_by_region": records_by_region,
        "errors_by_region": errors_by_region,
    }
