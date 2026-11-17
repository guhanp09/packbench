"""Download the original CALCE archives; do not relabel them as our measurements."""

import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "capacity.zip": "https://web.calce.umd.edu/batteries/data/SP1_Initial%20capacity_10_16_2015.zip",
    "dst.zip": "https://web.calce.umd.edu/batteries/data/SP2_25C_DST.zip",
}


def main():
    expected_path = ROOT / "data/sources.json"
    expected = json.loads(expected_path.read_text()) if expected_path.exists() else {}
    records = {}
    for name, url in SOURCES.items():
        path = ROOT / "data/raw" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            with urllib.request.urlopen(url, timeout=60) as response:
                path.write_bytes(response.read())
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if name in expected and digest != expected[name]["sha256"]:
            raise ValueError(f"Source checksum changed: {name}")
        records[name] = {
            "url": url,
            "sha256": digest,
            "bytes": path.stat().st_size,
            "provider": "University of Maryland CALCE",
            "acquired": "2026-11-17",
        }
    expected_path.write_text(json.dumps(records, indent=2) + "\n")
    print("CALCE archives present; source checksums verified")


if __name__ == "__main__":
    main()
