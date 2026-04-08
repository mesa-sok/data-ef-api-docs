# Data EF Public API — Scripts & Documentation

Python client library and runnable scripts for the **[Data EF Public API](https://data.mef.gov.kh/api/v1/)** provided by the Ministry of Economy and Finance of Cambodia.

---

## Table of Contents

1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Project Structure](#project-structure)
4. [Quick Start](#quick-start)
5. [API Reference](#api-reference)
   - [Public Datasets](#public-datasets)
   - [Events and News](#events-and-news)
   - [Superset Dashboard Token](#superset-dashboard-token)
   - [Contact](#contact)
   - [Realtime API – Exchange Rate](#realtime-api--exchange-rate)
   - [Realtime API – Weather](#realtime-api--weather)
   - [Realtime API – Air Quality Index](#realtime-api--air-quality-index)
   - [Realtime API – UV Index](#realtime-api--uv-index)
   - [Realtime API – CSX Index](#realtime-api--csx-index)
   - [Realtime API – CSX Summary](#realtime-api--csx-summary)
6. [Pydantic Models](#pydantic-models)
7. [Scripts](#scripts)
8. [Bulk Data Harvesting](#bulk-data-harvesting)
9. [Running Tests](#running-tests)
10. [Enumerations & Constants](#enumerations--constants)

---

## Requirements

| Tool | Version |
|------|---------|
| Python | ≥ 3.12 |
| [uv](https://github.com/astral-sh/uv) | ≥ 0.4 |

---

## Installation

```bash
# Install uv (if not already installed)
pip install uv

# Clone the repository
git clone https://github.com/mesa-sok/data-ef-api-docs.git
cd data-ef-api-docs

# Install all dependencies (including dev tools)
uv sync --all-groups
```

---

## Project Structure

```
data-ef-api-docs/
├── pyproject.toml                  # uv project manifest
├── uv.lock                         # locked dependency graph
├── README.md
│
├── src/
│   └── data_ef_api/
│       ├── __init__.py             # exposes DataEFClient
│       ├── client.py               # HTTP client (all endpoints)
│       ├── constants.py            # BASE_URL, enum lists
│       └── models/
│           ├── __init__.py         # public re-exports
│           ├── enums.py            # SortByEnum, EventsAndNewsCategoryEnum …
│           ├── common.py           # ValidationError, HTTPValidationError, Pagination
│           ├── contact.py          # EmailRequest, DashboardTokenRequest
│           ├── errors.py           # per-endpoint 400/404 error bodies
│           ├── realtime.py         # Exchange Rate, Weather, AQI, UV, CSX models
│           ├── public_datasets.py  # Dataset, FilterOptions, HomeData … models
│           └── events_news.py      # EventsAndNewsDetail / List models
│
├── scripts/
│   ├── public_datasets.py          # demonstrates all dataset endpoints
│   ├── events_news.py              # demonstrates events-and-news endpoints
│   ├── realtime_api.py             # demonstrates all realtime endpoints
│   ├── contact.py                  # demonstrates the contact endpoint
│   ├── explore_filters.py          # shows category / org / format breakdown
│   └── fetch_all_datasets.py       # bulk-harvests ALL metadata + file URLs
│
└── tests/
    └── test_client.py              # 38 pytest tests (httpx mock)
```

---

## Quick Start

```python
from data_ef_api import DataEFClient

with DataEFClient() as client:
    # Count datasets and data-sources
    counts = client.get_count_data()
    print(counts.datasets, counts.datasources)

    # Search datasets
    results = client.get_public_datasets(keyword="budget", page=1, page_size=5)
    for ds in results.data.results:
        print(ds)

    # Today's USD exchange rate
    rate = client.get_exchange_rate("USD")
    print(rate.data.currency_id, rate.data.data)

    # Weather for Phnom Penh
    weather = client.get_weather("Phnom Penh")
    print(weather.data.name, weather.data.data)
```

---

## API Reference

Base URL: **`https://data.mef.gov.kh`**

All methods raise `httpx.HTTPStatusError` on 4xx / 5xx responses.

---

### Public Datasets

#### `GET /api/v1/public-datasets/home`

Returns homepage summary data.

```python
home: HomeData = client.get_home()
```

---

#### `GET /api/v1/public-datasets/count-data`

Returns total counts of datasets and data-sources.

```python
counts: CountData = client.get_count_data()
# counts.datasets    → int | None
# counts.datasources → int | None
```

---

#### `GET /api/v1/public-datasets/filter-options`

Returns available filter options (categories, organisations, data formats).

```python
opts: FilterOptions = client.get_filter_options()
# opts.categories    → list[FilterOptionItem] | None
# opts.organizations → list[FilterOptionItem] | None
# opts.data_formats  → list[FilterOptionItem] | None
```

---

#### `GET /api/v1/public-datasets/auto-suggest`

Returns search auto-suggestions.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `keyword` | `str` | No | `""` | Partial search term |

```python
suggest: AutoSuggestResponse = client.get_auto_suggest("budget")
# suggest.suggestions → list[str | dict] | None
```

---

#### `GET /api/v1/public-datasets`

Searches and lists public datasets.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `keyword` | `str \| None` | No | — | Free-text search |
| `categories` | `str \| None` | No | — | Comma-separated category slugs |
| `organizations` | `str \| None` | No | — | Comma-separated org slugs |
| `data_formats` | `str \| None` | No | — | Comma-separated formats (e.g. `"CSV,JSON"`) |
| `sort_by` | `str \| None` | No | `"MOST_RELEVANT"` | Sort order (see [SortByEnum](#sortbyenum)) |
| `page` | `int` | No | `1` | Page number (≥ 1) |
| `page_size` | `int` | No | `20` | Items per page (0–10 000) |

```python
resp: DatasetListResponse = client.get_public_datasets(
    keyword="tax", sort_by="NEWEST", page=1, page_size=10
)
# resp.data.results   → list[Any] | None
# resp.data.total     → int | None
# resp.data.page      → int | None
# resp.data.page_size → int | None
```

---

#### `GET /api/v1/public-datasets/seo`

Returns SEO metadata (slug, title, description) for all public datasets.

```python
seo: list[Any] = client.get_public_datasets_seo()
```

---

#### `GET /api/v1/public-datasets/{id}`

Returns full detail for a single dataset.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `dataset_id` | `str` | Yes | — | Dataset slug or UUID |
| `locale` | `str \| None` | No | — | Language code (`"en"` / `"km"`) |

```python
ds: DatasetDetail = client.get_public_dataset("budget-2024", locale="en")
# ds.id, ds.slug, ds.title_en, ds.title_kh, ds.description_en …
```

---

#### `GET /api/v1/public-datasets/{id}/file`

Returns file metadata (download links) for a dataset.

```python
files: DatasetFileInfo = client.get_public_dataset_file("budget-2024")
# files.files → list[DatasetFileEntry] | None
```

---

#### `GET /api/v1/public-datasets/{id}/json`

Returns a paginated JSON preview of dataset contents.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `dataset_id` | `str` | Yes | — | Dataset identifier |
| `page` | `int` | No | `1` | Page number (≥ 1) |
| `page_size` | `int` | No | `10` | Items per page (0–200) |

```python
preview: DatasetJsonPreview = client.get_public_dataset_json(
    "budget-2024", page=1, page_size=20
)
# preview.data.results → list[dict] | None
# preview.columns      → list[str | dict] | None
```

---

#### `GET /api/v1/public-datasets/{id}/map-data`

Returns geographic / map data (GeoJSON-like) for a dataset.

```python
geo: DatasetMapData = client.get_public_dataset_map_data("provinces-2024")
# geo.type     → str | None   (e.g. "FeatureCollection")
# geo.features → list[dict] | None
```

---

#### `GET /api/v1/public-datasets/{id}/realtime-api-spec`

Returns the real-time API specification (OpenAPI) for a dataset.

```python
spec: RealtimeApiSpec = client.get_realtime_api_spec("exchange-rate")
# spec.openapi → str | None
# spec.paths   → dict | None
```

---

### Events and News

#### `GET /api/v1/events-and-news`

Lists events, news articles or blog posts.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `category` | `str \| None` | No | — | `"blog"` or `"events_and_news"` |
| `keyword` | `str \| None` | No | — | Free-text search |
| `page` | `int` | No | `1` | Page number |
| `size` | `int` | No | `10` | Items per page |
| `sort_by` | `str \| None` | No | — | `title_en`, `title_kh`, `created_at`, `updated_at`, `event_date` |
| `order_by` | `str \| None` | No | — | `"asc"` or `"desc"` |

```python
resp: EventsAndNewsListResponse = client.get_events_and_news(
    category="events_and_news", sort_by="event_date", order_by="desc"
)
# resp.data.results → list[EventsAndNewsList] | None
```

---

#### `GET /api/v1/events-and-news/{events_and_news_slug}`

Returns a single article by its URL slug.

```python
article: EventsAndNewsDetail = client.get_event_or_news("annual-report-2024")
# article.title_en, article.body_en, article.body_kh …
```

---

### Superset Dashboard Token

#### `POST /api/v1/superset/dashboard-token`

Requests a guest token for an embedded Apache Superset dashboard.

```python
token_resp: dict = client.get_dashboard_token("my-dashboard-uuid")
# token_resp["token"] → str
```

---

### Contact

#### `POST /api/v1/contact/`

Submits a contact / enquiry form.

| Field | Type | Constraints |
|-------|------|-------------|
| `first_name` | `str` | non-empty, whitespace stripped |
| `last_name` | `str` | non-empty, whitespace stripped |
| `email` | `str` | valid email format |
| `phone` | `str` | 9–15 characters |
| `message` | `str` | non-empty, whitespace stripped |

```python
resp: dict = client.send_contact(
    first_name="Jane",
    last_name="Doe",
    email="jane.doe@example.com",
    phone="0123456789",
    message="Hello, I would like to learn more about the open data portal.",
)
```

---

### Realtime API – Exchange Rate

#### `GET /api/v1/realtime-api/exchange-rate`

Returns today's KHR exchange rate(s) published by the National Bank of Cambodia.

| Parameter | Type | Required | Allowed Values |
|-----------|------|----------|----------------|
| `currency_id` | `str \| None` | No | `AUD`, `CAD`, `CHF`, `CNH`, `CNY`, `EUR`, `GBP`, `HKD`, `IDR`, `INR`, `JPY`, `KRW`, `LAK`, `MMK`, `MYR`, `NZD`, `PHP`, `SDR`, `SEK`, `SGD`, `THB`, `TWD`, `VND`, `USD` |

```python
# All currencies → data is a list
all_rates: ExchangeRateResponse = client.get_exchange_rate()

# Single currency → data is a single object
usd: ExchangeRateResponse = client.get_exchange_rate("USD")
print(usd.data.currency_id)   # "USD"
print(usd.data.valid_date)    # date
print(usd.data.data)          # {"buy": ..., "sell": ...}
```

**Error responses:**

| Status | Body |
|--------|------|
| `400` | `{"name": "ERROR_PARAMS", "errorMsg": "Invalid currency_id"}` |
| `404` | `{"name": "REAL_TIME_API_DATA_NOT_FOUND", "errorMsg": "There is no today rate yet."}` |

---

### Realtime API – Weather

#### `GET /api/v1/realtime-api/weather`

Returns the latest weather forecast for Cambodia.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `province` | `str \| None` | No | Province name (see [Provinces list](#provinces)) |

```python
# All provinces → data is a list
all_weather: WeatherResponse = client.get_weather()

# Single province → data is a single object
pp: WeatherResponse = client.get_weather("Phnom Penh")
print(pp.data.name)         # "Phnom Penh"
print(pp.data.last_updated) # datetime
print(pp.data.data)         # weather payload dict
```

**Error responses:**

| Status | Body |
|--------|------|
| `400` | `{"name": "ERROR_PARAMS", "errorMsg": "Invalid province"}` |
| `404` | `{"name": "REAL_TIME_API_DATA_NOT_FOUND", "errorMsg": "Weather data not found"}` |

---

### Realtime API – Air Quality Index

#### `GET /api/v1/realtime-api/aqi`

Returns the latest Air Quality Index (AQI) readings for Cambodia.

```python
all_aqi: AqiResponse = client.get_aqi()
sr: AqiResponse = client.get_aqi("Siem Reap")
print(sr.data.data)  # {"aqi": 42, "category": "Good", ...}
```

**Error responses:** same shape as Weather (400 / 404).

---

### Realtime API – UV Index

#### `GET /api/v1/realtime-api/uv`

Returns the latest Ultraviolet (UV) Index readings for Cambodia.

```python
all_uv: UvResponse = client.get_uv()
bt: UvResponse = client.get_uv("Battambang")
print(bt.data.data)  # {"uv_index": 8, "level": "Very High", ...}
```

**Error responses:** same shape as Weather (400 / 404).

---

### Realtime API – CSX Index

#### `GET /api/v1/realtime-api/csx-index`

Returns the latest Cambodia Securities Exchange (CSX) composite index snapshot.

```python
idx: CsxIndexResponse = client.get_csx_index()
print(idx.data.value)           # float | None
print(idx.data.change_percent)  # float | None
print(idx.data.market_cap)      # float | None
```

> **Note:** Only `id` and `created_at` are guaranteed; all other fields may be `None`.

**Error responses:**

| Status | Body |
|--------|------|
| `404` | `{"name": "REAL_TIME_API_DATA_NOT_FOUND", "errorMsg": "CSX index data not found"}` |

---

### Realtime API – CSX Summary

#### `GET /api/v1/realtime-api/csx-summary`

Returns per-stock trading summary for all CSX-listed companies.

```python
summary: CsxSummaryResponse = client.get_csx_summary()
for stock in summary.data:
    print(stock.name, stock.close, stock.volume)
```

> **Note:** Only `id`, `name`, and `created_at` are guaranteed; all other fields may be `None`.

**Error responses:**

| Status | Body |
|--------|------|
| `404` | `{"name": "REAL_TIME_API_DATA_NOT_FOUND", "errorMsg": "CSX summary data not found"}` |

---

## Pydantic Models

All client methods return typed Pydantic v2 models. Fields documented as
`anyOf: [{type: X}, {type: null}]` in the OpenAPI spec are typed `X | None`.
Endpoints whose response schema is `{}` use `extra="allow"` with all fields
optional, so they parse successfully regardless of server shape changes.

### Fully-defined models (from the OpenAPI spec)

| Model | Required Fields | Notable Optional Fields |
|-------|----------------|------------------------|
| `SingleExchangeRateResponse` | `id`, `valid_date`, `created_at`, `currency_id`, `data` | — |
| `SingleWeatherResponse` | `id`, `name`, `created_at`, `last_updated`, `data` | — |
| `SingleAqiResponse` | `id`, `name`, `created_at`, `last_updated`, `data` | — |
| `SingleUvResponse` | `id`, `name`, `created_at`, `last_updated`, `data` | — |
| `SingleCsxIndexResponse` | `id`, `created_at` | `value`, `change`, `change_percent`, `market_cap`, … |
| `SingleCsxSummaryResponse` | `id`, `name`, `created_at` | `icode`, `dividend`, `close`, `pe`, `pb`, … |

### Flexible models (`extra="allow"`, all fields optional)

| Model | Endpoint |
|-------|----------|
| `HomeData` | `/api/v1/public-datasets/home` |
| `CountData` | `/api/v1/public-datasets/count-data` |
| `FilterOptions` | `/api/v1/public-datasets/filter-options` |
| `AutoSuggestResponse` | `/api/v1/public-datasets/auto-suggest` |
| `DatasetListResponse` | `/api/v1/public-datasets` |
| `DatasetDetail` | `/api/v1/public-datasets/{id}` |
| `DatasetFileInfo` | `/api/v1/public-datasets/{id}/file` |
| `DatasetJsonPreview` | `/api/v1/public-datasets/{id}/json` |
| `DatasetMapData` | `/api/v1/public-datasets/{id}/map-data` |
| `RealtimeApiSpec` | `/api/v1/public-datasets/{id}/realtime-api-spec` |
| `EventsAndNewsListResponse` | `/api/v1/events-and-news` |
| `EventsAndNewsDetail` | `/api/v1/events-and-news/{slug}` |

---

## Scripts

Run any script directly with `uv run`:

```bash
# Public Datasets
uv run scripts/public_datasets.py

# Events and News
uv run scripts/events_news.py

# All Realtime APIs (exchange rate, weather, AQI, UV, CSX)
uv run scripts/realtime_api.py

# Contact form (edit the placeholder values first)
uv run scripts/contact.py

# Explore filter options (categories, organisations, formats)
uv run scripts/explore_filters.py

# Bulk-harvest ALL metadata + file URLs
uv run scripts/fetch_all_datasets.py
```

Each script prints pretty-printed output for every API call it makes.

---

## Bulk Data Harvesting

### The question: category filter, org filter, or plain pagination?

> **TL;DR — use plain pagination with `page_size=10000`.**
> It is the most efficient approach: one request covers the entire catalogue,
> no duplicates, no missed datasets.

| Approach | Requests needed | Risk of duplicates | Best for |
|---|---|---|---|
| **Plain pagination** `page_size=10000` | 1 (or a few) | ✅ None | Full catalogue harvest |
| Category filter | 1 per category | ⚠️ Yes (cross-category datasets) | Grouped-by-category views |
| Organisation filter | 1 per organisation | ⚠️ Yes (shared datasets) | Grouped-by-org views |
| Data-format filter | 1 per format | ⚠️ Yes | Format-specific pipelines |

---

### Step-by-step strategy

#### Step 1 — Explore the catalogue (once)

```bash
uv run scripts/explore_filters.py
```

This shows how many datasets exist, and their distribution across categories,
organisations, and data formats. Sample output:

```
Total: 142 datasets  /  87 datasources

=== Categories (14) ===
  finance                        38 datasets   [Finance]
  agriculture                    22 datasets   [Agriculture]
  education                      18 datasets   [Education]
  ...

=== Organisations (11) ===
  ministry-of-finance            55 datasets   [Ministry of Finance]
  national-bank-of-cambodia      14 datasets   [National Bank of Cambodia]
  ...

=== Data Formats (5) ===
  CSV                            98 datasets
  XLSX                           44 datasets
  JSON                           12 datasets
  ...
```

#### Step 2 — Harvest all metadata

```bash
uv run scripts/fetch_all_datasets.py
```

Writes `output/metadata.json` — a JSON array of every dataset metadata record.

```bash
# Limit to first 20 datasets (useful for testing)
MAX_DATASETS=20 uv run scripts/fetch_all_datasets.py

# Metadata only (skip file-URL collection)
FETCH_DATA=false uv run scripts/fetch_all_datasets.py

# Custom output directory
DATA_DIR=/tmp/data-ef uv run scripts/fetch_all_datasets.py
```

**Typical `metadata.json` record shape** (all fields optional per the API spec):

```json
{
  "organization_id": 43,
  "format": "PDF",
  "download_count": 0,
  "file_url": "pd_69d4f3d075bdc100087f426d.pdf",
  "dashboard_id": null,
  "id": "pd_69d4f3d075bdc100087f426d",
  "file_size": "74528308",
  "api_calls_count": 0,
  "column_data_id": null,
  "created_at": "2026-04-07T12:08:48.349161+00:00",
  "views_count": 13,
  "frequency": "once",
  "name": "Inter-Ministerial Prakas on Geographical Area Codes of the Kingdom of Cambodia 2025",
  "is_active": true,
  "coverage_start": "2025-09-09",
  "updated_at": "2026-04-07T12:17:59.511414+00:00",
  "description": "This Prakas is an Inter-Ministerial Prakas that shows the introduction of the capital, province, municipality, district, khan, commune, sangkat, and village identification codes of the Kingdom of Cambodia, as attached in the annex to this Inter-Ministerial Prakas. The Secretary-General, the Director-General of the General Department of Administration, the heads of departments and all units under the Ministry of Interior, the Directors-General of relevant General Departments, the heads of departments and all units under the Ministry of Land Management, Urban Planning and Construction, the governors of the capital, province, municipality, district, khan, and the commune/sangkat chiefs shall be responsible for implementing this Inter-Ministerial Prakas according to their respective duties from the date of signature. \n This announcement was made in Phnom Penh and signed on September 9, 2025, by His Excellency Dr. Sar Sokha, Deputy Prime Minister and Minister of Interior, and His Excellency Say Samal, Deputy Prime Minister and Minister of Land Management, Urban Planning, and Construction.",
  "coverage_end": "2030-12-31",
  "deleted_at": null,
  "source": null,
  "categories": [
    {
      "name_en": "Geospatial Data",
      "category_id": 30,
      "slug": "geospatial-data",
      "name_kh": "ទិន្នន័យភូមិសាស្រ្ត",
      "abbreviation": "GD",
      "deleted_at": null
    }
  ],
  "organization": {
    "name_kh": "ក្រសួងរៀបចំដែនដី នគរូបនីយកម្ម និងសំណង់",
    "abbreviation": "MLMUPC",
    "organization_id": 43,
    "file_url": "org_img_66b43bf8bcc3db0001df6754.png",
    "deleted_at": null,
    "name_en": "Ministry of Land Management, Urban Planning and Construction",
    "format": "PNG",
    "is_active": true
  }
}
```

#### Step 3 — Collect data for each dataset

The script also writes `output/data_index.json`, which describes how data is
available for every dataset.

**Method A — downloadable file (preferred)**

If `/file` returns entries the raw file (CSV, XLSX, …) is available for direct
download:

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
  "json_row_count": null
}
```

Download all files in a single shell loop:

```bash
jq -r '.[] | select(.method=="file") | .files[] | .url' output/data_index.json \
  | xargs -P 4 -I{} wget -q -P output/files/ {}
```

**Method B — JSON preview (fallback)**

Datasets without downloadable files expose their data through the paginated
`/json` endpoint (max 200 rows per page):

```json
{
  "id": "province-stats-2023",
  "method": "json",
  "files": [],
  "json_row_count": 1250
}
```

Retrieve all rows programmatically:

```python
import math, sys
sys.path.insert(0, "src")
from data_ef_api import DataEFClient

PAGE = 200  # maximum allowed

with DataEFClient() as client:
    # First page to get total
    first = client.get_public_dataset_json("province-stats-2023", page=1, page_size=PAGE)
    total = first.data.total or 0
    rows = list(first.data.results or [])

    for p in range(2, math.ceil(total / PAGE) + 1):
        page_data = client.get_public_dataset_json("province-stats-2023", page=p, page_size=PAGE)
        rows.extend(page_data.data.results or [])

print(f"Downloaded {len(rows)} rows")
```

---

### Complete harvest summary output

After `fetch_all_datasets.py` finishes it prints a summary:

```
============================================================
  SUMMARY
============================================================
  Total datasets harvested : 142
  Have downloadable files  : 118  (247 files total)
  JSON-only (no file)      :  20
  No data available        :   4

  Output written to: /your/path/output/
    metadata.json   — 142 records
    data_index.json — 142 records
============================================================
```

---

### Filtering use-cases

Even though plain pagination is best for a full harvest, filters are useful for
targeted queries:

```python
from data_ef_api import DataEFClient

with DataEFClient() as client:
    # All finance datasets
    finance = client.get_public_datasets(categories="finance", page_size=10000)

    # All datasets from the Ministry of Finance
    mof = client.get_public_datasets(organizations="ministry-of-finance", page_size=10000)

    # CSV-only datasets
    csvs = client.get_public_datasets(data_formats="CSV", page_size=10000)

    # Combined: finance CSVs, sorted newest first
    finance_csvs = client.get_public_datasets(
        categories="finance",
        data_formats="CSV",
        sort_by="NEWEST",
        page_size=10000,
    )
```

> **Note:** Slug values for `categories` and `organizations` come from the
> `/filter-options` endpoint. Run `explore_filters.py` to list them all.

---

## Running Tests

```bash
# Run all 38 tests
uv run pytest

# Verbose output
uv run pytest -v

# Lint with ruff
uv run ruff check src/ tests/
```

Tests use `pytest-httpx` to mock every HTTP call — **no network access required**.

---

## Enumerations & Constants

### SortByEnum

| Value | Description |
|-------|-------------|
| `MOST_RELEVANT` | Default — most relevant to the search query |
| `MOST_DOWNLOADED` | Most downloaded datasets first |
| `RECENTLY_UPDATED` | Most recently updated first |
| `MOST_POPULAR` | Most popular datasets first |
| `NEWEST` | Newest datasets first |

### EventsAndNewsCategoryEnum

| Value | Description |
|-------|-------------|
| `blog` | Blog posts |
| `events_and_news` | Events and news articles |

### Provinces

All 25 Cambodian provinces accepted by the weather / AQI / UV endpoints:

`Phnom Penh` · `Sihanoukville` · `Siem Reap` · `Battambang` · `Takeo` · `Koh Kong` · `Kratie` · `Kampot` · `Kep` · `Kampong Thom` · `Svay Rieng` · `Mondulkiri` · `Banteay Meanchey` · `Kandal` · `Prey Veng` · `Kampong Chhnang` · `Strung Treng` · `Preah Vihear` · `Tboung Khmum` · `Pailin` · `Ratanakiri` · `Kampong Speu` · `Kampong Cham` · `Oddar Meanchey` · `Pursat`

### Currency IDs

All 24 currencies accepted by the exchange-rate endpoint:

`AUD` · `CAD` · `CHF` · `CNH` · `CNY` · `EUR` · `GBP` · `HKD` · `IDR` · `INR` · `JPY` · `KRW` · `LAK` · `MMK` · `MYR` · `NZD` · `PHP` · `SDR` · `SEK` · `SGD` · `THB` · `TWD` · `VND` · `USD`
