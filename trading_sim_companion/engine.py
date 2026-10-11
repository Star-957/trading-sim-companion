"""Pure, deterministic replay of a single fictitious sensor-like price stream."""

from datetime import timedelta
import re

from .validation import InputError, integer, number, timestamp

MAX_EVENTS = 1000
SYMBOL = re.compile(r"SIM_[A-Z0-9]{1,16}")
COMMON = {"kind", "seq", "at"}
TICK = COMMON | {"observed_at", "bid", "ask", "price"}


def _event(event, previous_seq, previous_at, max_age):
    if type(event) is not dict:
        raise InputError("event_object")
    kind = event.get("kind")
    if type(kind) is not str or kind not in ("tick", "pause", "resume"):
        raise InputError("event_kind")
    if set(event) != (TICK if kind == "tick" else COMMON):
        raise InputError("event_fields")
    seq = integer(event["seq"], 1, 1000000000, "sequence_range")
    at = timestamp(event["at"])
    if seq <= previous_seq:
        raise InputError("sequence_order")
    if previous_at is not None and at < previous_at:
        raise InputError("time_order")
    price = None
    if kind == "tick":
        observed = timestamp(event["observed_at"])
        if not timedelta(0) <= at - observed <= max_age:
            raise InputError("observation_age")
        bid, ask, price = (number(event[key]) for key in ("bid", "ask", "price"))
        if not bid <= price <= ask:
            raise InputError("price_order")
    return kind, seq, at, price


def replay(document):
    """Return detached JSON-compatible output; rejected events never mutate state.

    Accepted events advance sequence and time. Valid ticks while paused are
    ignored but also advance sequence/time. Equal timestamps are permitted;
    sequences must strictly increase. A resume returns to idle until a new tick.
    """
    if type(document) is not dict or set(document) != {
        "version", "synthetic", "symbol", "max_age_ms", "events"
    }:
        raise InputError("document_fields")
    if type(document["version"]) is not int or document["version"] != 1:
        raise InputError("document_version")
    if document["synthetic"] is not True:
        raise InputError("synthetic_required")
    symbol = document["symbol"]
    if type(symbol) is not str or len(symbol) > 20 or SYMBOL.fullmatch(symbol) is None:
        raise InputError("synthetic_symbol")
    max_age = timedelta(milliseconds=integer(document["max_age_ms"], 0, 60000, "age_limit"))
    events = document["events"]
    if type(events) is not list or len(events) > MAX_EVENTS:
        raise InputError("event_limit")

    previous_seq, previous_at, last_price = 0, None, None
    paused, status, count = False, "idle", 0
    trace = []
    for index, event in enumerate(events):
        try:
            kind, seq, at, price = _event(event, previous_seq, previous_at, max_age)
        except InputError as error:
            outcome, reason = "rejected", str(error)
        else:
            previous_seq, previous_at = seq, at
            outcome, reason = "accepted", kind
            if kind == "pause":
                paused, status = True, "paused"
            elif kind == "resume":
                paused, status = False, "idle"
            elif paused:
                outcome, reason = "ignored", "paused"
            else:
                status = ("idle" if last_price is None else "rising" if price > last_price
                          else "falling" if price < last_price else "steady")
                last_price, count = price, count + 1
        trace.append({"index": index, "outcome": outcome, "reason": reason,
                      "status": status, "tick_count": count,
                      "last_price": str(last_price) if last_price is not None else None})
    return {"version": 1, "synthetic": True, "symbol": symbol,
            "status": status, "paused": paused, "tick_count": count,
            "last_price": str(last_price) if last_price is not None else None,
            "last_seq": previous_seq,
            "last_at": previous_at.isoformat() if previous_at is not None else None,
            "trace": trace}
