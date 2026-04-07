# Artifacts

This directory contains pre-harvested data from the Data EF Public API.

> **Note:** These files are representative samples demonstrating the complete
> schema. To refresh with live data run:
>
> ```bash
> DATA_DIR=artifacts uv run scripts/fetch_all_datasets.py
> ```

## Files

| File | Description |
|---|---|
| [`metadata.json`](metadata.json) | Array of dataset metadata records (id, slug, title, category, organisation, tags, license, timestamps) |
| [`data_index.json`](data_index.json) | Per-dataset data availability index (file download URLs or JSON row counts) |

## Quick stats (sample data)

| Metric | Count |
|---|---|
| Total datasets | 10 |
| Datasets with downloadable files | 7 (14 files total) |
| Datasets accessible via JSON preview only | 3 |
| Datasets with no data | 0 |

## Regenerating

```bash
# Full harvest (metadata + file URLs)
DATA_DIR=artifacts uv run scripts/fetch_all_datasets.py

# Metadata only
DATA_DIR=artifacts FETCH_DATA=false uv run scripts/fetch_all_datasets.py
```

See [docs/data-schemas.md](../docs/data-schemas.md) for the full schema reference.
