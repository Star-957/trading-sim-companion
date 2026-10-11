"""Build a dependency-free wheel and zipapp using only Python's standard library."""

import base64
import csv
import hashlib
import io
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "trading_sim_companion"
VERSION = "0.1.0"
MODULES = ("__init__.py", "__main__.py", "validation.py", "engine.py", "io.py", "demo.py")


def archive(path, entries):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as target:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            target.writestr(info, data)


def main():
    entries = {f"{PACKAGE}/{name}": (ROOT / PACKAGE / name).read_bytes() for name in MODULES}
    license_text = (ROOT / "LICENSE").read_bytes()
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    metadata = f"{PACKAGE}-{VERSION}.dist-info"
    wheel = dict(entries)
    wheel[f"{metadata}/METADATA"] = (
        "Metadata-Version: 2.1\nName: trading-sim-companion\n"
        f"Version: {VERSION}\nSummary: Offline synthetic event replay demo\n"
        "Requires-Python: >=3.12\nLicense: MIT\n\n"
        "Engineering demo only. No real trading, accounts or network integrations.\n"
    ).encode()
    wheel[f"{metadata}/WHEEL"] = b"Wheel-Version: 1.0\nGenerator: stdlib-build\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
    wheel[f"{metadata}/LICENSE"] = license_text
    record = io.StringIO(newline="")
    writer = csv.writer(record, lineterminator="\n")
    for name, data in sorted(wheel.items()):
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        writer.writerow((name, f"sha256={digest}", len(data)))
    writer.writerow((f"{metadata}/RECORD", "", ""))
    wheel[f"{metadata}/RECORD"] = record.getvalue().encode()
    archive(dist / f"{PACKAGE}-{VERSION}-py3-none-any.whl", wheel)
    app = dict(entries)
    app["__main__.py"] = b"from trading_sim_companion.__main__ import main\nraise SystemExit(main())\n"
    app["LICENSE"] = license_text
    archive(dist / "trading-sim-companion.pyz", app)
    print("Built wheel and zipapp in dist/ (no package download).")


if __name__ == "__main__":
    main()
