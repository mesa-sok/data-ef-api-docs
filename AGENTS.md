# AGENTS.md

## Project Overview

**data-ef-api-docs** is a Python client library and collection of runnable scripts for the
[Data EF Public API](https://data.mef.gov.kh/api/v1/) provided by the Ministry of Economy and
Finance of Cambodia. It exposes typed Pydantic v2 models for every endpoint and ships ready-made
demo scripts for public datasets, events & news, realtime data (exchange rates, weather, AQI, UV
index, CSX stock exchange), contact form submission, filter exploration, and bulk data harvesting.

**Key technologies:**

| Layer | Technology |
|---|---|
| Language | Python ≥ 3.12 |
| Package manager | [uv](https://github.com/astral-sh/uv) ≥ 0.4 |
| HTTP client | [httpx](https://www.python-httpx.org/) ≥ 0.28 |
| Data validation | [Pydantic v2](https://docs.pydantic.dev/latest/) |
| Test framework | pytest + pytest-httpx (fully mocked — no network needed) |
| Linter/formatter | [Ruff](https://docs.astral.sh/ruff/) |

**Source layout:**

```
src/data_ef_api/
├── __init__.py        # re-exports DataEFClient
├── client.py          # DataEFClient — one method per API endpoint
├── constants.py       # BASE_URL and enum lists
└── models/
    ├── __init__.py
    ├── enums.py        # SortByEnum, EventsAndNewsCategoryEnum
    ├── common.py       # ValidationError, HTTPValidationError, Pagination
    ├── contact.py      # EmailRequest, DashboardTokenRequest
    ├── errors.py       # per-endpoint 400 / 404 error bodies
    ├── realtime.py     # Exchange Rate, Weather, AQI, UV, CSX models
    ├── public_datasets.py
    └── events_news.py

scripts/               # standalone demo scripts (run with uv run, some are plain python3)
tests/
└── test_client.py     # 38 pytest tests using httpx mocking
docs/                  # extended Markdown documentation per feature area
artifacts/             # generated JSON/CSV outputs from harvest scripts
```

---

## Setup Commands

```bash
# 1. Install uv (if not present)
pip install uv          # or: curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install all dependencies, including dev extras
uv sync --all-groups

# 3. Verify installation — import the client
uv run python -c "from data_ef_api import DataEFClient; print('OK')"
```

> No `.env` file or API key is required. The Data EF Public API is open and unauthenticated.

---

## Development Workflow

```bash
# Run a demo script against the live API
uv run scripts/public_datasets.py
uv run scripts/realtime_api.py
uv run scripts/events_news.py
uv run scripts/contact.py           # edit placeholder values first
uv run scripts/explore_filters.py   # lists categories / orgs / formats
uv run scripts/fetch_all_datasets.py  # bulk-harvest ALL metadata + file URLs

# Bulk harvest — environment-variable overrides
MAX_DATASETS=20               uv run scripts/fetch_all_datasets.py  # first 20 only
FETCH_DATA=true               uv run scripts/fetch_all_datasets.py  # fetch data index + file URLs
DATA_DIR=artifacts/custom     uv run scripts/fetch_all_datasets.py  # custom output dir

# Plain python standalone scripts (zero dependencies)
python3 scripts/standalone_export_datasets.py

# Named entry-points (installed by uv sync)
uv run data-ef-public-datasets
uv run data-ef-events-news
uv run data-ef-realtime-api
```

**Base URL:** `https://data.mef.gov.kh` — all client methods call `https://data.mef.gov.kh/api/v1/`.

---

## Testing Instructions

```bash
# Run the full test suite (38 tests, no network access)
uv run pytest

# Verbose output with test names
uv run pytest -v

# Run a subset of tests by keyword
uv run pytest -k "exchange_rate"
uv run pytest -k "weather"

# Run a single specific test
uv run pytest tests/test_client.py::test_get_public_datasets -v

# Show coverage (if pytest-cov is added)
uv run pytest --tb=short
```

**Important:** Tests use `pytest-httpx` to intercept every HTTP call made by `httpx`. **No real
network requests are made.** When adding a new endpoint:
1. Add a matching mock in `tests/test_client.py` using `httpx_mock.add_response(...)`.
2. Assert the returned Pydantic model fields.
3. Test at least one error path (400 / 404) for endpoints that define error shapes.

Test file: `tests/test_client.py`

---

## Code Style

```bash
# Lint source and test code
uv run ruff check src/ tests/

# Auto-fix safe issues
uv run ruff check --fix src/ tests/

# Format (ruff format is the formatter)
uv run ruff format src/ tests/
```

**Conventions:**
- Line length: **99 characters** (configured in `pyproject.toml → [tool.ruff]`).
- Source root is `src/` — all imports use the `data_ef_api` package name.
- All response models are Pydantic v2 (`BaseModel`). Use `model_config = ConfigDict(extra="allow")`
  for endpoints whose OpenAPI schema is `{}` (flexible/undocumented shapes).
- Fields that appear as `anyOf: [{type: X}, {type: null}]` in the OpenAPI spec are typed `X | None`.
- New endpoint methods belong in `src/data_ef_api/client.py` inside the `DataEFClient` class.
- New response shapes belong in the appropriate model file under `src/data_ef_api/models/`.
- Publicly re-export new models from `src/data_ef_api/models/__init__.py`.

---

## Adding a New API Endpoint

1. **Model** — create or extend a model file in `src/data_ef_api/models/`.
2. **Re-export** — add the new model to `src/data_ef_api/models/__init__.py`.
3. **Client method** — add a method to `DataEFClient` in `src/data_ef_api/client.py` following the
   existing pattern (`self._client.get(...)`, parse with `TypeAdapter` or `.model_validate()`).
4. **Demo script** — update or create a script under `scripts/` to exercise the new endpoint.
5. **Tests** — add at least one happy-path and one error-path test in `tests/test_client.py`.
6. **Docs** — update the relevant file under `docs/` (or `README.md` for top-level endpoints).

---

## Bulk Data Harvesting

The recommended approach is **plain pagination with `page_size=10000`** — a single request covers
the entire catalogue with no duplicates.

| Approach | Requests | Duplicate risk | Best for |
|---|---|---|---|
| Plain pagination `page_size=10000` | 1 (or a few) | None | Full catalogue harvest |
| Category filter | 1 per category | Yes (cross-category datasets) | Category views |
| Organisation filter | 1 per org | Yes (shared datasets) | Org-specific views |

Output files written by `fetch_all_datasets.py`:

- `artifacts/metadata.json` — array of all dataset metadata records
- `artifacts/data_index.json` — per-dataset data access method (`"file"` or `"json"`)

To download all files after harvesting:

```bash
jq -r '.[] | select(.method=="file") | .files[] | .url' artifacts/data_index.json \
  | xargs -P 4 -I{} wget -q -P artifacts/files/ {}
```

---

## Key Enumerations & Constants

### `SortByEnum` (for `get_public_datasets`)

`MOST_RELEVANT` · `MOST_DOWNLOADED` · `RECENTLY_UPDATED` · `MOST_POPULAR` · `NEWEST`

### `EventsAndNewsCategoryEnum`

`blog` · `events_and_news`

### Provinces (weather / AQI / UV endpoints)

All 25 Cambodian provinces: `Phnom Penh` · `Siem Reap` · `Battambang` · `Sihanoukville` ·
`Kampot` · `Kep` · `Takeo` · `Koh Kong` · `Kratie` · `Kampong Thom` · `Svay Rieng` ·
`Mondulkiri` · `Banteay Meanchey` · `Kandal` · `Prey Veng` · `Kampong Chhnang` · `Strung Treng` ·
`Preah Vihear` · `Tboung Khmum` · `Pailin` · `Ratanakiri` · `Kampong Speu` · `Kampong Cham` ·
`Oddar Meanchey` · `Pursat`

### Currency IDs (exchange-rate endpoint)

`AUD` · `CAD` · `CHF` · `CNH` · `CNY` · `EUR` · `GBP` · `HKD` · `IDR` · `INR` · `JPY` ·
`KRW` · `LAK` · `MMK` · `MYR` · `NZD` · `PHP` · `SDR` · `SEK` · `SGD` · `THB` · `TWD` ·
`VND` · `USD`

---

## Pull Request Guidelines

- **Title format:** `[component] Brief description`
  - Components: `client`, `models`, `scripts`, `tests`, `docs`, `ci`
  - Example: `[client] Add /realtime-api/new-endpoint method`
- **Required checks before merging:**
  - `uv run ruff check src/ tests/` — must pass with zero errors
  - `uv run pytest` — all 38+ tests must pass
- **Commit style:** Imperative mood, present tense. Example: `Add WeatherResponse model`.
- The `artifacts/` directory contains harvested snapshots of the API data.

---

## Troubleshooting & Gotchas

- **`httpx.HTTPStatusError` on 400/404:** Endpoints with documented error shapes (exchange rate,
  weather, AQI, UV, CSX) return structured JSON bodies. Catch and inspect `e.response.json()`.
- **`uv sync` vs `uv sync --all-groups`:** Plain `uv sync` skips the `dev` dependency group
  (pytest, ruff). Always use `--all-groups` for development.
- **Flexible models:** Endpoints whose OpenAPI schema is `{}` use `extra="allow"` — they accept any
  server-returned payload. New fields added by the server will be accessible via `model.model_extra`.
- **`artifacts/` directory:** Created automatically by harvest scripts; tracked by git.
- **No auth required:** All API calls go to `https://data.mef.gov.kh/api/v1/` with no API key.
- **Locale parameter:** `get_public_dataset(id, locale=...)` accepts `"en"` or `"km"` (Khmer).
