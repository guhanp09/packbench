"""Execute evidence-producing checks and keep open physical requirements visible."""

import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    commands = {
        "tests": ["make", "test", "PYTHON=" + sys.executable],
        "arm": ["make", "arm"],
        "sanitizers": ["make", "sanitize"],
        "study": ["make", "study", "PYTHON=" + sys.executable],
    }
    runs = {}
    for name, command in commands.items():
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        (out / f"{name}.log").write_text((result.stdout + result.stderr).rstrip() + "\n")
        runs[name] = {"command": command, "exit_code": result.returncode}
        if result.returncode:
            print(result.stdout + result.stderr, file=sys.stderr)
            raise RuntimeError(f"{name} failed; inspect results/{name}.log")
    requirements = [
        (
            "PB-01",
            "Integrate measured Ah/Wh with explicit current sign",
            "passed",
            "tests.log;cell_report.md",
        ),
        (
            "PB-02",
            "Evaluate voltage prediction on a separate run without fitting on it",
            "passed",
            "metrics.json;cell_model.png",
        ),
        (
            "PB-03",
            "Reject corrupted packets and preserve signed units",
            "passed",
            "tests.log",
        ),
        (
            "PB-04",
            "Detect loss, timestamp problems and session-boundary truncation",
            "passed",
            "tests.log",
        ),
        ("PB-05", "Compile the telemetry core for Cortex-M0+", "passed", "arm.log"),
        (
            "PB-06",
            "Screen energy/current/voltage infeasibility of an assumed pack",
            "passed",
            "pack_screen.json;pack_sweep.csv",
        ),
        (
            "PB-07",
            "Retain input origin, specimen identity and hashes",
            "passed",
            "../data/sources.json;provenance.json",
        ),
        (
            "PB-08",
            "Verify calibrated physical acquisition and MCU timing",
            "open",
            "../docs/bench-plan.md",
        ),
        (
            "PB-09",
            "Verify real pack protection, cooling and failure response",
            "open",
            "../docs/evidence.md",
        ),
        (
            "PB-10",
            "Qualify a craft or obtain class approval",
            "outside scope",
            "../docs/evidence.md",
        ),
    ]
    with (out / "requirements.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["id", "requirement", "status", "evidence"])
        w.writerows(requirements)
    sources = [
        p
        for folder in ("src", "tools", "firmware", "tests")
        for p in (ROOT / folder).rglob("*")
        if p.suffix in (".py", ".c", ".h") and "__pycache__" not in p.parts
    ]
    artifacts = [
        p for p in out.iterdir() if p.is_file() and p.name != "provenance.json"
    ]
    record = {
        "data_owner": "University of Maryland CALCE",
        "physical_measurements_by_project": False,
        "commands": runs,
        "python": sys.version.split()[0],
        "packages": {
            n: importlib.metadata.version(n)
            for n in ("numpy", "scipy", "pandas", "openpyxl", "matplotlib", "pytest")
        },
        "source_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(sources)
        },
        "artifact_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(artifacts)
        },
    }
    (out / "provenance.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        "Executed checks pass; physical acquisition/protection requirements remain open."
    )


if __name__ == "__main__":
    main()
