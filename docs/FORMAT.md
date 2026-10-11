# Synthetic event format

The root has exactly five fields: `version: 1`, `synthetic: true`, `symbol`,
`max_age_ms`, and `events`. A symbol must match ASCII `SIM_[A-Z0-9]{1,16}`;
these are fictional labels, not exchange symbols. `max_age_ms` is an integer
from 0 through 60000, and there may be 0 through 1000 events.

Every event has `kind`, `seq`, and `at`. `kind` is `tick`, `pause`, or `resume`.
The sequence is an integer from 1 through 1000000000 and must exceed the last
accepted/ignored event sequence. Timestamps cannot move backwards; equal times
are allowed. A rejected event does not advance either cursor.

Ticks additionally require exactly `observed_at`, `bid`, `ask`, and `price`.
No other fields are permitted. Observation age must be between zero and the
configured limit, inclusively. The synthetic price must be between bid and ask,
inclusively. All prices are strings in `(0, 1000000000]`, with at most six decimal
places. Exponents, signs, whitespace, leading zeroes, non-ASCII numerals, NaN,
infinities, booleans and JSON numbers are rejected as price fields.

Timestamps use `YYYY-MM-DDTHH:MM:SS[.ffffff]Z` or an explicit `+/-HH:MM`
offset of at most 14 hours. There may be one through six fractional second digits.
Calendar-invalid dates, naive times, leap seconds, invalid offset minutes and
UTC-conversion overflow are rejected. UTC normalization makes offset-equivalent
instants compare identically. No OS clock or timezone database is consulted.

## State transitions

| Event | State effect |
| --- | --- |
| First accepted tick | Store value, increment tick count, status `idle`. |
| Further accepted tick | Store value, increment count; `rising`, `falling`, or `steady` compares it with the previous stored value. |
| Pause | Set paused/status to `true`/`paused`; keep the last value. Repeated pause is permitted. |
| Valid tick while paused | Outcome `ignored`; advance sequence/time only. |
| Resume | Set paused/status to `false`/`idle`; keep the last value for the next comparison. Repeated resume is permitted. |
| Invalid event | Outcome `rejected`, a fixed reason code, no state change. |

Input order is preserved, never sorted. Replay starts empty on each call, does
not mutate the supplied document, and returns new dictionaries/lists. Each trace
row contains only an input index, fixed diagnostic strings, state, count and
validated numeric text. Raw invalid input is not echoed.

Invalid root schema or JSON rejects the whole request (CLI exit 2). Bad individual
events remain in the trace as rejections; the replay still completes (exit 0).
CLI input is UTF-8 JSON read from stdin, bounded to 256 KiB and 16 container levels. Duplicate keys at any
depth and nonstandard JSON constants are rejected. Input may not reference files
or URLs. The Python API accepts already-parsed plain JSON data, with the same
schema/event count limits; the byte limit belongs to the stdin parser.

This is a state-machine contract, not a model of a real market or execution venue.
