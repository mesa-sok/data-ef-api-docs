#!/usr/bin/env python3
"""
Script: explore_filters.py

Fetches the filter-options and count-data endpoints to understand how datasets
are distributed across categories, organisations, and data formats.

Run this FIRST to decide which filter strategy (if any) suits your use-case
before running fetch_all_datasets.py.

Usage:
    uv run scripts/explore_filters.py

Output example
--------------
Total: 142 datasets  /  87 datasources

=== Categories (14) ===
  finance                 : 38 datasets
  agriculture             : 22 datasets
  ...

=== Organisations (11) ===
  ministry-of-finance     : 55 datasets
  ...

=== Data Formats (5) ===
  CSV   : 98 datasets
  XLSX  : 44 datasets
  ...
"""

import sys

sys.path.insert(0, "src")

from data_ef_api import DataEFClient


def main() -> None:
    with DataEFClient() as client:
        # ── Total counts ───────────────────────────────────────────
        counts = client.get_count_data()
        print(f"\nTotal: {counts.datasets} datasets  /  {counts.datasources} datasources\n")

        # ── Filter options ─────────────────────────────────────────
        opts = client.get_filter_options()

        def _show(title: str, items: list | None) -> None:
            if not items:
                print(f"\n=== {title} (0) ===\n  (none)\n")
                return
            print(f"\n=== {title} ({len(items)}) ===")
            for item in sorted(items, key=lambda x: -(x.count or 0)):
                slug = item.slug or item.id or "?"
                count = item.count if item.count is not None else "?"
                name = item.name or slug
                print(f"  {slug:<30}  {count:>6} datasets   [{name}]")

        _show("Categories", opts.categories)
        _show("Organisations", opts.organizations)
        _show("Data Formats", opts.data_formats)

        # ── Recommendation ─────────────────────────────────────────
        print("\n" + "=" * 60)
        print("  RECOMMENDATION")
        print("=" * 60)
        print(
            """
To pull ALL datasets metadata without duplicates use simple pagination:

    GET /api/v1/public-datasets?page=1&page_size=10000

This is a single request that returns every dataset (max page_size is 10 000,
which covers the entire catalogue in one shot unless there are >10 000 entries).

Use category / organisation filters ONLY when you need datasets grouped by
those dimensions — they can cause duplicates if a dataset belongs to multiple
categories.

To pull the actual row data for each dataset:
  1. Preferred  →  GET /api/v1/public-datasets/{id}/file
     Download the original file (CSV, XLSX, …).  Fast and complete.
  2. Fallback   →  GET /api/v1/public-datasets/{id}/json  (paginated, max 200/page)
     Use when no downloadable file is available.
"""
        )


if __name__ == "__main__":
    main()
