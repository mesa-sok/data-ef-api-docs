#!/usr/bin/env python3
"""
Script: fetch_all_datasets.py

Bulk-harvests ALL public dataset metadata and (optionally) their row data
from the Data EF Public API (https://data.mef.gov.kh/api/v1/).

Strategy
--------
1. Call ``/count-data`` to know the total number of datasets.
2. Fetch ALL metadata in one pass using ``page_size=10000`` (the API maximum).
   - No category or organisation filter → no duplicates, no missed datasets.
3. For each dataset, collect row data using the most efficient path:
   a. ``/file``  — returns download URLs for CSV/XLSX/etc.  **Preferred.**
      Files are complete and require only one request per dataset.
   b. ``/json``  — paginated JSON preview (max 200 rows / page).
      Used as fallback when no downloadable file exists.

Output
------
Results are written to:
  - ``output/metadata.json``   — list of dataset metadata objects
  - ``output/data_index.json`` — per-dataset mapping of id → file URLs / row count

Usage
-----
    uv run scripts/fetch_all_datasets.py

Options (edit the constants below or pass as env-vars):
    DATA_DIR      destination folder          (default: output/)
    MAX_DATASETS  cap number of datasets      (default: unlimited)
    FETCH_DATA    also fetch row data         (default: true)
    VERBOSE       print per-dataset progress  (default: true)
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")

from data_ef_api import DataEFClient

# ── Configuration ──────────────────────────────────────────────────────────────
DATA_DIR: Path = Path(os.getenv("DATA_DIR", "output"))
MAX_DATASETS: int | None = (
    int(os.getenv("MAX_DATASETS", "0")) or None
)  # None = no cap
FETCH_DATA: bool = os.getenv("FETCH_DATA", "true").lower() != "false"
VERBOSE: bool = os.getenv("VERBOSE", "true").lower() != "false"
PAGE_SIZE: int = 10_000  # maximum allowed by the API


# ── Helpers ────────────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    if VERBOSE:
        print(msg)


def save_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"  ✓ saved {path}")


# ── Step 1: collect all metadata ───────────────────────────────────────────────

def fetch_all_metadata(client: DataEFClient) -> list[dict]:
    """Return every dataset metadata record using minimal API requests."""
    counts = client.get_count_data()
    total = counts.get_datasets_count or 0
    log(f"\n[metadata] Total datasets reported: {total}")

    all_datasets: list[dict] = []
    page = 1

    while True:
        log(f"  → page {page} (page_size={PAGE_SIZE}) …")
        resp = client.get_public_datasets(
            sort_by="NEWEST",
            page=page,
            page_size=PAGE_SIZE,
        )

        data = resp.data
        if data is None:
            break

        results = data.results or []
        if not results:
            break

        all_datasets.extend(results)
        log(f"     collected {len(all_datasets)} / {data.total or '?'}")

        # Stop if we got everything or hit the optional cap
        total_pages = data.total_pages or math.ceil((data.total or len(results)) / PAGE_SIZE)
        if page >= total_pages:
            break
        if MAX_DATASETS and len(all_datasets) >= MAX_DATASETS:
            all_datasets = all_datasets[:MAX_DATASETS]
            break

        page += 1

    log(f"[metadata] Collected {len(all_datasets)} dataset records.\n")
    return all_datasets


# ── Step 2: collect file / row data for each dataset ──────────────────────────

def collect_dataset_id(record: dict) -> str | None:
    """Extract a usable identifier from a metadata record."""
    return (
        record.get("id")
        or record.get("slug")
        or record.get("uuid")
    )


def fetch_dataset_data(client: DataEFClient, dataset_id: str) -> dict:
    """
    Returns a dict describing what data is available for this dataset:
    {
        "id": str,
        "files": [{"name": ..., "format": ..., "url": ...}, ...],
        "json_row_count": int | None,   # only set when /file is empty
        "method": "file" | "json" | "none"
    }
    """
    result: dict = {"id": dataset_id, "files": [], "json_row_count": None, "method": "none"}

    # ── Try /file first ──────────────────────────────────────────
    try:
        file_info = client.get_public_dataset_file(dataset_id)
        files = file_info.files or []
        if files:
            result["files"] = [
                {
                    "name": f.name,
                    "format": f.format,
                    "url": f.url,
                    "size": f.size,
                }
                for f in files
            ]
            result["method"] = "file"
            return result
    except Exception as exc:  # noqa: BLE001
        log(f"     [warn] /file failed for {dataset_id}: {exc}")

    # ── Fallback: /json — just get row count from first page ─────
    try:
        preview = client.get_public_dataset_json(dataset_id, page=1, page_size=1)
        if preview.data:
            result["json_row_count"] = preview.data.total
            result["method"] = "json"
    except Exception as exc:  # noqa: BLE001
        log(f"     [warn] /json failed for {dataset_id}: {exc}")

    return result


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with DataEFClient(verify=False) as client:
        # ── 1. Fetch metadata ────────────────────────────────────
        metadata = fetch_all_metadata(client)
        save_json(DATA_DIR / "metadata.json", metadata)

        if not FETCH_DATA:
            log("\n[data] FETCH_DATA=false — skipping row-data collection.")
            return

        # ── 2. Fetch file info / row counts per dataset ──────────
        log(f"[data] Collecting file info for {len(metadata)} datasets …")
        data_index: list[dict] = []

        for i, record in enumerate(metadata, start=1):
            dataset_id = collect_dataset_id(record)
            if not dataset_id:
                log(f"  [{i}/{len(metadata)}] SKIP — no id in record")
                continue

            log(f"  [{i}/{len(metadata)}] {dataset_id}")
            entry = fetch_dataset_data(client, str(dataset_id))
            entry["title_en"] = record.get("title_en") or record.get("name")
            entry["title_kh"] = record.get("title_kh")
            entry["category"] = record.get("category")
            entry["organization"] = record.get("organization")
            data_index.append(entry)

        save_json(DATA_DIR / "data_index.json", data_index)

        # ── 3. Summary ───────────────────────────────────────────
        file_datasets = sum(1 for d in data_index if d["method"] == "file")
        json_datasets = sum(1 for d in data_index if d["method"] == "json")
        none_datasets = sum(1 for d in data_index if d["method"] == "none")
        total_files = sum(len(d["files"]) for d in data_index)

        print("\n" + "=" * 60)
        print("  SUMMARY")
        print("=" * 60)
        print(f"  Total datasets harvested : {len(metadata)}")
        print(f"  Have downloadable files  : {file_datasets}  ({total_files} files total)")
        print(f"  JSON-only (no file)      : {json_datasets}")
        print(f"  No data available        : {none_datasets}")
        print(f"\n  Output written to: {DATA_DIR.resolve()}/")
        print(f"    metadata.json   — {len(metadata)} records")
        print(f"    data_index.json — {len(data_index)} records")
        print("=" * 60)


if __name__ == "__main__":
    main()
