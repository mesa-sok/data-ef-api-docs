# Data EF Public API — Documentation

> Python client library and runnable scripts for the **[Data EF Public API](https://data.mef.gov.kh/api/v1/)** — Cambodia's open-data platform maintained by the Ministry of Economy and Finance.

---

## Table of Contents

| Document | Description |
|---|---|
| **[Client Reference](client-reference.md)** | All 20 `DataEFClient` methods with signatures, parameters, and examples |
| **[Models Reference](models-reference.md)** | Every Pydantic v2 request/response model with typed field tables |
| **[Scripts Guide](scripts-guide.md)** | How to run each helper script and what output to expect |
| **[Bulk Harvesting Guide](bulk-harvesting.md)** | Strategy for pulling all dataset metadata + row data efficiently |
| **[Data Schemas](data-schemas.md)** | Schema reference for `artifacts/metadata.json` and `artifacts/data_index.json` |

---

## Project Overview

```
data-ef-api-docs/
├── src/data_ef_api/          # Installable Python package
│   ├── client.py             # DataEFClient — synchronous httpx-based client
│   ├── constants.py          # BASE_URL, PROVINCES, CURRENCY_IDS, sort options
│   └── models/               # Pydantic v2 response models
│       ├── public_datasets.py
│       ├── realtime.py
│       ├── events_news.py
│       ├── contact.py
│       ├── common.py
│       ├── enums.py
│       └── errors.py
├── scripts/                  # Runnable demo + harvest scripts
│   ├── public_datasets.py    # Exercise all dataset endpoints
│   ├── events_news.py        # Events & news endpoints
│   ├── realtime_api.py       # Exchange rate, weather, AQI, UV, CSX
│   ├── contact.py            # Contact form endpoint
│   ├── explore_filters.py    # Catalogue breakdown + strategy guide
│   └── fetch_all_datasets.py # Bulk metadata + file-URL harvester
├── docs/                     # This documentation
├── artifacts/                # Harvested data (metadata.json, data_index.json)
└── tests/                    # 38 pytest-httpx mock tests
```

---

## Requirements

| Tool | Version |
|------|---------|
| Python | ≥ 3.12 |
| [uv](https://github.com/astral-sh/uv) | ≥ 0.4 |

---

## Installation

```bash
# 1. Clone
git clone https://github.com/mesa-sok/data-ef-api-docs.git
cd data-ef-api-docs

# 2. Install dependencies (including dev tools)
uv sync --all-groups
```

---

## Quick Start

```python
from data_ef_api import DataEFClient

with DataEFClient() as client:
    # Total counts
    counts = client.get_count_data()
    print(f"{counts.datasets} datasets, {counts.datasources} datasources")

    # List 10 newest datasets
    page = client.get_public_datasets(sort_by="NEWEST", page_size=10)
    for ds in (page.data.results or []):
        print(ds.get("slug"), "—", ds.get("title_en"))

    # Live exchange rate
    usd = client.get_exchange_rate("USD")
    print(usd.data.data)  # {"buy": ..., "sell": ...}
```

---

## API Base URL

```
https://data.mef.gov.kh
```

All paths are relative to this base. The client accepts a custom `base_url` argument for testing against other environments.

---

## Running Tests

```bash
uv run pytest           # all 38 tests (no network needed)
uv run pytest -v        # verbose
uv run ruff check src/ tests/
```

Tests use `pytest-httpx` to mock every HTTP call — **no network access required**.
