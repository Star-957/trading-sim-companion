"""Synthetic-only correctness, parser, privacy and adversarial regressions."""

from copy import deepcopy
from datetime import timezone
from decimal import Decimal, localcontext
import io
import json
from pathlib import Path
import random
import unittest
from unittest.mock import patch

from trading_sim_companion import InputError, replay
from trading_sim_companion.__main__ import main
from trading_sim_companion.demo import scenario
from trading_sim_companion.io import MAX_BYTES, load_document, render_html
from trading_sim_companion.validation import number, timestamp


def document(events=None):
    value = scenario()
    if events is not None:
        value["events"] = events
    return value


def tick(**changes):
    value = scenario()["events"][0]
    value.update(changes)
    return value


class ValidationTests(unittest.TestCase):
    def test_price_domains(self):
        for value in ["0.000001", "1", "10.125000", "1000000000"]:
            with self.subTest(value=value):
                self.assertEqual(number(value), Decimal(value))

    def test_adversarial_prices(self):
        for value in [None, True, False, 1, 1.5, [], {}, "", "0", "-1", "+1", " 1", "1 ",
                      "01", "1_000", "1e3", "1e999999999", "NaN", "sNaN", "Infinity",
                      "0.0000001", "1000000001", "9" * 10000, "1\n", "\u0661", "<svg/onload=alert(1)>"]:
            with self.subTest(value=str(value)[:25]):
                with self.assertRaises(InputError):
                    number(value)

    def test_numeric_output_ignores_decimal_precision(self):
        with localcontext() as context:
            context.prec = 1
            self.assertEqual(str(number("123.456000")), "123.456000")

    def test_timestamp_offsets_and_precision(self):
        self.assertEqual(timestamp("2030-01-01T01:00:00+01:00"), timestamp("2030-01-01T00:00:00Z"))
        self.assertEqual(timestamp("2030-01-01T00:00:00.123456Z").microsecond, 123456)
        self.assertIs(timestamp("2030-01-01T00:00:00Z").tzinfo, timezone.utc)

    def test_timestamp_rejections(self):
        for value in [None, {}, [], True, "2030-01-01", "2030-01-01T00:00:00", "2030-02-30T00:00:00Z",
                      "2030-01-01 00:00:00Z", "2030-01-01T00:00:60Z", "0001-01-01T00:00:00+14:00",
                      "9999-12-31T23:59:59-14:00", "2030-01-01T00:00:00+15:00",
                      "2030-01-01T00:00:00+00:99", "2030-01-01T00:00:00.1234567Z", "x" * 10000]:
            with self.subTest(value=str(value)[:40]):
                with self.assertRaises(InputError):
                    timestamp(value)


