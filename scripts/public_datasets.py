#!/usr/bin/env python3
"""
Script: public_datasets.py
Demonstrates all Public Datasets API endpoints.

Usage:
    uv run scripts/public_datasets.py
"""

import json
import sys

sys.path.insert(0, "src")

from data_ef_api import DataEFClient


def print_json(label: str, data: object) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print("=" * 60)
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main() -> None:
    with DataEFClient() as client:
        # 1. Homepage summary
        print_json("GET /api/v1/public-datasets/home", client.get_home())

        # 2. Count datasets & data-sources
        print_json(
            "GET /api/v1/public-datasets/count-data", client.get_count_data()
        )

        # 3. Filter options
        print_json(
            "GET /api/v1/public-datasets/filter-options",
            client.get_filter_options(),
        )

        # 4. Auto-suggest
        print_json(
            "GET /api/v1/public-datasets/auto-suggest?keyword=budget",
            client.get_auto_suggest("budget"),
        )

        # 5. List datasets
        print_json(
            "GET /api/v1/public-datasets (page 1, size 5)",
            client.get_public_datasets(page=1, page_size=5),
        )

        # 6. SEO metadata
        print_json(
            "GET /api/v1/public-datasets/seo", client.get_public_datasets_seo()
        )

        # 7. Single dataset (first result, if any)
        datasets = client.get_public_datasets(page=1, page_size=1)
        results = datasets.get("data", {}).get("results", []) if isinstance(datasets, dict) else []
        if results:
            first_id = results[0].get("id") or results[0].get("slug")
            if first_id:
                print_json(
                    f"GET /api/v1/public-datasets/{first_id}",
                    client.get_public_dataset(str(first_id)),
                )
                print_json(
                    f"GET /api/v1/public-datasets/{first_id}/file",
                    client.get_public_dataset_file(str(first_id)),
                )
                print_json(
                    f"GET /api/v1/public-datasets/{first_id}/json",
                    client.get_public_dataset_json(str(first_id), page=1, page_size=5),
                )


if __name__ == "__main__":
    main()
