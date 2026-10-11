"""Fixed invented data: no wall clock, randomness, historical prices or accounts."""

def scenario():
    def event(kind, seq, **fields):
        return {"kind": kind, "seq": seq, "at": f"2030-01-01T00:00:{seq:02d}Z", **fields}

    def tick(seq, price):
        return event("tick", seq, observed_at=f"2030-01-01T00:00:{seq:02d}Z",
                     bid="90.00", ask="110.00", price=price)

    return {"version": 1, "synthetic": True, "symbol": "SIM_ORB", "max_age_ms": 3000,
            "events": [tick(1, "100.00"), tick(2, "101.25"), event("pause", 3),
                       tick(4, "109.00"), event("resume", 5), tick(6, "99.50"),
                       tick(7, "NaN"), tick(8, "99.50")]}
