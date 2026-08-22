"""
Starter scraper.

Do not hard-code or assume that a third-party website is an authoritative
source. Configure SOURCE_URL after verifying that you are permitted to
retrieve and reuse the content.
"""

from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "bns_index.json"


def fetch_index(source_url: str):
    response = requests.get(source_url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    links = []

    for anchor in soup.select("a[href]"):
        links.append(
            {
                "title": anchor.get_text(" ", strip=True),
                "url": anchor.get("href"),
            }
        )

    OUT.write_text(
        __import__("json").dumps(links, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Saved {len(links)} links to {OUT}")


if __name__ == "__main__":
    raise SystemExit(
        "Review and set an authorised SOURCE_URL in this script before using it."
    )
