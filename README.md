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
8. [Running Tests](#running-tests)
9. [Enumerations & Constants](#enumerations--constants)

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
│   └── contact.py                  # demonstrates the contact endpoint
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
```

Each script prints pretty-printed JSON for every API call it makes.

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
