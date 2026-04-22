# Bulk Data Harvesting Guide

This guide explains how to pull **all** dataset metadata and row data from the
Data EF Public API as efficiently as possible.

---

## Strategy Summary

> **TL;DR — use plain pagination with `page_size=10000`.**

| Approach | API requests | Duplicate risk | Use when |
|---|---|---|---|
| **Plain pagination** `page_size=10000` | 1 (usually) | ✅ None | Full catalogue harvest ← **recommended** |
| Category filter | 1 per category | ⚠️ Possible | Grouped-by-category views |
| Organisation filter | 1 per org | ⚠️ Possible | Grouped-by-org views |
| Format filter | 1 per format | ⚠️ Possible | Format-specific pipelines |
| Full-text search | 1 per query | ⚠️ Possible | Targeted keyword queries |

Category, organisation, and format filters are useful for *scoped* access but
can cause duplicates when a dataset belongs to multiple categories or organisations.
Plain pagination is always complete and duplicate-free.

---

## Step 1 — Explore the catalogue

Before harvesting, understand the data distribution:

```bash
uv run scripts/explore/explore_filters.py
```

This calls `/count-data` and `/filter-options` and prints a breakdown:

```
Total: 142 datasets  /  87 datasources

=== Categories (14) ===
  finance              38 datasets   [Finance]
  agriculture          22 datasets   [Agriculture]
  education            18 datasets   [Education]
  ...

=== Organisations (11) ===
  ministry-of-finance  55 datasets   [Ministry of Finance]
  ...

=== Data Formats (5) ===
  CSV                  98 datasets
  XLSX                 44 datasets
  ...
```

Use these **slug values** when you need to filter later.

---

## Step 2 — Harvest all metadata

```bash
DATA_DIR=artifacts uv run scripts/harvest/fetch_all_datasets.py
```

Internally this does:

```python
# Single request covers the full catalogue
resp = client.get_public_datasets(sort_by="NEWEST", page=1, page_size=10000)
records = resp.data.results   # complete list
```

If the catalogue ever exceeds 10 000 entries the script automatically pages
through using `total_pages` from the response envelope.

Output: `artifacts/metadata.json`

---

## Step 3 — Collect file URLs / row data

For every dataset the script tries two methods in order:

### Method A — Downloadable file (preferred)

```
GET /api/v1/public-datasets/{id}/file
```

Returns one or more files (CSV, XLSX, JSON, PDF, …).  
**This is the fastest and most complete way to get data** — the original file
is returned directly and requires only one request per dataset.

Example response:

```json
{
  "files": [
    {
      "name": "budget_2024.csv",
      "format": "CSV",
      "url": "https://data.mef.gov.kh/media/datasets/budget_2024.csv",
      "size": 204800
    }
  ]
}
```

### Method B — JSON preview (fallback)

```
GET /api/v1/public-datasets/{id}/json?page=1&page_size=200
```

Used only when `/file` returns no entries.  
Returns paginated rows (max 200 per page).

To download all rows:

```python
import math
from data_ef_api import DataEFClient

PAGE = 200

with DataEFClient() as client:
    first = client.get_public_dataset_json("dataset-slug", page=1, page_size=PAGE)
    total = first.data.total or 0
    rows  = list(first.data.results or [])

    for p in range(2, math.ceil(total / PAGE) + 1):
        data = client.get_public_dataset_json("dataset-slug", page=p, page_size=PAGE)
        rows.extend(data.data.results or [])

print(f"Downloaded {len(rows)} / {total} rows")
```

---

## Step 4 — Download files in bulk

After running `fetch_all_datasets.py`, download every file from `data_index.json`:

```bash
# Using jq + wget (4 parallel downloads)
jq -r '.[] | select(.method=="file") | .files[] | .url' artifacts/data_index.json \
  | xargs -P 4 -I{} wget -q -P artifacts/files/ {}
```

Or with Python:

```python
import json, urllib.request
from pathlib import Path

index = json.loads(Path("artifacts/data_index.json").read_text())
out_dir = Path("artifacts/files")
out_dir.mkdir(exist_ok=True)

for entry in index:
    for f in entry.get("files", []):
        url = f["url"]
        fname = out_dir / f["name"]
        print(f"Downloading {url}")
        urllib.request.urlretrieve(url, fname)
```

---

## Using filters for targeted queries

Even though plain pagination is best for a full harvest, filters are useful for
targeted queries:

```python
from data_ef_api import DataEFClient

with DataEFClient() as client:
    # All finance datasets
    finance = client.get_public_datasets(categories="finance", page_size=10000)

    # All datasets from the Ministry of Finance
    mof = client.get_public_datasets(
        organizations="ministry-of-finance", page_size=10000
    )

    # CSV-only datasets
    csvs = client.get_public_datasets(data_formats="CSV", page_size=10000)

    # Combine filters: finance CSVs, newest first
    finance_csvs = client.get_public_datasets(
        categories="finance",
        data_formats="CSV",
        sort_by="NEWEST",
        page_size=10000,
    )

    # Full-text search
    gdp = client.get_public_datasets(keyword="GDP growth", page_size=50)
```

> **Note:** Slug values for `categories` and `organizations` come from
> `/filter-options`. Run `scripts/explore/explore_filters.py` to list all available slugs.

---

## Keeping data up to date

The `updated_at` field in each metadata record lets you detect stale data:

```python
import json
from datetime import datetime, timezone
from pathlib import Path

CUTOFF = datetime(2024, 1, 1, tzinfo=timezone.utc)
metadata = json.loads(Path("artifacts/metadata.json").read_text())

recently_updated = [
    ds for ds in metadata
    if ds.get("updated_at") and datetime.fromisoformat(ds["updated_at"]) > CUTOFF
]
print(f"{len(recently_updated)} datasets updated since {CUTOFF.date()}")
```

For incremental updates, use `sort_by="RECENTLY_UPDATED"` and only process
datasets whose `updated_at` is newer than your last harvest timestamp.

---

## Environment variables for `fetch_all_datasets.py`

| Variable | Default | Description |
|---|---|---|
| `DATA_DIR` | `output/` | Destination directory |
| `MAX_DATASETS` | *(none)* | Limit number of processed datasets |
| `FETCH_DATA` | `true` | Collect file URLs / row counts |
| `VERBOSE` | `true` | Print per-dataset progress |

```bash
# Full harvest into artifacts/
DATA_DIR=artifacts uv run scripts/harvest/fetch_all_datasets.py

# Metadata only (skip file-URL collection), quiet
FETCH_DATA=false VERBOSE=false DATA_DIR=artifacts uv run scripts/harvest/fetch_all_datasets.py

# Test with first 10 datasets
MAX_DATASETS=10 DATA_DIR=/tmp/test uv run scripts/harvest/fetch_all_datasets.py
```
