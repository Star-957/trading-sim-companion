"""Bounded JSON input and a standalone HTML report; no network or file discovery."""

from html import escape
import json

from .validation import InputError

MAX_BYTES = 262144
MAX_DEPTH = 16


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError("duplicate_key")
        result[key] = value
    return result


def _constant(_value):
    raise InputError("json_constant")


def _depth_limit(raw):
    # Count structural brackets only; quoted/escaped brackets are ordinary data.
    depth, quoted, escaped = 0, False, False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            if depth > MAX_DEPTH:
                raise InputError("json_depth")
        elif byte in (93, 125):
            depth -= 1


def load_document(stream):
    """Read at most 256 KiB + 1 byte from a binary stream, never a URL."""
    raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise InputError("input_too_large")
    _depth_limit(raw)
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                          parse_constant=_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as error:
        if isinstance(error, InputError):
            raise
        raise InputError("invalid_json") from None


def render_html(result):
    """Render only a validated replay result. Escape every dynamic text field."""
    def text(value):
        return escape(str(value if value is not None else "-"), quote=True)

    rows = "".join(
        "<tr>" + "".join(f"<td>{text(row[key])}</td>" for key in
                          ("index", "outcome", "reason", "status", "last_price")) + "</tr>"
        for row in result["trace"]
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Synthetic replay companion</title>
<style>
:root{{color-scheme:light dark}}body{{margin:0;background:#102b2a;color:#f2f6eb;font:16px/1.55 system-ui,sans-serif}}
main{{max-width:960px;margin:auto;padding:40px 24px}}h1{{font-size:clamp(28px,5vw,48px);line-height:1.12;margin:12px 0}}
.tag{{color:#e0d68a;letter-spacing:.12em;font-size:13px;font-weight:700}}.intro{{max-width:650px}}
.card{{display:flex;gap:24px;align-items:center;border:1px solid #91aaa0;padding:24px;margin:28px 0;border-radius:16px}}
.card>div:last-child{{min-width:0;overflow-wrap:anywhere}}
.bot{{flex:0 0 76px;height:70px;background:#e0d68a;border-radius:20px;position:relative}}
.bot:before,.bot:after{{content:'';position:absolute;top:25px;width:9px;height:13px;background:#102b2a;border-radius:50%}}
.bot:before{{left:20px}}.bot:after{{right:20px}}.status{{font-size:26px;font-weight:700;margin:0}}
.scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}}
th,td{{text-align:left;padding:10px 12px;border-bottom:1px solid #5c7a70}}th{{color:#e0d68a}}
footer{{margin-top:28px;color:#c6d5ca;font-size:14px}}code{{color:#e0d68a}}
</style></head><body><main>
<div class="tag">OFFLINE ENGINEERING DEMO</div><h1>Synthetic replay companion</h1>
<p class="intro">A deterministic state machine with a small, original placeholder companion.
All values are invented. This is not real trading, a trading strategy, or a profitability demonstration.</p>
<section class="card" aria-label="Final replay state"><div class="bot" aria-hidden="true"></div><div>
<p class="status">{text(result['status'])}</p><div>{text(result['symbol'])} &middot;
{text(result['tick_count'])} accepted ticks &middot; last synthetic price {text(result['last_price'])}</div></div></section>
<h2>Event trace</h2><p>Rejected events leave state unchanged. Valid ticks while paused advance the event cursor only.</p>
<div class="scroll"><table><caption>Replay results in supplied order</caption><thead><tr>
<th scope="col">Index</th><th scope="col">Outcome</th><th scope="col">Reason</th><th scope="col">State</th><th scope="col">Price</th>
</tr></thead><tbody>{rows}</tbody></table></div>
<footer>No scripts, external assets, analytics, network calls, account integrations or order submission.</footer>
</main></body></html>"""
