import re


SHORTS_RULE_VERSION = "v2_duration_lte_180_seconds"
SHORTS_MAX_SECONDS = 180

_ISO8601_DURATION_PATTERN = re.compile(
    r"^P"
    r"(?:(?P<days>\d+)D)?"
    r"(?:T"
    r"(?:(?P<hours>\d+)H)?"
    r"(?:(?P<minutes>\d+)M)?"
    r"(?:(?P<seconds>\d+)S)?"
    r")?$"
)


def parse_iso8601_duration_seconds(duration):
    if not isinstance(duration, str):
        raise ValueError("duration must be an ISO8601 string")

    match = _ISO8601_DURATION_PATTERN.match(duration)
    if match is None:
        raise ValueError("duration must be a valid ISO8601 duration")

    parts = match.groupdict()
    if all(parts[name] is None for name in ("days", "hours", "minutes", "seconds")):
        raise ValueError("duration must include at least one time component")

    days = int(parts["days"]) if parts["days"] is not None else 0
    hours = int(parts["hours"]) if parts["hours"] is not None else 0
    minutes = int(parts["minutes"]) if parts["minutes"] is not None else 0
    seconds = int(parts["seconds"]) if parts["seconds"] is not None else 0

    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def classify_shorts_duration(duration):
    duration_seconds = parse_iso8601_duration_seconds(duration)
    return {
        "is_short": duration_seconds <= SHORTS_MAX_SECONDS,
        "shorts_rule_version": SHORTS_RULE_VERSION,
    }