class ReplayTests(unittest.TestCase):
    def test_demo_expected_trace(self):
        value = replay(scenario())
        self.assertEqual(value["tick_count"], 4)
        self.assertEqual(value["status"], "steady")
        self.assertEqual(value["last_price"], "99.50")
        self.assertEqual([row["outcome"] for row in value["trace"]],
                         ["accepted", "accepted", "accepted", "ignored", "accepted", "accepted", "rejected", "accepted"])

    def test_input_and_output_are_detached(self):
        source = scenario()
        backup = deepcopy(source)
        result = replay(source)
        self.assertEqual(source, backup)
        result["trace"].clear()
        self.assertEqual(replay(source), replay(backup))

    def test_rejected_event_is_atomic(self):
        first = tick()
        bad = tick(seq=999, at="2030-01-01T00:50:00Z", price="NaN")
        following = tick(seq=2, at="2030-01-01T00:00:02Z")
        control = replay(document([first, following]))
        result = replay(document([first, bad, following]))
        self.assertEqual(result["trace"][1]["outcome"], "rejected")
        self.assertEqual({k: v for k, v in result.items() if k != "trace"},
                         {k: v for k, v in control.items() if k != "trace"})

    def test_duplicate_and_out_of_order_sequences(self):
        for seq in [1, 0, -1, True, 1.0, "2", 1000000001]:
            result = replay(document([tick(), tick(seq=seq)]))
            self.assertEqual(result["tick_count"], 1)
            self.assertEqual(result["last_seq"], 1)
            self.assertEqual(result["trace"][-1]["outcome"], "rejected")

    def test_reversed_time_rejected_equal_time_allowed(self):
        self.assertEqual(replay(document([tick(), tick(seq=2)]))["tick_count"], 2)
        self.assertEqual(replay(document([tick(), tick(seq=2, at="2030-01-01T00:00:00Z")]))["tick_count"], 1)

    def test_freshness_boundaries(self):
        for observed, accepted in [("2030-01-01T00:00:01Z", True), ("2029-12-31T23:59:58Z", True),
                                    ("2029-12-31T23:59:57.999999Z", False), ("2030-01-01T00:00:01.000001Z", False)]:
            self.assertEqual(replay(document([tick(observed_at=observed)]))["tick_count"], int(accepted))

    def test_invalid_tick_book(self):
        for patch_values in [{"bid": "111"}, {"ask": "89"}, {"price": "111"}, {"price": "89"}, {"bid": []}]:
            self.assertEqual(replay(document([tick(**patch_values)]))["tick_count"], 0)

    def test_paused_tick_does_not_change_price(self):
        result = replay(document(scenario()["events"][:4]))
        self.assertEqual(result["last_price"], "101.25")
        self.assertEqual(result["last_seq"], 4)
        self.assertTrue(result["paused"])
        self.assertEqual(result["status"], "paused")

    def test_resume_and_first_tick_states(self):
        self.assertEqual(replay(document(scenario()["events"][:5]))["status"], "idle")
        self.assertEqual(replay(document([tick()]))["status"], "idle")
        self.assertEqual(replay(document(scenario()["events"][:6]))["status"], "falling")

    def test_empty_document_events(self):
        result = replay(document([]))
        self.assertEqual(result["status"], "idle")
        self.assertIsNone(result["last_price"])
        self.assertIsNone(result["last_at"])

    def test_document_and_unknown_field_rejections(self):
        for value in [None, [], {}, {**scenario(), "token": "synthetic-forbidden-marker"},
                      {**scenario(), "version": True}, {**scenario(), "version": 2},
                      {**scenario(), "synthetic": False}, {**scenario(), "synthetic": 1},
                      {**scenario(), "events": {}}, {**scenario(), "events": [None] * 1001}]:
            with self.assertRaises(InputError):
                replay(value)

    def test_only_fictitious_symbols(self):
        for symbol in ["REAL", "SIM_", "SIM_" + "X" * 17, "SIM_a", "SIM_\n", "../SIM_A", [],
                       "<script>", "SIM_\u212a", "SIM_\u0661"]:
            with self.assertRaises(InputError):
                replay({**scenario(), "symbol": symbol})

    def test_max_age_domain(self):
        for value in [None, True, -1, 60001, 1.0, "1", float("nan")]:
            with self.assertRaises(InputError):
                replay({**scenario(), "max_age_ms": value})
        for value in [0, 60000]:
            self.assertEqual(replay({**document([tick()]), "max_age_ms": value})["tick_count"], 1)

    def test_non_objects_and_malicious_event_fields(self):
        cases = [None, [], 1, "text", {"kind": []}, {"kind": {}}, {"kind": "order"},
                 tick(secret="synthetic-forbidden-marker"), {k: v for k, v in tick().items() if k != "at"}]
        for event in cases:
            result = replay(document([event]))
            self.assertEqual(result["trace"][0]["outcome"], "rejected")
            self.assertEqual(result["last_seq"], 0)
            self.assertNotIn("synthetic-forbidden-marker", json.dumps(result))

    def test_thousand_events_and_no_state_leak_between_runs(self):
        result = replay(document([tick(seq=n) for n in range(1, 1001)]))
        self.assertEqual(result["tick_count"], 1000)
        self.assertEqual(replay(document([]))["tick_count"], 0)

    def test_deterministic_seeded_invalid_input_sweep(self):
        generator = random.Random(947)
        replacements = [None, [], {}, True, -1, "", "NaN", "<script>", 1e100, "9" * 200]
        for _ in range(500):
            event = tick()
            event[generator.choice(list(event))] = generator.choice(replacements)
            value = document([event, tick(seq=2)])
            first = replay(value)
            self.assertEqual(first, replay(deepcopy(value)))
            json.dumps(first, allow_nan=False)
            self.assertLessEqual(first["tick_count"], 2)


