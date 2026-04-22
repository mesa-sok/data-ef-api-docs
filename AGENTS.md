# AGENTS.md

## Project Overview

`data-ef-api-docs` is a Python project centered on the Data EF Public API at `https://data.mef.gov.kh/api/v1/`.

The repository currently has two main areas:

- A typed API client in `src/data_ef_api/` built with `httpx` and Pydantic v2.
- Dataset harvesting, embedding, semantic-search, and evaluation scripts in `scripts/` backed by local artifacts and optional Qdrant / embedding infrastructure.

Treat this as an application repo with a reusable client library inside it, not just a docs-only or scripts-only repo.

## Tech Stack

- Python `>=3.12`
- Dependency management and command runner: `uv`
- HTTP client: `httpx`
- Data models: Pydantic v2
- Tests: `pytest`, `pytest-httpx`
- Lint / format: `ruff`
- Optional semantic-search stack: `qdrant-client`, local embedding server, LLM-assisted labeling/eval scripts

## Repository Layout

```text
src/data_ef_api/
  client.py                  # DataEFClient, one method per endpoint pattern
  constants.py               # Base URL and shared constants
  models/                    # Pydantic models grouped by API area

tests/
  test_client.py             # Mocked client tests

scripts/
  explore/                   # one-off API demos & quick inspections
    public_datasets.py
    events_news.py
    realtime_api.py
    contact.py
    explore_filters.py
  harvest/                   # bulk fetching & column metadata
    fetch_all_datasets.py
    fetch_categories.py
    fetch_organizations.py
    fetch_csv_datasets.py
    fetch_column_metadata.py
    standalone_fetch_column_metadata.py
    standalone_export_datasets.py
  search/                    # embedding, vector DB, similarity queries
    embed_datasets.py
    embed_columns.py
    search_datasets.py
    find_dataset_similarity.py
    find_similar_datasets.py
    nearest_neighbors_by_dataset_id.py
    find_similar_datasets.ipynb
  eval/                      # evaluation set generation & LLM labeling
    generate_eval_sets.py
    label_pairs_llm.py
    run_eval.py

docs/
  client-reference.md
  scripts-guide.md
  bulk-harvesting.md
  semantic-search.md
  models-reference.md
  data-schemas.md
```

## Setup Commands

Install dependencies for normal development:

```bash
uv sync --all-groups
```

Quick import smoke test:

```bash
uv run python -c "from data_ef_api import DataEFClient; print('OK')"
```

There is no required API key for the public Data EF API.

## Core Development Workflow

Run tests after changing the client, models, or request/response behavior:

```bash
uv run pytest
```

Run lint and formatting checks before finishing a change:

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

If you modify scripts heavily, it is reasonable to run the specific script you touched with `uv run` in addition to tests.

## API Client Conventions

- Keep endpoint methods on `DataEFClient` in `src/data_ef_api/client.py`.
- Put new response/request models under `src/data_ef_api/models/` in the closest existing module.
- Re-export public models from `src/data_ef_api/models/__init__.py` when they are part of the supported surface.
- Follow existing typing style: prefer explicit optional types like `X | None`.
- Preserve current parsing patterns instead of introducing new abstraction layers unless there is a clear reuse benefit.
- Raise or propagate `httpx` errors consistently with the existing client behavior.

When adding a new endpoint, usually update all of these:

1. `src/data_ef_api/models/...`
2. `src/data_ef_api/models/__init__.py`
3. `src/data_ef_api/client.py`
4. `tests/test_client.py`
5. Relevant docs in `README.md` or `docs/`

## Testing Guidance

- Tests for the client are in `tests/test_client.py`.
- The suite uses `pytest-httpx`; keep tests fully mocked.
- Do not add tests that depend on real network access.
- For new client methods, add at least one happy-path assertion and one error-path assertion when the endpoint has meaningful error behavior.
- Assert parsed model behavior, not just raw JSON equality.

Useful commands:

```bash
uv run pytest -v
uv run pytest tests/test_client.py
uv run pytest tests/test_client.py -k weather
```

## Script Workflows

API exploration / harvesting scripts:

```bash
uv run scripts/explore/public_datasets.py
uv run scripts/explore/events_news.py
uv run scripts/explore/realtime_api.py
uv run scripts/explore/explore_filters.py
uv run scripts/harvest/fetch_all_datasets.py
```

Some scripts write outputs under `artifacts/`. Do not casually rename output files or directories without checking related docs and downstream scripts.

Standalone scripts prefixed with `standalone_` may be intended to run without the full package import path assumptions. Preserve that distinction unless you are deliberately consolidating workflows.

## Semantic Search And Embeddings

The repo also includes optional semantic-search tooling documented in `docs/semantic-search.md`.

Typical commands:

```bash
uv run scripts/search/embed_datasets.py
uv run scripts/search/search_datasets.py "budget allocation"
uv run scripts/search/embed_columns.py
uv run scripts/eval/run_eval.py
```

Important notes:

- Some of these scripts expect local services or models, such as a local embedding API or Qdrant storage.
- Common environment variables referenced by docs/scripts include `EMBEDDING_API_BASE`, `COLLECTION_NAME`, `BATCH_SIZE`, `DATA_DIR`, `MAX_DATASETS`, `FETCH_DATA`, and `VERBOSE`.
- `artifacts/qdrant_storage/` is persistent local state for vector search workflows.

Do not assume semantic-search scripts are covered by the main pytest suite.

## Code Style

- Ruff line length is `99`.
- Use the `src/` layout correctly; imports should resolve through `data_ef_api`.
- Keep changes minimal and local when extending the client or models.
- Match existing file organization before creating new modules.
- Prefer ASCII unless a file already requires Unicode content.

## Documentation Expectations

Update documentation when behavior changes:

- `README.md` for top-level usage or API examples
- `docs/client-reference.md` for client surface changes
- `docs/scripts-guide.md` for script behavior or new scripts
- `docs/semantic-search.md` for embedding/search pipeline changes
- `docs/data-schemas.md` when generated artifact structure changes

## Pull Request / Change Hygiene

Before finishing substantial code changes, run:

```bash
uv run ruff check src/ tests/
uv run pytest
```

If you changed script-only logic that is not exercised by tests, mention what you ran manually and what remains unverified.

## Gotchas

- `uv sync --all-groups` is required for dev tools; plain `uv sync` may omit them.
- The public API itself is unauthenticated, but some local semantic-search tooling may depend on local services or model endpoints.
- `tests/test_client.py` currently adjusts `sys.path` directly; avoid large test harness changes unless needed.
- `artifacts/` contains generated data and may be intentionally tracked for some workflows. Do not delete or rewrite large generated outputs unless the task requires it.
