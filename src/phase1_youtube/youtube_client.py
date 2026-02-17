import random
import time


RETRYABLE_STATUS_CODES = frozenset([429, 500, 502, 503, 504])


class YouTubeClientError(RuntimeError):
    def __init__(
        self,
        message,
        status_code=None,
        attempts=None,
        max_attempts=None,
        last_error_message=None,
    ):
        super(YouTubeClientError, self).__init__(message)
        self.status_code = status_code
        self.attempts = attempts
        self.max_attempts = max_attempts
        self.last_error_message = last_error_message


class YouTubeVideosClient(object):
    def __init__(
        self,
        service,
        timeout_seconds,
        max_attempts=3,
        base_backoff_seconds=1.0,
        max_backoff_seconds=8.0,
        random_func=None,
        sleep_func=None,
    ):
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if base_backoff_seconds <= 0:
            raise ValueError("base_backoff_seconds must be > 0")
        if max_backoff_seconds < base_backoff_seconds:
            raise ValueError("max_backoff_seconds must be >= base_backoff_seconds")

        self._service = service
        self._timeout_seconds = timeout_seconds
        self._max_attempts = max_attempts
        self._base_backoff_seconds = float(base_backoff_seconds)
        self._max_backoff_seconds = float(max_backoff_seconds)
        self._random_func = random_func or random.random
        self._sleep_func = sleep_func or time.sleep

    def videos_list(self, **request_params):
        attempt = 0
        last_error = None
        last_status_code = None

        while attempt < self._max_attempts:
            attempt += 1
            request = self._build_request(request_params)
            try:
                return request.execute(num_retries=0)
            except Exception as exc:
                last_error = exc
                last_status_code = _extract_status_code(exc)
                is_retryable = last_status_code in RETRYABLE_STATUS_CODES

                if (not is_retryable) or attempt >= self._max_attempts:
                    break

                self._sleep_func(self._compute_backoff_seconds(attempt))

        message = (
            "videos.list failed after {attempts}/{max_attempts} attempts"
            " (last_status={status_code})"
        ).format(
            attempts=attempt,
            max_attempts=self._max_attempts,
            status_code=last_status_code,
        )
        raise YouTubeClientError(
            message,
            status_code=last_status_code,
            attempts=attempt,
            max_attempts=self._max_attempts,
            last_error_message=str(last_error),
        )

    def _build_request(self, request_params):
        request = self._service.videos().list(**request_params)
        request_http = getattr(request, "http", None)
        if request_http is not None and hasattr(request_http, "timeout"):
            request_http.timeout = self._timeout_seconds
        return request

    def _compute_backoff_seconds(self, attempt):
        exponential = self._base_backoff_seconds * (2 ** (attempt - 1))
        bounded = min(exponential, self._max_backoff_seconds)
        jitter = bounded * self._random_func()
        return bounded + jitter


def _extract_status_code(exc):
    status_code = getattr(exc, "status_code", None)
    if status_code is not None:
        return status_code

    response = getattr(exc, "resp", None)
    if response is None:
        return None

    return getattr(response, "status", None)
