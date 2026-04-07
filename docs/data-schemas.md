# Data Schemas — `artifacts/` Files

The `artifacts/` directory contains the output of running `fetch_all_datasets.py`
against the live API. Two JSON files are produced:

| File | Description |
|---|---|
| [`metadata.json`](#metadatajson) | All dataset metadata records |
| [`data_index.json`](#data_indexjson) | Per-dataset file URLs and row counts |

---

## `metadata.json`

A JSON **array** of dataset metadata objects — one entry per dataset.

### Example record

```json
{
  "id": "budget-law-2024",
  "slug": "budget-law-2024",
  "title_en": "Budget Law 2024",
  "title_kh": "ច្បាប់ហិរញ្ញប្បទាន ២០២៤",
  "description_en": "Annual budget law published by the Ministry of Economy and Finance.",
  "description_kh": "...",
  "category": {
    "id": 1,
    "slug": "finance",
    "name_en": "Finance",
    "name_kh": "ហិរញ្ញវត្ថុ"
  },
  "organization": {
    "id": 3,
    "slug": "ministry-of-finance",
    "name_en": "Ministry of Finance",
    "name_kh": "ក្រសួងសេដ្ឋកិច្ច និងហិរញ្ញវត្ថុ"
  },
  "tags": ["budget", "law", "finance"],
  "license": "CC-BY-4.0",
  "created_at": "2024-01-15T08:00:00Z",
  "updated_at": "2024-03-20T12:30:00Z"
}
```

### Field reference

| Field | Type | Notes |
|---|---|---|
| `id` | `string \| number \| null` | Unique dataset identifier (numeric ID or slug) |
| `slug` | `string \| null` | URL-friendly identifier; used in all per-dataset API calls |
| `title_en` | `string \| null` | Dataset title in English |
| `title_kh` | `string \| null` | Dataset title in Khmer |
| `description_en` | `string \| null` | Long description in English |
| `description_kh` | `string \| null` | Long description in Khmer |
| `category` | `object \| null` | Category metadata — see below |
| `organization` | `object \| null` | Organisation metadata — see below |
| `tags` | `array \| null` | Free-form tag strings |
| `license` | `string \| null` | License identifier (e.g. `"CC-BY-4.0"`) |
| `created_at` | `string \| null` | ISO 8601 creation timestamp |
| `updated_at` | `string \| null` | ISO 8601 last-update timestamp |
| *(extra fields)* | `any` | The API may return additional fields not listed here |

#### `category` object

| Field | Type |
|---|---|
| `id` | `number` |
| `slug` | `string` |
| `name_en` | `string` |
| `name_kh` | `string` |

#### `organization` object

| Field | Type |
|---|---|
| `id` | `number` |
| `slug` | `string` |
| `name_en` | `string` |
| `name_kh` | `string` |

### Reading with Python

```python
import json
from pathlib import Path

metadata = json.loads(Path("artifacts/metadata.json").read_text())

print(f"Total datasets: {len(metadata)}")

# Find all finance datasets
finance = [ds for ds in metadata if ds.get("category", {}).get("slug") == "finance"]

# Group by organization
from collections import defaultdict
by_org: dict = defaultdict(list)
for ds in metadata:
    org = ds.get("organization") or {}
    by_org[org.get("slug", "unknown")].append(ds.get("slug"))
```

---

## `data_index.json`

A JSON **array** of per-dataset data-availability records — one entry per dataset.

### Example records

**Dataset with downloadable files:**

```json
{
  "id": "budget-law-2024",
  "method": "file",
  "files": [
    {
      "name": "budget_2024.csv",
      "format": "CSV",
      "url": "https://data.mef.gov.kh/media/datasets/budget_2024.csv",
      "size": 204800
    },
    {
      "name": "budget_2024.xlsx",
      "format": "XLSX",
      "url": "https://data.mef.gov.kh/media/datasets/budget_2024.xlsx",
      "size": 389120
    }
  ],
  "json_row_count": null,
  "title_en": "Budget Law 2024",
  "title_kh": "ច្បាប់ហិរញ្ញប្បទាន ២០២៤",
  "category": {"slug": "finance", "name_en": "Finance"},
  "organization": {"slug": "ministry-of-finance", "name_en": "Ministry of Finance"}
}
```

**Dataset accessible only via JSON preview:**

```json
{
  "id": "province-statistics-2023",
  "method": "json",
  "files": [],
  "json_row_count": 1250,
  "title_en": "Province Statistics 2023",
  "title_kh": "...",
  "category": {"slug": "demographics"},
  "organization": {"slug": "nis"}
}
```

**Dataset with no accessible data:**

```json
{
  "id": "restricted-dataset",
  "method": "none",
  "files": [],
  "json_row_count": null,
  "title_en": "Restricted Dataset",
  "title_kh": null,
  "category": null,
  "organization": null
}
```

### Field reference

| Field | Type | Description |
|---|---|---|
| `id` | `string \| number` | Dataset identifier (same as `metadata.json`) |
| `method` | `"file" \| "json" \| "none"` | How data can be accessed — see [Methods](#access-methods) |
| `files` | `array` | List of downloadable file entries (non-empty only when `method == "file"`) |
| `json_row_count` | `number \| null` | Total rows available via `/json` (non-null only when `method == "json"`) |
| `title_en` | `string \| null` | Title in English (copied from metadata) |
| `title_kh` | `string \| null` | Title in Khmer (copied from metadata) |
| `category` | `object \| null` | Category object (copied from metadata) |
| `organization` | `object \| null` | Organisation object (copied from metadata) |

#### `files[]` entry fields

| Field | Type | Description |
|---|---|---|
| `name` | `string \| null` | Filename, e.g. `"budget_2024.csv"` |
| `format` | `string \| null` | Format string: `"CSV"`, `"XLSX"`, `"JSON"`, `"PDF"`, etc. |
| `url` | `string \| null` | Direct download URL |
| `size` | `number \| string \| null` | File size in bytes (may be a formatted string) |

### Access methods

| `method` value | Meaning | How to get the data |
|---|---|---|
| `"file"` | One or more downloadable files are available | Download directly from `files[].url` |
| `"json"` | No file, but row data is accessible via the JSON preview endpoint | Use `client.get_public_dataset_json()` with pagination |
| `"none"` | Data is not currently accessible (API error on both endpoints) | Skip or retry later |

### Querying with Python

```python
import json
from pathlib import Path

index = json.loads(Path("artifacts/data_index.json").read_text())

# Stats
file_ds   = [e for e in index if e["method"] == "file"]
json_ds   = [e for e in index if e["method"] == "json"]
none_ds   = [e for e in index if e["method"] == "none"]
all_files = [f for e in file_ds for f in e["files"]]

print(f"File-based:  {len(file_ds)} datasets, {len(all_files)} files")
print(f"JSON-based:  {len(json_ds)} datasets, "
      f"{sum(e['json_row_count'] or 0 for e in json_ds)} rows total")
print(f"No data:     {len(none_ds)} datasets")

# All CSV download URLs
csv_urls = [
    f["url"] for e in file_ds
    for f in e["files"]
    if (f.get("format") or "").upper() == "CSV"
]

# Datasets with > 1000 JSON rows
large = [e for e in json_ds if (e["json_row_count"] or 0) > 1000]
```

### Downloading all files (shell)

```bash
# Extract all file URLs and download with 4 parallel workers
jq -r '.[] | select(.method=="file") | .files[] | .url' artifacts/data_index.json \
  | xargs -P 4 -I{} wget -q --no-clobber -P artifacts/files/ {}
```

---

## Regenerating the artifacts

```bash
# Full harvest (metadata + file URLs)
DATA_DIR=artifacts uv run scripts/fetch_all_datasets.py

# Metadata only (faster, skips file-URL collection)
DATA_DIR=artifacts FETCH_DATA=false uv run scripts/fetch_all_datasets.py
```