class InputAndOutputTests(unittest.TestCase):
    def test_json_roundtrip(self):
        self.assertEqual(load_document(io.BytesIO(json.dumps(scenario()).encode())), scenario())

    def test_depth_limit_ignores_escaped_string_brackets(self):
        value = {"text": '[{\\"' * 2000}
        self.assertEqual(load_document(io.BytesIO(json.dumps(value).encode())), value)
        self.assertEqual(load_document(io.BytesIO(b'[' * 16 + b']' * 16)), [[[[[[[[[[[[[[[[]]]]]]]]]]]]]]]])
        with self.assertRaisesRegex(InputError, "json_depth"):
            load_document(io.BytesIO(b'[' * 17 + b']' * 17))

    def test_json_adversarial_inputs(self):
        for raw in [b'{"version":1,"version":1}', b'{"events":[{"x":1,"x":2}]}', b'NaN', b'Infinity',
                    b'-Infinity', b'\xff', b'{', b'[] trailing', b'[' * 2000 + b']' * 2000,
                    b'{"x":' + b'9' * 10000 + b'}']:
            with self.subTest(prefix=raw[:20]):
                with self.assertRaises(InputError):
                    load_document(io.BytesIO(raw))

    def test_byte_limit_reads_one_bounded_chunk(self):
        class RecordingStream(io.BytesIO):
            def read(self, size):
                self.requested = size
                return super().read(size)
        stream = RecordingStream(b' ' * (MAX_BYTES + 10))
        with self.assertRaisesRegex(InputError, "input_too_large"):
            load_document(stream)
        self.assertEqual(stream.requested, MAX_BYTES + 1)
        self.assertEqual(load_document(io.BytesIO(b'[]' + b' ' * (MAX_BYTES - 2))), [])

    def test_static_report_has_no_active_network_content(self):
        html = render_html(replay(scenario()))
        for banned in ["<script", "<iframe", "<img", "<form", "http://", "https://", "javascript:", "url(", "@import"]:
            self.assertNotIn(banned, html.lower())
        self.assertIn("default-src 'none'", html)
        self.assertIn("not real trading", html)

    def test_html_escapes_dynamic_values(self):
        result = replay(scenario())
        result["symbol"] = '<script>alert("x")</script>'
        result["trace"][0]["reason"] = '<img src=x onerror="alert(1)">'
        html = render_html(result)
        self.assertNotIn("<script>", html)
        self.assertNotIn("<img", html)
        self.assertIn("&lt;script&gt;", html)

    def test_cli_demo_and_stdin(self):
        for args in [[], ["--stdin"], ["--format", "html"]]:
            incoming = io.TextIOWrapper(io.BytesIO(json.dumps(scenario()).encode()), encoding="utf-8")
            outgoing = io.StringIO()
            with patch("sys.stdin", incoming), patch("sys.stdout", outgoing):
                self.assertEqual(main(args), 0)
            self.assertIn("SIM_ORB", outgoing.getvalue())

    def test_cli_rejects_without_echo_or_traceback(self):
        incoming = io.TextIOWrapper(io.BytesIO(b'{"private":"synthetic-forbidden-marker"}'), encoding="utf-8")
        outgoing, errors = io.StringIO(), io.StringIO()
        with patch("sys.stdin", incoming), patch("sys.stdout", outgoing), patch("sys.stderr", errors):
            self.assertEqual(main(["--stdin"]), 2)
        self.assertEqual(outgoing.getvalue(), "")
        self.assertEqual(errors.getvalue(), "Input rejected: document_fields\n")

    def test_fixture_matches_builtin(self):
        root = Path(__file__).resolve().parents[1]
        with (root / "examples" / "synthetic.json").open("rb") as source:
            self.assertEqual(load_document(source), scenario())


if __name__ == "__main__":
    unittest.main()
