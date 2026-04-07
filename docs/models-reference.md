# Models Reference

All response models are Pydantic v2 `BaseModel` subclasses.

**Conventions:**
- Models for **realtime endpoints** have strictly typed, non-optional fields (the spec is fully defined).
- Models for **public-dataset and events/news endpoints** use `extra="allow"` and `X | None` fields because the spec declares `{}` for every response.
- Every model can be serialised with `.model_dump()` and deserialised with `Model.model_validate(dict)`.

---

## `src/data_ef_api/models/public_datasets.py`

### `DatasetListData`

Inner `data` object returned by the dataset-list endpoint.

| Field | Type | Description |
|---|---|---|
| `results` | `list[Any] \| None` | Dataset metadata records (list of dicts) |
| `total` | `int \| None` | Total matching datasets |
| `page` | `int \| None` | Current page |
| `page_size` | `int \| None` | Items per page |
| `total_pages` | `int \| None` | Total pages |

---

### `DatasetListResponse`

Response envelope for `GET /api/v1/public-datasets`.

| Field | Type |
|---|---|
| `data` | `DatasetListData \| None` |

---

### `HomeData`

Response for `GET /api/v1/public-datasets/home`.

| Field | Type | Description |
|---|---|---|
| `featured_datasets` | `list[Any] \| None` | Curated featured dataset records |
| `recent_datasets` | `list[Any] \| None` | Most recently added datasets |
| `stats` | `dict[str, Any] \| None` | Aggregate statistics (downloads, dataset counts, etc.) |

---

### `CountData`

Response for `GET /api/v1/public-datasets/count-data`.

| Field | Type | Description |
|---|---|---|
| `datasets` | `int \| None` | Total number of public datasets |
| `datasources` | `int \| None` | Total number of data sources |

---

### `FilterOptionItem`

A single selectable filter option.

| Field | Type | Description |
|---|---|---|
| `id` | `str \| int \| None` | Numeric or string identifier |
| `name` | `str \| None` | Display name (English) |
| `slug` | `str \| None` | URL-friendly identifier — use this as the filter parameter value |
| `count` | `int \| None` | Number of datasets in this group |

---

### `FilterOptions`

Response for `GET /api/v1/public-datasets/filter-options`.

| Field | Type |
|---|---|
| `categories` | `list[FilterOptionItem] \| None` |
| `organizations` | `list[FilterOptionItem] \| None` |
| `data_formats` | `list[FilterOptionItem] \| None` |

---

### `AutoSuggestResponse`

Response for `GET /api/v1/public-datasets/auto-suggest`.

| Field | Type |
|---|---|
| `suggestions` | `list[str \| dict[str, Any]] \| None` |

---

### `DatasetDetail`

Response for `GET /api/v1/public-datasets/{id}`.

| Field | Type | Description |
|---|---|---|
| `id` | `str \| int \| None` | Dataset ID |
| `slug` | `str \| None` | URL slug |
| `title_en` | `str \| None` | Title (English) |
| `title_kh` | `str \| None` | Title (Khmer) |
| `description_en` | `str \| None` | Description (English) |
| `description_kh` | `str \| None` | Description (Khmer) |
| `category` | `dict[str, Any] \| None` | Category object `{"id", "slug", "name_en", "name_kh"}` |
| `organization` | `dict[str, Any] \| None` | Organisation object `{"id", "slug", "name_en", "name_kh"}` |
| `tags` | `list[Any] \| None` | Tag list |
| `license` | `str \| None` | License identifier (e.g. `"CC-BY-4.0"`) |
| `created_at` | `str \| None` | ISO 8601 creation timestamp |
| `updated_at` | `str \| None` | ISO 8601 last-update timestamp |

---

### `DatasetFileEntry`

A single downloadable file attached to a dataset.

| Field | Type | Description |
|---|---|---|
| `id` | `str \| int \| None` | File ID |
| `name` | `str \| None` | Filename |
| `format` | `str \| None` | Format string: `"CSV"`, `"XLSX"`, `"JSON"`, etc. |
| `url` | `str \| None` | Direct download URL |
| `size` | `int \| str \| None` | File size in bytes |

---

### `DatasetFileInfo`

Response for `GET /api/v1/public-datasets/{id}/file`.

| Field | Type |
|---|---|
| `files` | `list[DatasetFileEntry] \| None` |

---

### `DatasetJsonPreviewData`

Inner wrapper for the JSON-preview endpoint.

| Field | Type | Description |
|---|---|---|
| `results` | `list[dict[str, Any]] \| None` | Row data (one dict per row) |
| `total` | `int \| None` | Total rows across all pages |
| `page` | `int \| None` | Current page |
| `page_size` | `int \| None` | Rows per page |

---

### `DatasetJsonPreview`

Response for `GET /api/v1/public-datasets/{id}/json`.

