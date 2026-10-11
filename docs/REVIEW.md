# Review contract and limits

This repository is reviewed as an offline engineering demo. Passing checks do
not establish financial validity, independent security certification or absence
of every possible defect.

The publication boundary is an allowlisted source tree with a new root history
and a GitHub noreply identity. Private source snapshots and machine-specific
review records stay outside this repository. No CI workflows, dependency update
bots, hosting, deployments, releases or package publishing are included.

The checks are:

1. Review every included source file, import, input and output. No external I/O
   is present in the replay path; the CLI uses stdin/stdout only.
2. Test correctness, invalid input, timestamp boundaries, rejection atomicity,
   sequence/time ordering, finite bounded values, output escaping and resource caps.
3. Run tests with sockets and subprocesses denied by a process-local audit hook.
4. Rebuild reproducibly, install the wheel in a new environment with package
   indexes disabled, and run the installed package away from the source tree.
5. Verify the exact public tree/revision from a fresh public clone, then perform
   distinct data-flow and adversarial review passes. Record and fix actionable
   findings, with regression tests. Repeat on the corrected revision.

Tests use invented fixed fixtures and a seeded malformed-input sweep. The byte
and event bounds constrain the documented JSON path; arbitrary Python objects,
concurrent caller mutation and malicious interpreter modification are outside
the API contract. The HTML renderer is intended for validated replay output.
The synthetic marker is a schema declaration, not a data provenance detector.

Review passes performed by the implementation agent are self-review, even when
their checklists differ. Automated tests are separately reproducible. Review
findings, exact revisions and fresh-clone results are reported with the release
handoff; this document specifies checks rather than claiming unperformed runs.

## Optional browser layout regression

The application, build and standard test suite need only Python. Layout checking
additionally uses an already-installed Node.js, Playwright module and Chromium;
the following commands do not download or install them:

```text
python tools/render_layout_fixtures.py ../layout-reports
node tests/browser_layout.mjs PATH_TO_PLAYWRIGHT/index.mjs ../layout-reports
```

Choose a new report directory. The regression launches a disposable headless
Chromium with its sandbox enabled, reads local synthetic HTML, blocks page requests
outside `file:`, and closes the browser. It checks default and maximum-length valid
symbol/price reports at 320, 390 and 1280 CSS pixels. Both the page and actual text
rectangles must stay within their bounds; merely clipping overflowing text fails.
It writes two 320px screenshots beside the reports and prints measured geometry.
An overflow or missing boundary value returns exit 1. This is a browser geometry
check, not Safari/Firefox/mobile hardware or screen-reader certification.
