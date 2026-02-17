import pytest

from phase1_youtube.config import ConfigError, load_config


def test_load_config_uses_defaults_and_optional_none() -> None:
    config = load_config({"YOUTUBE_API_KEY": "test-key"})

    assert config["youtube_api_key"] == "test-key"
    assert config["youtube_quota_daily_limit"] == 10000
    assert config["youtube_quota_budget"] == 8000
    assert config["youtube_timeout_seconds"] == 30
    assert config["asr_timeout_seconds"] == 120
    assert config["youtube_oauth_client_id"] is None
    assert config["youtube_oauth_client_secret"] is None
    assert config["youtube_oauth_refresh_token"] is None
    assert config["asr_provider"] is None
    assert config["asr_model"] is None


def test_load_config_parses_numeric_overrides() -> None:
    config = load_config(
        {
            "YOUTUBE_API_KEY": "key-123",
            "YOUTUBE_QUOTA_DAILY_LIMIT": "12000",
            "YOUTUBE_QUOTA_BUDGET": "9000",
            "YOUTUBE_TIMEOUT_SECONDS": "45",
            "ASR_TIMEOUT_SECONDS": "240",
            "YOUTUBE_OAUTH_CLIENT_ID": "client-id",
            "YOUTUBE_OAUTH_CLIENT_SECRET": "client-secret",
            "YOUTUBE_OAUTH_REFRESH_TOKEN": "refresh-token",
            "ASR_PROVIDER": "whisper",
            "ASR_MODEL": "small",
        }
    )

    assert config["youtube_quota_daily_limit"] == 12000
    assert config["youtube_quota_budget"] == 9000
    assert config["youtube_timeout_seconds"] == 45
    assert config["asr_timeout_seconds"] == 240
    assert config["youtube_oauth_client_id"] == "client-id"
    assert config["youtube_oauth_client_secret"] == "client-secret"
    assert config["youtube_oauth_refresh_token"] == "refresh-token"
    assert config["asr_provider"] == "whisper"
    assert config["asr_model"] == "small"


def test_load_config_rejects_invalid_numeric_env_value() -> None:
    with pytest.raises(
        ConfigError,
        match=r"^YOUTUBE_TIMEOUT_SECONDS: expected integer, got 'not-a-number'$",
    ):
        load_config(
            {
                "YOUTUBE_API_KEY": "test-key",
                "YOUTUBE_TIMEOUT_SECONDS": "not-a-number",
            }
        )


def test_load_config_rejects_quota_budget_above_daily_limit() -> None:
    with pytest.raises(
        ConfigError,
        match=r"^YOUTUBE_QUOTA_BUDGET: must be <= YOUTUBE_QUOTA_DAILY_LIMIT$",
    ):
        load_config(
            {
                "YOUTUBE_API_KEY": "test-key",
                "YOUTUBE_QUOTA_DAILY_LIMIT": "100",
                "YOUTUBE_QUOTA_BUDGET": "101",
            }
        )
