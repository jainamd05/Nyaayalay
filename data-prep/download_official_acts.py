from pathlib import Path
import sys
import time

import requests

from act_sources import ACT_SOURCES

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "data" / "raw" / "source_pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Nyayalay-Legal-Corpus-Builder/1.0",
}

def download_act(act_code: str, timeout: int = 60) -> Path:
    if act_code not in ACT_SOURCES:
        raise ValueError(
            f"Unknown act {act_code}. Available: {', '.join(ACT_SOURCES)}"
        )

    source = ACT_SOURCES[act_code]
    destination = PDF_DIR / source["filename"]

    response = requests.get(
        source["url"],
        headers=HEADERS,
        timeout=(20, 300),
    )
    response.raise_for_status()

    content_type = response.headers.get("content-type", "")
    if "pdf" not in content_type.lower() and not response.content.startswith(b"%PDF"):
        raise RuntimeError(
            f"{act_code}: expected a PDF but received content-type={content_type!r}"
        )

    destination.write_bytes(response.content)
    print(f"Downloaded {act_code}: {destination}")
    return destination

def main():
    requested = sys.argv[1:] or list(ACT_SOURCES.keys())

    for act_code in requested:
        started = time.time()
        download_act(act_code)
        print(f"Completed {act_code} in {time.time() - started:.1f}s")

if __name__ == "__main__":
    main()
