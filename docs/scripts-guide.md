# Scripts Guide

All scripts live in `scripts/` and are run with `uv run`:

```bash
uv run scripts/<script_name>.py
```

---

## `public_datasets.py`

Exercises every Public Datasets API endpoint in sequence and pretty-prints the JSON results.

**What it calls:**

| Step | Endpoint |
|---|---|
| 1 | `GET /api/v1/public-datasets/home` |
| 2 | `GET /api/v1/public-datasets/count-data` |
| 3 | `GET /api/v1/public-datasets/filter-options` |
| 4 | `GET /api/v1/public-datasets/auto-suggest?keyword=budget` |
| 5 | `GET /api/v1/public-datasets?page=1&page_size=5` |
| 6 | `GET /api/v1/public-datasets/seo` |
| 7 | `GET /api/v1/public-datasets/{first_id}` |
| 8 | `GET /api/v1/public-datasets/{first_id}/file` |
| 9 | `GET /api/v1/public-datasets/{first_id}/json?page=1&page_size=5` |

```bash
uv run scripts/public_datasets.py
```

**Sample output (truncated):**

```
============================================================
  GET /api/v1/public-datasets/count-data
============================================================
{
  "datasets": 142,
  "datasources": 87
}

============================================================
  GET /api/v1/public-datasets/filter-options
============================================================
{
  "categories": [
    {"id": 1, "slug": "finance", "name": "Finance", "count": 38},
    {"id": 2, "slug": "agriculture", "name": "Agriculture", "count": 22}
  ],
  "organizations": [...],
  "data_formats": [
    {"id": null, "slug": "CSV", "name": "CSV", "count": 98}
  ]
}
```

---

## `events_news.py`

Demonstrates the Events and News endpoints.

**What it calls:**

| Step | Endpoint |
|---|---|
| 1 | `GET /api/v1/events-and-news` (page 1, size 5) |
| 2 | `GET /api/v1/events-and-news?category=blog` (page 1, size 5) |
| 3 | `GET /api/v1/events-and-news/{first_slug}` (first article detail) |

```bash
uv run scripts/events_news.py
```

---

## `realtime_api.py`

Exercises all six Realtime API endpoints.

**What it calls:**

| Step | Endpoint |
|---|---|
| 1 | `GET /api/v1/realtime-api/exchange-rate` (all currencies) |
| 2 | `GET /api/v1/realtime-api/exchange-rate?currency_id=USD` |
| 3 | `GET /api/v1/realtime-api/weather` (all provinces) |
| 4 | `GET /api/v1/realtime-api/weather?province=Phnom+Penh` |
| 5 | `GET /api/v1/realtime-api/aqi?province=Phnom+Penh` |
| 6 | `GET /api/v1/realtime-api/uv?province=Phnom+Penh` |
| 7 | `GET /api/v1/realtime-api/csx-index` |
| 8 | `GET /api/v1/realtime-api/csx-summary` |

```bash
uv run scripts/realtime_api.py
```

**Sample CSX index output:**

```json
{
  "data": {
    "id": 1001,
    "created_at": "2024-03-20T09:30:00",
    "date": "2024-03-20",
    "value": 493.2,
    "change": -2.1,
    "change_percent": -0.42,
    "change_up_down": "down",
    "trading_volume": "1,234,567",
    "trading_value": "2,891,234",
    "market_cap": 15234567890.0
  }
}
```

---

## `contact.py`

Demonstrates the contact form endpoint.  
**Edit the placeholder values before running.**

```bash
uv run scripts/contact.py
```

---

## `explore_filters.py`

Fetches `/filter-options` and `/count-data` to show how datasets are distributed across categories, organisations, and formats. Prints a strategy recommendation.

```bash
uv run scripts/explore_filters.py
```

**Sample output:**

```
Total: 142 datasets  /  87 datasources

=== Categories (14) ===
  finance                          38 datasets   [Finance]
  agriculture                      22 datasets   [Agriculture]
  education                        18 datasets   [Education]
  environment                      12 datasets   [Environment]
  ...

=== Organisations (11) ===
  ministry-of-finance              55 datasets   [Ministry of Finance]
  national-bank-of-cambodia        14 datasets   [National Bank of Cambodia]
  ...

=== Data Formats (5) ===
  CSV                              98 datasets
  XLSX                             44 datasets
  JSON                             12 datasets
  PDF                               8 datasets
  ...

============================================================
  RECOMMENDATION
============================================================

To pull ALL datasets metadata without duplicates use simple pagination:

    GET /api/v1/public-datasets?page=1&page_size=10000

This is a single request that returns every dataset ...
```

---

## `fetch_all_datasets.py`

Bulk-harvests ALL dataset metadata and file-download URLs.  
Outputs `metadata.json` and `data_index.json` to a configurable directory.

```bash
uv run scripts/fetch_all_datasets.py
```

### Configuration (environment variables)

| Variable | Default | Description |
|---|---|---|
| `DATA_DIR` | `output/` | Output directory |
| `MAX_DATASETS` | *(unlimited)* | Cap on number of datasets to process |
| `FETCH_DATA` | `true` | Whether to collect file URLs / row counts |
| `VERBOSE` | `true` | Print per-dataset progress |

### Examples

```bash
# Standard run — full harvest into output/
uv run scripts/fetch_all_datasets.py

# Save to artifacts/ (as committed in this repo)
DATA_DIR=artifacts uv run scripts/fetch_all_datasets.py

# Quick test — first 20 datasets only, metadata only
MAX_DATASETS=20 FETCH_DATA=false uv run scripts/fetch_all_datasets.py

# Silent, custom output path
VERBOSE=false DATA_DIR=/tmp/ef-data uv run scripts/fetch_all_datasets.py
```

### Output files

| File | Description |
|---|---|
| `metadata.json` | Array of every dataset metadata record |
| `data_index.json` | Per-dataset file URLs + row counts |

See [Data Schemas](data-schemas.md) for the full structure of each file.

### Sample terminal output

```
[metadata] Total datasets reported: 142
  → page 1 (page_size=10000) …
     collected 142 / 142
[metadata] Collected 142 dataset records.
  ✓ saved output/metadata.json

[data] Collecting file info for 142 datasets …
  [1/142] budget-law-2024
  [2/142] trade-statistics-2023
  ...
  ✓ saved output/data_index.json

============================================================
  SUMMARY
============================================================
  Total datasets harvested : 142
  Have downloadable files  : 118  (247 files total)
  JSON-only (no file)      :  20
  No data available        :   4

  Output written to: /path/to/output/
    metadata.json   — 142 records
    data_index.json — 142 records
============================================================
```
