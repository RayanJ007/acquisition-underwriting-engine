"""Fingerprint original data and source metadata for reproducibility."""

from pathlib import Path
import hashlib, json

ROOT = Path(__file__).resolve().parents[1]


def write_manifest() -> None:
    records = []
    for p in sorted((ROOT / "data/raw").iterdir()):
        if p.name == "manifest.json" or not p.is_file():
            continue
        records.append(
            {
                "file": p.name,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                "bytes": p.stat().st_size,
            }
        )
    (ROOT / "data/raw/manifest.json").write_text(json.dumps(records, indent=2))


if __name__ == "__main__":
    write_manifest()
