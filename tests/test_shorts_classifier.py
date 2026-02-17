import pytest

from phase1_youtube.shorts_classifier import SHORTS_RULE_VERSION, classify_shorts_duration


@pytest.mark.parametrize(
    "duration, expected_is_short",
    [
        ("PT59S", True),
        ("PT60S", True),
        ("PT61S", False),
    ],
)
def test_classify_shorts_duration_boundary_seconds(duration, expected_is_short):
    result = classify_shorts_duration(duration)

    assert result == {
        "is_short": expected_is_short,
        "shorts_rule_version": SHORTS_RULE_VERSION,
    }


def test_classify_shorts_duration_rejects_invalid_duration_deterministically():
    with pytest.raises(ValueError, match=r"^duration must be a valid ISO8601 duration$"):
        classify_shorts_duration("invalid")