| Field | Type | Description |
|---|---|---|
| `data` | `DatasetJsonPreviewData \| None` | Paginated row data |
| `columns` | `list[str \| dict[str, Any]] \| None` | Column names or column metadata objects |

---

### `DatasetMapData`

Response for `GET /api/v1/public-datasets/{id}/map-data`.

| Field | Type |
|---|---|
| `type` | `str \| None` | GeoJSON type (usually `"FeatureCollection"`) |
| `features` | `list[dict[str, Any]] \| None` | GeoJSON Feature objects |

---

### `RealtimeApiSpec`

Response for `GET /api/v1/public-datasets/{id}/realtime-api-spec`.  
An OpenAPI 3.x specification fragment.

| Field | Type |
|---|---|
| `openapi` | `str \| None` | OpenAPI version string |
| `info` | `dict[str, Any] \| None` | API info block |
| `paths` | `dict[str, Any] \| None` | Path-item objects |

---

## `src/data_ef_api/models/events_news.py`

### `EventsAndNewsList`

A single article summary as it appears in a list response.

| Field | Type | Description |
|---|---|---|
| `id` | `str \| int \| None` | Article ID |
| `slug` | `str \| None` | URL slug (use for `get_event_or_news()`) |
| `title_en` | `str \| None` | Title (English) |
| `title_kh` | `str \| None` | Title (Khmer) |
| `summary_en` | `str \| None` | Short summary (English) |
| `summary_kh` | `str \| None` | Short summary (Khmer) |
| `category` | `str \| None` | `"blog"` or `"events_and_news"` |
| `event_date` | `str \| None` | ISO date string |
| `thumbnail` | `str \| None` | Thumbnail image URL |
| `created_at` | `str \| None` | ISO 8601 creation timestamp |
| `updated_at` | `str \| None` | ISO 8601 last-update timestamp |

---

### `EventsAndNewsListData`

Paginated wrapper returned by the list endpoint.

| Field | Type |
|---|---|
| `results` | `list[EventsAndNewsList] \| None` |
| `total` | `int \| None` |
| `page` | `int \| None` |
| `size` | `int \| None` |
| `total_pages` | `int \| None` |

---

### `EventsAndNewsListResponse`

Response envelope for `GET /api/v1/events-and-news`.

| Field | Type |
|---|---|
| `data` | `EventsAndNewsListData \| None` |

---

### `EventsAndNewsDetail`

Full article returned by `GET /api/v1/events-and-news/{slug}`.

| Field | Type | Description |
|---|---|---|
| `id` | `str \| int \| None` | Article ID |
| `slug` | `str \| None` | URL slug |
| `title_en` | `str \| None` | Title (English) |
| `title_kh` | `str \| None` | Title (Khmer) |
| `body_en` | `str \| None` | Full article body (English), may contain HTML |
| `body_kh` | `str \| None` | Full article body (Khmer) |
| `summary_en` | `str \| None` | Short summary (English) |
| `summary_kh` | `str \| None` | Short summary (Khmer) |
| `category` | `str \| None` | `"blog"` or `"events_and_news"` |
| `event_date` | `str \| None` | ISO date string |
| `thumbnail` | `str \| None` | Thumbnail image URL |
| `images` | `list[Any] \| None` | Additional image URLs |
| `tags` | `list[Any] \| None` | Tag list |
| `created_at` | `str \| None` | ISO 8601 creation timestamp |
| `updated_at` | `str \| None` | ISO 8601 last-update timestamp |

---

## `src/data_ef_api/models/realtime.py`

### `SingleExchangeRateResponse`

One currency's exchange-rate entry.

| Field | Type | Notes |
|---|---|---|
| `id` | `int` | Record ID |
| `valid_date` | `date` | Date this rate is valid for |
| `created_at` | `datetime` | Record creation timestamp |
| `currency_id` | `str` | ISO 4217 currency code, e.g. `"USD"` |
| `data` | `dict[str, Any]` | Rate payload, e.g. `{"buy": 4100.0, "sell": 4120.0}` |

---

### `ExchangeRateResponse`

| Field | Type | Notes |
|---|---|---|
| `data` | `SingleExchangeRateResponse \| list[SingleExchangeRateResponse]` | Single object when `currency_id` is specified; list otherwise |

---

### `SingleWeatherResponse` / `SingleAqiResponse` / `SingleUvResponse`

All three share the same shape:

| Field | Type | Notes |
|---|---|---|
| `id` | `int` | Record ID |
| `name` | `str` | Province name |
| `created_at` | `datetime` | Record creation timestamp |
| `last_updated` | `datetime` | Last data update |
| `data` | `dict[str, Any]` | Sensor payload (varies by endpoint) |

Their response envelopes (`WeatherResponse`, `AqiResponse`, `UvResponse`) each have:

| Field | Type |
|---|---|
| `data` | `Single* \| list[Single*]` |

---

### `SingleCsxIndexResponse`

Cambodia Securities Exchange composite index snapshot.

