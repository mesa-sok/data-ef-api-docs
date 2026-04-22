#!/usr/bin/env python3
"""
standalone_export_datasets.py

A strictly standalone script — zero external dependencies, no DataEFClient,
no httpx, no pydantic. Only Python standard library modules are used.

  Standard library used:
    - urllib.request  → makes the HTTP GET request
    - ssl             → disables SSL verification (matches other scripts in this project)
    - json            → parses the API response
    - csv             → writes the output file
    - datetime        → generates the fetched_at timestamp and filename
    - pathlib.Path    → creates the output directory and builds the file path

What this script does, step by step:
  1. Builds the API URL with page_size=10000 to fetch all datasets in one request.
  2. Opens an HTTPS connection, disabling certificate verification (as the rest of
     this project does via verify=False).
  3. Reads and decodes the raw JSON response body.
  4. Navigates the response envelope: JSON → data → results (list of datasets).
  5. Validates that the number of records pulled matches the API's reported total.
  6. Flattens each nested record:
       - organization  (dict)   → name_en + abbreviation columns
       - categories    (list)   → joined into a single " | " separated string
  7. Writes one row per dataset to a CSV file under artifacts/.
  8. The filename contains only the date (YYYYMMDD), e.g. all_datasets_20260408.csv.
     The CSV itself contains a full ISO 8601 UTC timestamp in the fetched_at header comment.

Usage:
    python3 scripts/standalone_export_datasets.py

Output:
    artifacts/all_datasets_<YYYYMMDD>.csv
"""

import csv
import json
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


# ── Configuration ──────────────────────────────────────────────────────────────

API_BASE_URL = "https://data.mef.gov.kh"
ENDPOINT = "/api/v1/public-datasets"
PAGE_SIZE = 10000                   # Fetch everything in a single request
OUTPUT_DIR = Path("artifacts")      # Output directory (created automatically)


# ── Helpers ────────────────────────────────────────────────────────────────────

def fetch_json(url: str) -> dict:
    """Perform a GET request and return the parsed JSON body.

    SSL certificate verification is disabled to match the rest of the project's
    usage of DataEFClient(verify=False).
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "standalone-dataef-exporter/1.0"},
    )

    with urllib.request.urlopen(req, context=ctx) as response:
        return json.loads(response.read().decode("utf-8"))


def flatten_dataset(ds: dict) -> dict:
    """Flatten one dataset record from the API into a CSV-ready row.

    Nested fields handled:
      - organization (dict)  → organization, organization_abbr
      - categories   (list)  → categories (pipe-separated string)
    """
    org = ds.get("organization") or {}
    cats = ds.get("categories") or []

    # Join multiple category names with a readable separator
    cat_names = [c.get("name_en") or c.get("name_kh") or "" for c in cats]

    return {
        "id":                ds.get("id"),
        "name":              ds.get("name"),
        "format":            ds.get("format"),
        "frequency":         ds.get("frequency"),
        "organization":      org.get("name_en") or org.get("name_kh") or "",
        "organization_abbr": org.get("abbreviation") or "",
        "categories":        " | ".join(cat_names),
        "views":             ds.get("views_count"),
        "downloads":         ds.get("download_count"),
        "file_size_bytes":   ds.get("file_size"),
        "created_at":        ds.get("created_at"),
        "updated_at":        ds.get("updated_at"),
        "coverage_start":    ds.get("coverage_start"),
        "coverage_end":      ds.get("coverage_end"),
        "file_url":          ds.get("file_url"),
        "description":       ds.get("description"),
    }


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    url = f"{API_BASE_URL}{ENDPOINT}?page=1&page_size={PAGE_SIZE}"
    print(f"→ Fetching: {url}")

    try:
        body = fetch_json(url)
    except urllib.error.URLError as exc:
        print(f"✗ Network error: {exc}")
        return
    except json.JSONDecodeError as exc:
        print(f"✗ JSON parse error: {exc}")
        return

    # Navigate the response envelope. The Data EF API has two known shapes:
    # Shape A: { "data": { "results": [...], "total": N } }
    # Shape B: { "data": [...], "total_items": N }
    data_node = body.get("data")
    
    if isinstance(data_node, list):
        datasets = data_node
        api_total = body.get("total_items")
    elif isinstance(data_node, dict):
        datasets = data_node.get("results") or []
        api_total = data_node.get("total")
    else:
        datasets = []
        api_total = None

    pulled = len(datasets)

    # ── Count validation ──────────────────────────────────────────────────────
    print(f"\n  API reported total : {api_total}")
    print(f"  Records pulled     : {pulled}")

    if api_total is not None and pulled != api_total:
        print(f"  ⚠️  MISMATCH — expected {api_total}, got {pulled}.")
    elif api_total is not None:
        print(f"  ✅ Count matches — all {pulled} records retrieved.")
    else:
        print("  ⚠️  API did not return a total count. Cannot verify completeness.")

    if not datasets:
        print("\nNo datasets found — nothing to export.")
        return

    # ── Build output path ─────────────────────────────────────────────────────
    fetched_at   = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    date_stamp   = datetime.now(timezone.utc).strftime("%Y%m%d")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path     = OUTPUT_DIR / f"all_datasets_{date_stamp}.csv"

    # ── Write CSV ─────────────────────────────────────────────────────────────
    fieldnames = [
        "id", "name", "format", "frequency",
        "organization", "organization_abbr", "categories",
        "views", "downloads", "file_size_bytes",
        "created_at", "updated_at", "coverage_start", "coverage_end",
        "file_url", "description",
    ]

    print(f"\n→ Writing {pulled} rows to {csv_path} ...")

    with csv_path.open(mode="w", encoding="utf-8", newline="") as f:
        # Write a human-readable comment header before the CSV data
        f.write(f"# Data EF Public Datasets export\n")
        f.write(f"# fetched_at : {fetched_at}\n")
        f.write(f"# api_total  : {api_total}\n")
        f.write(f"# pulled     : {pulled}\n")
        f.write(f"# source     : {url}\n")

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for ds in datasets:
            writer.writerow(flatten_dataset(ds))

    print(f"✅ Export complete → {csv_path}")


if __name__ == "__main__":
    main()
