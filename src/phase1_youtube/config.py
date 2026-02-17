import os
from typing import Dict, Mapping, Optional


DEFAULT_YOUTUBE_QUOTA_DAILY_LIMIT = 10000
DEFAULT_YOUTUBE_QUOTA_BUDGET = 8000
DEFAULT_YOUTUBE_TIMEOUT_SECONDS = 30
DEFAULT_ASR_TIMEOUT_SECONDS = 120


class ConfigError(ValueError):
    pass


def _get_optional_text(env: Mapping[str, str], key: str) -> Optional[str]:
    value = env.get(key)
    if value is None:
        return None

    stripped = value.strip()
    if not stripped:
        return None

    return stripped


def _get_required_text(env: Mapping[str, str], key: str) -> str:
    value = _get_optional_text(env, key)
    if value is None:
        raise ConfigError("{0}: missing required environment variable".format(key))
    return value


def _parse_int_env(
    env: Mapping[str, str],
    key: str,
    default: int,
    minimum: int,
) -> int:
    value = env.get(key)
    if value is None:
        return default

    stripped = value.strip()
    if not stripped:
        raise ConfigError("{0}: expected integer, got ''".format(key))

    try:
        parsed = int(stripped)
    except ValueError:
        raise ConfigError(
            "{0}: expected integer, got '{1}'".format(key, stripped)
        )

    if parsed < minimum:
        raise ConfigError("{0}: must be >= {1}".format(key, minimum))

    return parsed


def load_config(env: Optional[Mapping[str, str]] = None) -> Dict[str, Optional[object]]:
    active_env = env or os.environ

    youtube_api_key = _get_required_text(active_env, "YOUTUBE_API_KEY")

    youtube_quota_daily_limit = _parse_int_env(
        active_env,
        "YOUTUBE_QUOTA_DAILY_LIMIT",
        DEFAULT_YOUTUBE_QUOTA_DAILY_LIMIT,
        minimum=1,
    )
    youtube_quota_budget = _parse_int_env(
        active_env,
        "YOUTUBE_QUOTA_BUDGET",
        DEFAULT_YOUTUBE_QUOTA_BUDGET,
        minimum=1,
    )
    youtube_timeout_seconds = _parse_int_env(
        active_env,
        "YOUTUBE_TIMEOUT_SECONDS",
        DEFAULT_YOUTUBE_TIMEOUT_SECONDS,
        minimum=1,
    )
    asr_timeout_seconds = _parse_int_env(
        active_env,
        "ASR_TIMEOUT_SECONDS",
        DEFAULT_ASR_TIMEOUT_SECONDS,
        minimum=1,
    )

    if youtube_quota_budget > youtube_quota_daily_limit:
        raise ConfigError(
            "YOUTUBE_QUOTA_BUDGET: must be <= YOUTUBE_QUOTA_DAILY_LIMIT"
        )

    return {
        "youtube_api_key": youtube_api_key,
        "youtube_quota_daily_limit": youtube_quota_daily_limit,
        "youtube_quota_budget": youtube_quota_budget,
        "youtube_timeout_seconds": youtube_timeout_seconds,
        "youtube_oauth_client_id": _get_optional_text(active_env, "YOUTUBE_OAUTH_CLIENT_ID"),
        "youtube_oauth_client_secret": _get_optional_text(active_env, "YOUTUBE_OAUTH_CLIENT_SECRET"),
        "youtube_oauth_refresh_token": _get_optional_text(active_env, "YOUTUBE_OAUTH_REFRESH_TOKEN"),
        "asr_provider": _get_optional_text(active_env, "ASR_PROVIDER"),
        "asr_model": _get_optional_text(active_env, "ASR_MODEL"),
        "asr_timeout_seconds": asr_timeout_seconds,
    }