| Field | Type | Nullable? |
|---|---|---|
| `id` | `int` | No |
| `created_at` | `datetime` | No |
| `date` | `str \| None` | Yes |
| `value` | `float \| None` | Yes |
| `change` | `float \| None` | Yes |
| `change_percent` | `float \| None` | Yes |
| `change_up_down` | `str \| None` | Yes — `"up"` or `"down"` |
| `index_time` | `str \| None` | Yes |
| `opening` | `float \| None` | Yes |
| `high` | `float \| None` | Yes |
| `low` | `float \| None` | Yes |
| `trading_volume` | `str \| None` | Yes — formatted string e.g. `"1,234,567"` |
| `trading_value` | `str \| None` | Yes |
| `market_cap` | `float \| None` | Yes |

---

### `SingleCsxSummaryResponse`

Per-stock trading summary for one CSX-listed company.

| Field | Type | Nullable? |
|---|---|---|
| `id` | `int` | No |
| `name` | `str` | No |
| `created_at` | `datetime` | No |
| `icode` | `str \| None` | Yes — ticker symbol |
| `dividend` | `float \| None` | Yes |
| `stock` | `str \| None` | Yes — stock name |
| `close` | `str \| None` | Yes |
| `change_up_down` | `str \| None` | Yes |
| `change` | `float \| None` | Yes |
| `open_price` | `str \| None` | Yes |
| `high` | `str \| None` | Yes |
| `low` | `str \| None` | Yes |
| `volume` | `str \| None` | Yes |
| `value` | `str \| None` | Yes |
| `pe` | `str \| None` | Yes — Price/Earnings ratio |
| `pb` | `str \| None` | Yes — Price/Book ratio |

---

## `src/data_ef_api/models/contact.py`

### `EmailRequest`

Request body for `POST /api/v1/contact/`.

| Field | Type | Constraints |
|---|---|---|
| `first_name` | `str` | Non-empty, whitespace stripped |
| `last_name` | `str` | Non-empty, whitespace stripped |
| `email` | `EmailStr` | Valid email address |
| `phone` | `str` | 9–15 characters |
| `message` | `str` | Non-empty, whitespace stripped |

---

### `DashboardTokenRequest`

Request body for `POST /api/v1/superset/dashboard-token`.

| Field | Type |
|---|---|
| `dashboard_id` | `str` |

---

## `src/data_ef_api/models/common.py`

### `ValidationError`

A single FastAPI 422 validation error entry.

| Field | Type |
|---|---|
| `loc` | `list[str \| int]` |
| `msg` | `str` |
| `type` | `str` |

---

### `HTTPValidationError`

Top-level 422 Unprocessable Entity response body.

| Field | Type |
|---|---|
| `detail` | `list[ValidationError] \| None` |

---

### `Pagination`

Generic pagination metadata helper (extra fields allowed).

| Field | Type |
|---|---|
| `page` | `int \| None` |
| `page_size` | `int \| None` |
| `total` | `int \| None` |
| `total_pages` | `int \| None` |
| `results` | `list[Any] \| None` |

---

## `src/data_ef_api/models/enums.py`

### `SortByEnum`

| Value | Description |
|---|---|
| `MOST_RELEVANT` | Default; matches on title/description |
| `MOST_DOWNLOADED` | Sorted by download count |
| `RECENTLY_UPDATED` | Most recently updated first |
| `MOST_POPULAR` | By popularity score |
| `NEWEST` | By creation date, newest first |

---

### `EventsAndNewsCategoryEnum`

| Value | Description |
|---|---|
| `BLOG` | Blog posts |
| `EVENTS_AND_NEWS` | Events and news articles |

---

### `EventsAndNewsSortBy`

`title_en` · `title_kh` · `created_at` · `updated_at` · `event_date`

---

### `EventsAndNewsOrderBy`

`asc` · `desc`

---

## `src/data_ef_api/models/errors.py`

Error-response models for every realtime endpoint.  
These are **not** returned by the client methods but document the HTTP error payloads.

| Model | Status | Endpoint |
|---|---|---|
| `ExchangeRateError400` | 400 | Exchange rate (invalid `currency_id`) |
| `ExchangeRateError404` | 404 | Exchange rate (no data today) |
| `WeatherError400` | 400 | Weather (invalid province) |
| `WeatherError404` | 404 | Weather (data not found) |
| `AqiError400` | 400 | AQI (invalid province) |
| `AqiError404` | 404 | AQI (data not found) |
| `UvError400` | 400 | UV (invalid province) |
| `UvError404` | 404 | UV (data not found) |
| `CsxIndexError404` | 404 | CSX Index (data not found) |
| `CsxSummaryError404` | 404 | CSX Summary (data not found) |

All error models share the same two fields:

| Field | Python name | JSON key | Description |
|---|---|---|---|
| `name` | `name` | `name` | Machine-readable error code |
| `error_msg` | `error_msg` | `errorMsg` | Human-readable message |
