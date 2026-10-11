"""Write fixed synthetic reports for the optional browser layout regression."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trading_sim_companion import replay
from trading_sim_companion.demo import scenario
from trading_sim_companion.io import render_html


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="a new output directory")
    output = parser.parse_args().output
    boundary = scenario()
    boundary["symbol"] = "SIM_" + "X" * 16
    event = boundary["events"][0]
    event["bid"] = event["ask"] = event["price"] = "1000000000.000000"
    boundary["events"] = [event]
    reports = {"default": scenario(), "boundary": boundary}
    output.mkdir(parents=True, exist_ok=False)
    for name, document in reports.items():
        (output / f"{name}.html").write_text(render_html(replay(document)), encoding="utf-8")


if __name__ == "__main__":
    main()
