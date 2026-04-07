# Client Reference — `DataEFClient`

`DataEFClient` is a synchronous HTTP client built on [httpx](https://www.python-httpx.org/).  
It covers all 20 public endpoints of the Data EF API.

```python
from data_ef_api import DataEFClient

# Use as a context manager (recommended — closes connection automatically)
with DataEFClient() as client:
    result = client.get_count_data()

# Or manage lifetime manually
client = DataEFClient(timeout=60.0)
result = client.get_count_data()
client.close()
```

**Constructor parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `base_url` | `str` | `"https://data.mef.gov.kh"` | Root URL of the API |
| `timeout` | `float` | `30.0` | Request timeout in seconds |

---

## Public Datasets

### `get_home() → HomeData`

Returns homepage summary data.

`GET /api/v1/public-datasets/home`

```python
home = client.get_home()
# home.featured_datasets → list of featured dataset dicts
# home.recent_datasets   → list of recently added dataset dicts
# home.stats             → {"total_datasets": N, "total_downloads": N, ...}
```

---

### `get_count_data() → CountData`

Returns total counts of datasets and data-sources.

`GET /api/v1/public-datasets/count-data`

```python
counts = client.get_count_data()
print(counts.datasets)     # e.g. 142
print(counts.datasources)  # e.g. 87
```

---

### `get_filter_options() → FilterOptions`

Returns available filter options: categories, organisations, and data formats.  
Use the `slug` values as arguments to `get_public_datasets()`.

`GET /api/v1/public-datasets/filter-options`

```python
opts = client.get_filter_options()

for cat in (opts.categories or []):
    print(cat.slug, cat.name, cat.count)   # e.g. "finance", "Finance", 38

for org in (opts.organizations or []):
    print(org.slug, org.name, org.count)

for fmt in (opts.data_formats or []):
    print(fmt.slug, fmt.name, fmt.count)   # e.g. "CSV", "CSV", 98
```

---

### `get_auto_suggest(keyword="") → AutoSuggestResponse`

Returns search suggestions for a partial keyword.

`GET /api/v1/public-datasets/auto-suggest`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `keyword` | `str` | `""` | Partial search term |

```python
resp = client.get_auto_suggest("budget")
print(resp.suggestions)  # ["Budget Law 2024", "Budget Report 2023", ...]
```

---

### `get_public_datasets(...) → DatasetListResponse`

Search and list public datasets with optional filters and pagination.

`GET /api/v1/public-datasets`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `keyword` | `str \| None` | `None` | Free-text search term |
| `categories` | `str \| None` | `None` | Comma-separated category slugs |
| `organizations` | `str \| None` | `None` | Comma-separated organisation slugs |
| `data_formats` | `str \| None` | `None` | Comma-separated format names, e.g. `"CSV,JSON"` |
| `sort_by` | `str \| None` | `"MOST_RELEVANT"` | See [Sort Options](#sort-options) |
| `page` | `int` | `1` | 1-based page number |
| `page_size` | `int` | `20` | Items per page (max 10 000) |

**Sort options** (`sort_by` values): `MOST_RELEVANT`, `MOST_DOWNLOADED`, `RECENTLY_UPDATED`, `MOST_POPULAR`, `NEWEST`

```python
# All datasets in one request (full catalogue)
all_ds = client.get_public_datasets(sort_by="NEWEST", page_size=10000)
records = all_ds.data.results or []
print(f"{len(records)} datasets, {all_ds.data.total} total")

# Filter: finance CSVs only
finance_csv = client.get_public_datasets(
    categories="finance",
    data_formats="CSV",
    sort_by="NEWEST",
    page_size=100,
)

# Full-text search
results = client.get_public_datasets(keyword="gdp growth", page_size=20)
```

---

### `get_public_datasets_seo() → list[Any]`

Returns SEO metadata (slug, title, description) for all datasets.  
Useful for building sitemaps or search indexes.

`GET /api/v1/public-datasets/seo`

```python
seo_list = client.get_public_datasets_seo()
for item in seo_list:
    print(item.get("slug"), "—", item.get("title_en"))
```

---

### `get_public_dataset(dataset_id, locale=None) → DatasetDetail`

Returns full detail for a single dataset by its slug or UUID.

`GET /api/v1/public-datasets/{id}`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `dataset_id` | `str` | required | Dataset slug or UUID |
| `locale` | `str \| None` | `None` | Language code: `"en"` or `"km"` |

```python
ds = client.get_public_dataset("budget-law-2024")
print(ds.title_en)
print(ds.category)       # {"id": 1, "slug": "finance", "name_en": "Finance", ...}
print(ds.organization)   # {"id": 3, "slug": "ministry-of-finance", ...}
print(ds.tags)           # ["budget", "law", "finance"]
print(ds.license)        # "CC-BY-4.0"
print(ds.updated_at)     # "2024-03-20T12:30:00Z"
```

---

### `get_public_dataset_file(dataset_id) → DatasetFileInfo`

Returns file metadata (download URLs) for a dataset.  
This is the **preferred** method for accessing a dataset's raw data.

`GET /api/v1/public-datasets/{id}/file`

```python
file_info = client.get_public_dataset_file("budget-law-2024")
for f in (file_info.files or []):
    print(f.name, f.format, f.url, f.size)
    # budget_2024.csv  CSV  https://data.mef.gov.kh/media/...  204800
```

---

### `get_public_dataset_json(dataset_id, *, page=1, page_size=10) → DatasetJsonPreview`

Returns a paginated JSON preview of a dataset's row data.  
Use as a fallback when `/file` returns no entries.

`GET /api/v1/public-datasets/{id}/json`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `dataset_id` | `str` | required | Dataset identifier |
| `page` | `int` | `1` | 1-based page number |
| `page_size` | `int` | `10` | Rows per page (max 200) |

```python
preview = client.get_public_dataset_json("province-stats-2023", page=1, page_size=50)
total   = preview.data.total        # e.g. 1250
columns = preview.columns           # ["province", "year", "population", ...]
rows    = preview.data.results      # list of row dicts
```

**Paginating all rows:**

```python
import math

PAGE = 200
first = client.get_public_dataset_json("province-stats-2023", page=1, page_size=PAGE)
total = first.data.total or 0
rows  = list(first.data.results or [])

for p in range(2, math.ceil(total / PAGE) + 1):
    page_data = client.get_public_dataset_json("province-stats-2023", page=p, page_size=PAGE)
    rows.extend(page_data.data.results or [])
```

---

### `get_public_dataset_map_data(dataset_id) → DatasetMapData`

Returns geographic / GeoJSON data for a dataset.

`GET /api/v1/public-datasets/{id}/map-data`

```python
geo = client.get_public_dataset_map_data("cambodia-provinces")
print(geo.type)      # "FeatureCollection"
print(len(geo.features or []))  # number of geographic features
```

---

### `get_realtime_api_spec(dataset_id) → RealtimeApiSpec`

Returns the OpenAPI spec for a real-time dataset endpoint.

`GET /api/v1/public-datasets/{id}/realtime-api-spec`

```python
spec = client.get_realtime_api_spec("exchange-rate")
print(spec.openapi)  # "3.0.0"
print(list(spec.paths.keys()))  # ["/api/v1/realtime-api/exchange-rate"]
```

---

## Events and News

### `get_events_and_news(...) → EventsAndNewsListResponse`

Lists events and news (or blog) articles.

`GET /api/v1/events-and-news`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `category` | `str \| None` | `None` | `"blog"` or `"events_and_news"` |
| `keyword` | `str \| None` | `None` | Free-text search |
| `page` | `int` | `1` | Page number |
| `size` | `int` | `10` | Items per page |
| `sort_by` | `str \| None` | `None` | `title_en`, `title_kh`, `created_at`, `updated_at`, `event_date` |
| `order_by` | `str \| None` | `None` | `"asc"` or `"desc"` |

```python
news = client.get_events_and_news(category="events_and_news", size=20)
for article in (news.data.results or []):
    print(article.slug, article.title_en, article.event_date)
```

---

### `get_event_or_news(slug) → EventsAndNewsDetail`

Returns a single event / news article by its slug.

`GET /api/v1/events-and-news/{events_and_news_slug}`

```python
article = client.get_event_or_news("open-data-forum-2024")
print(article.title_en)
print(article.body_en)     # full HTML/markdown body
print(article.thumbnail)   # URL string
```

---

## Superset

### `get_dashboard_token(dashboard_id) → dict`

Requests a guest token for an embedded Superset dashboard.

`POST /api/v1/superset/dashboard-token`

```python
token = client.get_dashboard_token("abc-123-uuid")
print(token)  # {"token": "eyJ..."}
```

---

## Contact

### `send_contact(...) → dict`

Submits a contact/enquiry form.

`POST /api/v1/contact/`

| Parameter | Type | Constraints |
|---|---|---|
| `first_name` | `str` | non-empty, whitespace stripped |
| `last_name` | `str` | non-empty, whitespace stripped |
| `email` | `str` | valid email address |
| `phone` | `str` | 9–15 digits |
| `message` | `str` | non-empty, whitespace stripped |

```python
resp = client.send_contact(
    first_name="Jane",
    last_name="Doe",
    email="jane@example.com",
    phone="0123456789",
    message="Hello, I would like more information about the open data portal.",
)
print(resp)  # {"success": true} or similar
```

---

## Realtime APIs

### `get_exchange_rate(currency_id=None) → ExchangeRateResponse`

Returns today's KHR exchange rate(s) from the National Bank of Cambodia.

`GET /api/v1/realtime-api/exchange-rate`

| Parameter | Type | Description |
|---|---|---|
| `currency_id` | `str \| None` | ISO currency code, e.g. `"USD"`. Omit for all currencies. |

**Supported currencies:** `AUD`, `CAD`, `CHF`, `CNH`, `CNY`, `EUR`, `GBP`, `HKD`, `IDR`, `INR`, `JPY`, `KRW`, `LAK`, `MMK`, `MYR`, `NZD`, `PHP`, `SDR`, `SEK`, `SGD`, `THB`, `TWD`, `VND`, `USD`

```python
# Single currency → data is a SingleExchangeRateResponse object
usd = client.get_exchange_rate("USD")
print(usd.data.currency_id)  # "USD"
print(usd.data.valid_date)   # date
print(usd.data.data)         # {"buy": 4100.0, "sell": 4120.0}

# All currencies → data is a list
all_rates = client.get_exchange_rate()
for r in all_rates.data:
    print(r.currency_id, r.data)
```

**Error responses:**

| Status | Body |
|--------|------|
| `400` | `{"name": "ERROR_PARAMS", "errorMsg": "Invalid currency_id"}` |
| `404` | `{"name": "REAL_TIME_API_DATA_NOT_FOUND", "errorMsg": "There is no today rate yet."}` |

---

### `get_weather(province=None) → WeatherResponse`

Returns the latest weather forecast for Cambodia.

`GET /api/v1/realtime-api/weather`

```python
# All provinces
all_wx = client.get_weather()
for w in all_wx.data:
    print(w.name, w.last_updated, w.data)

# Single province
pp = client.get_weather("Phnom Penh")
print(pp.data.data)  # {"temperature": 32, "humidity": 80, ...}
```

**Supported provinces:** see [constants.py](../src/data_ef_api/constants.py) `PROVINCES` list (25 provinces).

---

### `get_aqi(province=None) → AqiResponse`

Returns the latest Air Quality Index (AQI) readings.

`GET /api/v1/realtime-api/aqi`

```python
aqi = client.get_aqi("Phnom Penh")
print(aqi.data.data)  # {"aqi": 42, "pm25": 12.3, "category": "Good"}
```

---

### `get_uv(province=None) → UvResponse`

Returns the latest UV Index readings.

`GET /api/v1/realtime-api/uv`

```python
uv = client.get_uv("Siem Reap")
print(uv.data.data)  # {"uv_index": 9, "category": "Very High"}
```

---

### `get_csx_index() → CsxIndexResponse`

Returns the latest Cambodia Securities Exchange (CSX) composite index snapshot.

`GET /api/v1/realtime-api/csx-index`

```python
idx = client.get_csx_index()
print(idx.data.value)           # e.g. 493.2
print(idx.data.change)          # e.g. -2.1
print(idx.data.change_percent)  # e.g. -0.42
print(idx.data.trading_volume)  # e.g. "1,234,567"
```

---

### `get_csx_summary() → CsxSummaryResponse`

Returns per-stock trading summaries for all CSX-listed companies.

`GET /api/v1/realtime-api/csx-summary`

```python
summary = client.get_csx_summary()
for stock in summary.data:
    print(stock.icode, stock.name, stock.close, stock.change)
```
