# Trading Sim Companion

A small **offline engineering demo**: replay invented price events, inspect
deterministic state transitions, and generate a standalone HTML report with an
original geometric placeholder companion.

**This is not real trading.** There are no accounts, orders, strategies, returns,
profitability claims, broker connectors, external data, AI calls or network clients.
The word “price” is just a synthetic numeric signal for exercising a state machine.

## Run

Requires Python 3.12 or newer. No third-party dependencies and no downloads are
needed after obtaining the source and Python.

```text
python -m trading_sim_companion
python -m unittest discover -s tests -v
python tools/offline_check.py
```

The default scenario always produces the same eight-event trace: rising values,
pause, ignored tick, resume, falling value, rejected invalid price, and steady value.
It ends with four accepted ticks at the invented value `99.50`.

To generate `report.html` locally:

```text
python -c "from pathlib import Path; from trading_sim_companion import replay; from trading_sim_companion.demo import scenario; from trading_sim_companion.io import render_html; Path('report.html').write_text(render_html(replay(scenario())), encoding='utf-8')"
```

Open that file in a browser. The report has no JavaScript, external fonts, images,
analytics or server. No hosting is configured.

## Synthetic input

`examples/synthetic.json` is an editable copy of the built-in scenario. On a shell
with input redirection, run:

```text
python -m trading_sim_companion --stdin < examples/synthetic.json
```

In PowerShell:

```powershell
Get-Content -Raw examples/synthetic.json | python -m trading_sim_companion --stdin
```

Use invented values only. The `synthetic: true` flag records intent; it cannot
prove where user-provided values came from. Unknown fields are rejected to keep
the format small. Do not put personal records or credentials in the input.

The schema and exact state semantics are in [docs/FORMAT.md](docs/FORMAT.md).
The Python API is `replay(document)`: it has no I/O and returns detached,
JSON-compatible state and per-event results.

## Build and clean offline install

```text
python tools/build.py
python -m venv .venv
```

Then install the wheel without contacting a package index:

```text
.venv/Scripts/python -m pip --isolated install --no-index --no-deps dist/trading_sim_companion-0.1.0-py3-none-any.whl
.venv/Scripts/python -I -m trading_sim_companion
```

On macOS/Linux use `.venv/bin/python` instead. The build uses only the standard
library and creates both a wheel and `dist/trading-sim-companion.pyz`. The zipapp
also runs with `python dist/trading-sim-companion.pyz`. Neither artifact is
published to a package registry. Archive entries use a fixed timestamp and sorted
paths; rebuilding with the same Python/zlib produces the same bytes.

## Scope and evidence

- Strict decimal strings and offset-aware timestamps; bounded input and trace size.
- Rejected events do not alter state or consume the accepted sequence cursor.
- Valid ticks while paused advance sequence/time but do not change the last value.
- A process-local test hook denies socket and child-process activity; it is a
  regression detector, not a general-purpose security sandbox.
- Tests cover malformed JSON, duplicates, extremes, chronology, pause/resume,
  atomic rejection, output escaping and deterministic replay.

See [PROVENANCE.md](PROVENANCE.md) for the original-code boundary and excluded
upstream components, and [docs/REVIEW.md](docs/REVIEW.md) for review scope and limits.
MIT license covers the original source in this repository only. The source
application and its third-party components are not relicensed by this export.
