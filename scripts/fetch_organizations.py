#!/usr/bin/env python3
"""
Script: fetch_organizations.py

Fetches all available organisations from the Data EF filter-options endpoint,
prints a summary table, and saves the result to a timestamped JSON file.

The saved JSON includes a top-level ``fetched_at`` field (ISO 8601 UTC) so
you always know when the snapshot was taken and can schedule incremental
pulls to detect when ``dataset_count`` changes.

Usage:
    uv run scripts/fetch_organizations.py

Output file:
    organizations_<YYYYMMDD_HHMMSS>.json

    {
      "fetched_at": "2026-04-08T04:00:00Z",
      "total": 48,
      "organizations": [
        {
          "id": 9,
          "abbreviation": "NIS",
          "label_en": "National Institute of Statistics",
          "label_kh": "វិទ្យាស្ថានជាតិស្ថិតិ",
          "dataset_count": 105
        },
        ...
      ]
    }

To pull datasets for a specific organisation later, use the ``id`` value:
    client.get_public_datasets(organizations="9")
"""

from pathlib import Path
import json
import sys
from datetime import datetime, timezone

# Resolve project root relative to this script
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from data_ef_api import DataEFClient


def main() -> None:
    with DataEFClient(verify=False) as client:
        print("Fetching filter options...")
        opts = client.get_filter_options()

    orgs = opts.organizations or []

    # Sort by dataset_count descending
    def get_dataset_count(org: list) -> int:
        return org.dataset_count or 0

    orgs_sorted = sorted(orgs, key=get_dataset_count, reverse=True)

    # ── Print summary table ───────────────────────────────────────────────────
    print(f"\n{'#':<4} {'ID':<6} {'Abbr':<12} {'Datasets':<10} English Name")
    print("-" * 75)
    for i, org in enumerate(orgs_sorted, start=1):
        print(
            f"{i:<4} {org.value!s:<6} {org.abbreviation or '?':<12} "
            f"{org.dataset_count or 0:<10} {org.label_en or 'Unknown'}"
        )
    print(f"\nTotal organisations: {len(orgs)}")

    # ── Build output payload ──────────────────────────────────────────────────
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    payload = {
        "fetched_at": fetched_at,
        "total": len(orgs),
        "organizations": [
            {
                "id": org.value,
                "abbreviation": org.abbreviation,
                "label_en": org.label_en,
                "label_kh": org.label_kh,
                "dataset_count": org.dataset_count,
            }
            for org in orgs_sorted
        ],
    }

    # ── Save to timestamped file ──────────────────────────────────────────────
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    output_dir = Path("artifacts")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"organizations_{timestamp}.json"

    with open(output_file, mode="w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to: {output_file}  (fetched_at: {fetched_at})")
    print(
        "\nTip: use the 'id' field to pull datasets for a specific org:\n"
        "     client.get_public_datasets(organizations='<id>')"
    )


if __name__ == "__main__":
    main()
