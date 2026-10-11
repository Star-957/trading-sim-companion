"""Write JSON or static HTML to stdout; optionally read synthetic JSON from stdin."""

import argparse
import json
import sys

from .demo import scenario
from .engine import replay
from .io import load_document, render_html
from .validation import InputError


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline synthetic event demo. Not real trading.")
    parser.add_argument("--stdin", action="store_true", help="read bounded synthetic JSON from stdin")
    parser.add_argument("--format", choices=("json", "html"), default="json")
    args = parser.parse_args(argv)
    try:
        result = replay(load_document(sys.stdin.buffer) if args.stdin else scenario())
        output = render_html(result) if args.format == "html" else json.dumps(result, indent=2, allow_nan=False)
        sys.stdout.write(output + "\n")
    except InputError as error:
        sys.stderr.write(f"Input rejected: {error}\n")
        return 2
    except OSError:
        sys.stderr.write("Input/output unavailable.\n")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
