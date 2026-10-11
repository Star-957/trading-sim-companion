"""Strict, bounded versions of the original stdlib timestamp/number seam."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import re


class InputError(ValueError):
    """A fixed diagnostic that never includes untrusted input."""


TIME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})")
PRICE = re.compile(r"(?:0|[1-9][0-9]{0,9})(?:\.[0-9]{1,6})?")


def timestamp(value):
    """Require an explicit offset, reject ambiguous local time and normalize UTC."""
    if type(value) is not str or len(value) > 32 or TIME.fullmatch(value) is None:
        raise InputError("timestamp_format")
    try:
        if not value.endswith("Z") and int(value[-2:]) >= 60:
            raise ValueError
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if abs(result.utcoffset()) > timedelta(hours=14):
            raise ValueError
        return result.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise InputError("timestamp_range") from None


def number(value):
    """Accept decimal strings in (0, 1e9], with at most six fraction digits."""
    if type(value) is not str or len(value) > 17 or PRICE.fullmatch(value) is None:
        raise InputError("price_format")
    result = Decimal(value)
    if not 0 < result <= Decimal("1000000000"):
        raise InputError("price_range")
    return result


def integer(value, minimum, maximum, reason):
    if type(value) is not int or not minimum <= value <= maximum:
        raise InputError(reason)
    return value
