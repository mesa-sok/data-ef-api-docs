#!/usr/bin/env python3
"""
Script: fetch_csv_datasets.py

Fetches ALL public dataset metadata with CSV format from the Data EF API.
Uses a single large-page request (page_size=10000) to avoid pagination.
Validates the pulled count against the API-reported total before saving.

Usage:
    uv run scripts/fetch_csv_datasets.py

Output file:
    csv_datasets_<YYYYMMDD_HHMMSS>.json
"""

from pathlib import Path
import sys
import json
from datetime import datetime, timezone

# Resolve project root relative to this script
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from data_ef_api import DataEFClient


def main() -> None:
    with DataEFClient(verify=False) as client:
        print("Fetching all CSV datasets from API...")
        response = client.get_public_datasets(
            data_formats="CSV",
            sort_by="NEWEST",
            page=1,
            page_size=10000,
        )

        data = response.data
        csv_datasets = data.results or [] if data else []

        # ── Count validation ──────────────────────────────────────────
        api_total = data.total if data else None
        pulled = len(csv_datasets)

        print(f"\n  API reported total : {api_total}")
        print(f"  Records pulled     : {pulled}")

        if api_total is not None and pulled != api_total:
            print(f"  ⚠️  MISMATCH — expected {api_total}, got {pulled}. "
                  "Consider increasing page_size or paginating.")
        elif api_total is not None:
            print(f"  ✅ Count matches — all {pulled} records retrieved.")
        else:
            print("  ⚠️  API did not return a total count. Cannot verify completeness.")

    # ── Print a summary table ─────────────────────────────────────────────────
    print(f"\n{'#':<6} {'Format':<8} {'Org':<10} Title")
    print("-" * 80)
    for i, ds in enumerate(csv_datasets, start=1):
        title = ds.get("name") or "Unknown"
        # The API returns a single 'format' string, NOT a list
        fmt = ds.get("format") or "?"
        org = (ds.get("organization") or {}).get("abbreviation") or "?"
        print(f"{i:<6} {fmt:<8} {org:<10} {title}")

    # ── Build payload and save ────────────────────────────────────────────────
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    payload = {
        "fetched_at": fetched_at,
        "api_reported_total": api_total,
        "pulled_count": pulled,
        "count_matched": (api_total == pulled) if api_total is not None else None,
        "datasets": csv_datasets,
    }

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    output_dir = Path("artifacts")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"csv_datasets_{timestamp}.json"

    with open(output_file, mode="w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to: {output_file}  (fetched_at: {fetched_at})")


if __name__ == "__main__":
    main()

