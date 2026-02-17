import pytest

from phase1_youtube.youtube_client import YouTubeClientError, YouTubeVideosClient


class _TransientHttpError(Exception):
    def __init__(self, status_code, message):
        super(_TransientHttpError, self).__init__(message)
        self.status_code = status_code


class _FakeHttp(object):
    def __init__(self):
        self.timeout = None


class _FakeRequest(object):
    def __init__(self, outcomes):
        self._outcomes = outcomes
        self.http = _FakeHttp()
        self.execute_calls = 0

    def execute(self, num_retries=0):
        self.execute_calls += 1
        outcome = self._outcomes[self.execute_calls - 1]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class _FakeVideosResource(object):
    def __init__(self, request):
        self._request = request
        self.calls = []

    def list(self, **kwargs):
        self.calls.append(kwargs)
        return self._request


class _FakeService(object):
    def __init__(self, videos_resource):
        self._videos_resource = videos_resource

    def videos(self):
        return self._videos_resource


def test_videos_list_retries_once_then_returns_success() -> None:
    request = _FakeRequest(
        [
            _TransientHttpError(503, "transient backend error"),
            {"items": [{"id": "abc123"}]},
        ]
    )
    videos_resource = _FakeVideosResource(request)
    service = _FakeService(videos_resource)
    sleep_calls = []

    client = YouTubeVideosClient(
        service=service,
        timeout_seconds=45,
        max_attempts=3,
        base_backoff_seconds=1.0,
        max_backoff_seconds=4.0,
        random_func=lambda: 0.0,
        sleep_func=sleep_calls.append,
    )

    response = client.videos_list(
        chart="mostPopular",
        regionCode="JP",
        maxResults=50,
        part="snippet,contentDetails,statistics",
    )

    assert response["items"][0]["id"] == "abc123"
    assert request.execute_calls == 2
    assert request.http.timeout == 45
    assert sleep_calls == [1.0]
    assert len(videos_resource.calls) == 2


def test_videos_list_raises_capped_retry_error_after_max_attempts() -> None:
    request = _FakeRequest(
        [
            _TransientHttpError(503, "backend unavailable #1"),
            _TransientHttpError(503, "backend unavailable #2"),
            _TransientHttpError(503, "backend unavailable #3"),
        ]
    )
    service = _FakeService(_FakeVideosResource(request))
    sleep_calls = []

    client = YouTubeVideosClient(
        service=service,
        timeout_seconds=30,
        max_attempts=3,
        base_backoff_seconds=1.0,
        max_backoff_seconds=4.0,
        random_func=lambda: 0.0,
        sleep_func=sleep_calls.append,
    )

    with pytest.raises(
        YouTubeClientError,
        match=r"^videos.list failed after 3/3 attempts \(last_status=503\)$",
    ) as error_info:
        client.videos_list(
            chart="mostPopular",
            regionCode="US",
            maxResults=50,
            part="snippet,contentDetails,statistics",
        )

    error = error_info.value
    assert error.status_code == 503
    assert error.attempts == 3
    assert error.max_attempts == 3
    assert error.last_error_message == "backend unavailable #3"
    assert request.execute_calls == 3
    assert sleep_calls == [1.0, 2.0]
