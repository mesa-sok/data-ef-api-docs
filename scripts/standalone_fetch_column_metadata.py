#!/usr/bin/env python3
"""
standalone_fetch_column_metadata.py

A strictly standalone script — zero external dependencies, no DataEFClient,
no httpx, no pydantic. Only Python standard library modules are used.

  Standard library used:
    - urllib.request  → makes HTTP GET requests
    - urllib.error    → catches HTTP / network errors
    - ssl             → disables SSL verification (matches project convention)
    - json            → parses and writes JSON
    - time            → sleep between requests and on retry
    - pathlib.Path    → file I/O

What this script does, step by step:
  1. Reads artifacts/metadata.json (produced by fetch_all_datasets.py / standalone_export_datasets.py).
  2. Filters to only CSV-format datasets.
  3. Loads any existing artifacts/column_metadata.json — skips IDs already present
     (safe to interrupt and re-run; progress is never lost).
  4. For each remaining dataset, calls:
       GET https://data.mef.gov.kh/api/v1/public-datasets/{id}
     and extracts the nested "column_data" object.
  5. On any HTTP or network error, waits 10 seconds and retries once before
     recording the failure and moving on.
  6. After every successful fetch the output file is rewritten as a checkpoint,
     so a keyboard-interrupt loses at most one record.

Output:
    artifacts/column_metadata.json  — JSON array of:
    {
      "id":             "pd_...",
      "name":           "...",
      "format":         "CSV",
      "column_data_id": 1268 | null,
      "columns": [
        {
          "title":       "partner_country_en",
          "type":        "Text",
          "format":      null,
          "description": "...",
          "reference_id":    null,
          "reference_field": null
        },
        ...
      ] | null
    }

Usage:
    python3 scripts/standalone_fetch_column_metadata.py

Options (env-vars):
    DATA_DIR    destination / source folder  (default: artifacts/)
    VERBOSE     print per-dataset progress   (default: true)

Resume / Checkpoint:
    The script is safe to interrupt and re-run. On startup it reads any
    existing column_metadata.json and skips IDs that already have a successful
    result (columns or a clean "no data" response). IDs that previously
    failed with an error are automatically re-attempted.
"""

import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


# ── Configuration ──────────────────────────────────────────────────────────────

API_BASE_URL = "https://data.mef.gov.kh"
DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parent.parent / "artifacts"))
VERBOSE: bool = os.getenv("VERBOSE", "true").lower() != "false"
RETRY_WAIT_SECS = 10
REQUEST_DELAY_SECS = 0.1


# ── Helpers ────────────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    if VERBOSE:
        print(msg)


def _ssl_ctx() -> ssl.SSLContext:
    """Create an SSL context with certificate verification disabled."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def fetch_json(url: str) -> dict:
    """GET *url* and return the parsed JSON body. Raises on HTTP errors."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "standalone-dataef-column-fetcher/1.0"},
    )
    with urllib.request.urlopen(req, context=_ssl_ctx()) as resp:
        return json.loads(resp.read().decode("utf-8"))


def save_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"  ✓ saved {path}")


# ── Core fetch with retry ──────────────────────────────────────────────────────

def fetch_column_data(ds_id: str) -> tuple[list | None, str | None]:
    """
    Fetch column definitions for one dataset.

    Returns:
        (columns, error_msg)  — one of the two will be None.
    """
    url = f"{API_BASE_URL}/api/v1/public-datasets/{ds_id}"

    for attempt in range(2):
        try:
            body = fetch_json(url)
            detail = body.get("data", body) if isinstance(body, dict) else {}
            col_data = detail.get("column_data")
            if col_data and col_data.get("data"):
                return col_data["data"], None
            return None, None  # endpoint ok but no column_data present
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            if attempt == 0:
                log(f"     → ERROR (attempt 1): {exc} — retrying in {RETRY_WAIT_SECS}s …")
                time.sleep(RETRY_WAIT_SECS)
            else:
                return None, str(exc)

    return None, "unknown error"  # unreachable, but satisfies type checkers


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    metadata_path = DATA_DIR / "metadata.json"
    if not metadata_path.exists():
        print(
            f"ERROR: {metadata_path} not found.\n"
            "Run standalone_export_datasets.py or fetch_all_datasets.py first.",
            file=sys.stderr,
        )
        sys.exit(1)

    all_metadata: list[dict] = json.loads(metadata_path.read_text(encoding="utf-8"))

    # Filter to CSV datasets only
    csv_datasets = [ds for ds in all_metadata if ds.get("format", "").upper() == "CSV"]
    log(f"\n[column_metadata] Found {len(csv_datasets)} CSV datasets in metadata.json")

    # ── Resume: load already-fetched checkpoint ────────────────────────────────
    output_path = DATA_DIR / "column_metadata.json"
    already_fetched: dict[str, dict] = {}
    if output_path.exists():
        existing: list[dict] = json.loads(output_path.read_text(encoding="utf-8"))
        already_fetched = {e["id"]: e for e in existing if e.get("id")}
        log(
            f"[column_metadata] Resuming — {len(already_fetched)} IDs already fetched, "
            "skipping them."
        )

    # Pre-seed counters from already-fetched entries
    success = sum(1 for e in already_fetched.values() if e.get("columns"))
    no_column_data = sum(1 for e in already_fetched.values() if not e.get("columns") and not e.get("error"))
    errors = sum(1 for e in already_fetched.values() if e.get("error"))

    # New results fetched this run (we merge into already_fetched as we go)
    fetched_this_run = 0

    for i, ds in enumerate(csv_datasets, start=1):
        ds_id = ds.get("id")
        ds_name = ds.get("name", "")
        col_data_id = ds.get("column_data_id")

        # ── Skip if already fetched (only if successful) ───────────────
        if ds_id in already_fetched and not already_fetched[ds_id].get("error"):
            log(f"  [{i}/{len(csv_datasets)}] {ds_id} — SKIP (already fetched)")
            continue

        log(f"  [{i}/{len(csv_datasets)}] {ds_id} | column_data_id={col_data_id}")

        columns, error_msg = fetch_column_data(ds_id)

        entry: dict = {
            "id": ds_id,
            "name": ds_name,
            "format": ds.get("format"),
            "column_data_id": col_data_id,
            "columns": columns,
        }

        if error_msg:
            entry["error"] = error_msg
            errors += 1
            log(f"     → ERROR (attempt 2): {error_msg} — giving up")
        elif columns:
            success += 1
            log(f"     → {len(columns)} column(s) found")
        else:
            no_column_data += 1
            log("     → no column_data in response")

        # Upsert into checkpoint dict and persist immediately
        already_fetched[ds_id] = entry
        fetched_this_run += 1
        save_json(output_path, list(already_fetched.values()))

        time.sleep(REQUEST_DELAY_SECS)

    # Final save (also covers the case where nothing new was fetched)
    save_json(output_path, list(already_fetched.values()))

    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  CSV datasets total       : {len(csv_datasets)}")
    print(f"  Fetched this run         : {fetched_this_run}")
    print(f"  With column definitions  : {success}")
    print(f"  No column_data returned  : {no_column_data}")
    print(f"  Errors                   : {errors}")
    print(f"\n  Output: {output_path.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
