from __future__ import annotations

from pathlib import Path
import json
import sys

from act_sources import ACT_SOURCES

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"

def validate_act(act_code: str) -> bool:
    path = PROCESSED_DIR / f"{act_code.lower()}_2023_sections.json"
    if not path.exists():
        print(f"[FAIL] Missing {path}")
        return False

    records = json.loads(path.read_text(encoding="utf-8"))
    expected = ACT_SOURCES[act_code]

    if not records:
        print(f"[FAIL] {act_code}: no records")
        return False

    failures = []
    section_numbers = []

    for record in records:
        required = [
            "id", "act", "act_title", "section",
            "source_url",
        ]

        missing = [key for key in required if not record.get(key)]

        if missing:
            failures.append(
                f"section {record.get('section')}: missing {missing}"
            )

        # A valid section must contain legal content either in its title,
        # its body text, or both.
        if not record.get("title") and not record.get("text"):
            failures.append(
                f"section {record.get('section')}: missing both title and text"
    )

        if record.get("act") != act_code:
            failures.append(
                f"section {record.get('section')}: wrong act"
            )

        if record.get("source_url") != expected["url"]:
            failures.append(
                f"section {record.get('section')}: unexpected source URL"
            )

        try:
            section_numbers.append(int(record["section"]))
        except (ValueError, TypeError):
            failures.append(f"invalid section number: {record.get('section')}")

    if len(section_numbers) != len(set(section_numbers)):
        failures.append("duplicate section numbers detected")

    if failures:
        print(f"[FAIL] {act_code}:")
        for failure in failures[:20]:
            print(f"  - {failure}")
        return False

    print(
        f"[PASS] {act_code}: {len(records)} sections, "
        f"range {min(section_numbers)}–{max(section_numbers)}"
    )
    return True

def main():
    requested = sys.argv[1:] or list(ACT_SOURCES.keys())
    ok = all(validate_act(code) for code in requested)
    raise SystemExit(0 if ok else 1)

if __name__ == "__main__":
    main()
