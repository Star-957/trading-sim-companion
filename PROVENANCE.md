# Original-code boundary

This repository is a narrow engineering extraction, not a repackaging of the
source application. The owner authorized publication of separable original work.

| Included material | Origin and changes |
| --- | --- |
| `validation.py` timestamp/number helpers | Adapted from the owner's original standard-library-only validation module; now restricted to bounded textual input, fixed diagnostics, strict timestamp/decimal syntax and smaller numeric limits. |
| Observation age check | Adapted from the same module's future/stale timestamp guard; supplied event times replace wall-clock and market-session behavior. |
| Event replay, parser, CLI, report, fixture, build tools, tests and documentation | Newly authored for this demo. |
| Placeholder graphic | Newly authored CSS geometry; no character art, screenshots, fonts or media copied. |

The inspected original validation module imported only `datetime` and `decimal`.
Its initial tracked source predates the later vendor integration and does not
import or call those components. This export does not import the original
application at all. The full source tree and wheel can be read and tested with
only Python's standard library.

## Excluded third-party material

The source application contains distinct third-party subsets with different
licenses. None of their code, prompts, data, documentation or assets are included:

- [PA_Agent](https://github.com/rosemarycox5334-debug/PA_Agent): the inspected
  vendored notices identify **AGPL-3.0-or-later**. Its original notices and license
  remain with the source application; this export does not replace them.
- [AipcCode/pa](https://github.com/AipcCode/pa): the inspected subset carries
  **MIT** notices. None of that subset was copied into this repository.
- backtesting, research integrations, exchange calendars, GUI libraries and
  broker SDKs: absent, including their adapters and examples.

There is no claim that mixing MIT and AGPL source permits changing AGPL code to
MIT. The license decision relies on exclusion and separation, not on deleting
notices. Adding any upstream material later requires a new provenance/license
review. The MIT grant here covers only the original material actually included.

No original history, account configuration, credentials, private logs, financial
records, historical prices or original media are part of the public tree.
