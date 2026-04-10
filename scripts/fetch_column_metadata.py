#!/usr/bin/env python3
"""
Script: fetch_column_metadata.py

Fetches the full column_data definitions for every CSV dataset by calling
GET /api/v1/public-datasets/{id} and extracting the nested `column_data` field.

Output
------
  artifacts/column_metadata.json — list of records:
    {
      "id": "pd_...",
      "name": "...",
      "column_data_id": 1268 | null,
      "columns": [{"title": ..., "type": ..., "description": ...}, ...] | null
    }

Usage
-----
    uv run scripts/fetch_column_metadata.py

Options (env-vars):
    DATA_DIR      destination folder  (default: artifacts/)
    VERBOSE       print progress      (default: true)

Resume / Checkpoint
-------------------
  The script is safe to interrupt and re-run.  On startup it reads any
  existing ``column_metadata.json`` and skips IDs that already have a
  successful result (columns or a clean "no data" response). IDs that
  previously failed with an error are automatically re-attempted.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from data_ef_api import DataEFClient

DATA_DIR: Path = Path(os.getenv("DATA_DIR", ROOT / "artifacts"))
VERBOSE: bool = os.getenv("VERBOSE", "true").lower() != "false"


def log(msg: str) -> None:
    if VERBOSE:
        print(msg)


def save_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"  ✓ saved {path}")


def main() -> None:
    metadata_path = DATA_DIR / "metadata.json"
    if not metadata_path.exists():
        print(f"ERROR: {metadata_path} not found — run fetch_all_datasets.py first.", file=sys.stderr)
        sys.exit(1)

    all_metadata: list[dict] = json.loads(metadata_path.read_text(encoding="utf-8"))

    # Filter to only CSV datasets with a column_data_id (those likely have column defs)
    csv_datasets = [
        ds for ds in all_metadata
        if ds.get("format", "").upper() == "CSV"
    ]
    log(f"\n[column_metadata] Found {len(csv_datasets)} CSV datasets in metadata.json")

    results: list[dict] = []
    success = 0
    no_column_data = 0
    errors = 0

    # ── Resume: load already-fetched results ──────────────────────────────────
    output_path = DATA_DIR / "column_metadata.json"
    already_fetched: dict[str, dict] = {}  # id → existing entry
    if output_path.exists():
        existing: list[dict] = json.loads(output_path.read_text(encoding="utf-8"))
        already_fetched = {e["id"]: e for e in existing if e.get("id")}
        log(f"[column_metadata] Resuming — {len(already_fetched)} IDs already fetched, skipping them.")
        # Carry over stats for already-completed entries
        for e in already_fetched.values():
            if e.get("columns"):
                success += 1
            elif e.get("error"):
                errors += 1
            else:
                no_column_data += 1

    with DataEFClient(verify=False) as client:
        for i, ds in enumerate(csv_datasets, start=1):
            ds_id = ds.get("id")
            ds_name = ds.get("name", "")
            col_data_id = ds.get("column_data_id")

            # ── Skip already-fetched (only if successful) ──────────────────
            if ds_id in already_fetched and not already_fetched[ds_id].get("error"):
                log(f"  [{i}/{len(csv_datasets)}] {ds_id} — SKIP (already fetched)")
                results.append(already_fetched[ds_id])
                continue

            log(f"  [{i}/{len(csv_datasets)}] {ds_id} | column_data_id={col_data_id}")

            entry: dict = {
                "id": ds_id,
                "name": ds_name,
                "format": ds.get("format"),
                "column_data_id": col_data_id,
                "columns": None,
            }

            for attempt in range(2):
                try:
                    raw = client._get(f"/api/v1/public-datasets/{ds_id}")
                    detail = raw.get("data", raw) if isinstance(raw, dict) else {}
                    col_data = detail.get("column_data")
                    if col_data and col_data.get("data"):
                        entry["columns"] = col_data["data"]
                        entry["column_data_id"] = col_data.get("column_data_id", col_data_id)
                        success += 1
                        log(f"     → {len(entry['columns'])} column(s) found")
                    else:
                        no_column_data += 1
                        log(f"     → no column_data in response")
                    break  # success — exit retry loop
                except Exception as exc:  # noqa: BLE001
                    if attempt == 0:
                        log(f"     → ERROR (attempt 1): {exc} — retrying in 10s …")
                        time.sleep(10)
                    else:
                        errors += 1
                        entry["error"] = str(exc)
                        log(f"     → ERROR (attempt 2): {exc} — giving up")

            results.append(entry)

            # Checkpoint: save after each successful fetch so progress is
            # never lost if the script is interrupted
            save_json(output_path, results + list(already_fetched.values()))

            # Small delay to avoid hammering the API
            time.sleep(0.1)

    # Final save with all results (already-fetched merged with new)
    merged = {e["id"]: e for e in results}
    merged.update(already_fetched)  # already_fetched only has skipped entries at this point
    save_json(output_path, list(merged.values()))

    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  CSV datasets processed   : {len(csv_datasets)}")
    print(f"  With column definitions  : {success}")
    print(f"  No column_data returned  : {no_column_data}")
    print(f"  Errors                   : {errors}")
    print(f"\n  Output: {DATA_DIR.resolve()}/column_metadata.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
