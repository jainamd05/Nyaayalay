"""
Starter section scraper.

Use only a source you are authorised to retrieve and reuse. The script
intentionally requires an explicit URL instead of silently depending on a
particular third-party site's URL structure.
"""

import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "bns_sections.json"


def parse_section(source_url: str):
    response = requests.get(source_url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text(" ", strip=True)

    record = {
        "act": "BNS",
        "section": "REPLACE_ME",
        "title": "REPLACE_ME",
        "text": text,
        "source_url": source_url,
    }

    OUT.write_text(
        json.dumps([record], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Saved starter record to {OUT}")


if __name__ == "__main__":
    raise SystemExit(
        "Review the source and parser before using this script."
    )
