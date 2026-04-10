# Dataset Similarity Pipeline Plan

This document outlines a practical v1 pipeline for finding similar datasets for a target dataset without attempting relational joinability yet.

The goal is to return:

1. Top 5 similar datasets globally
2. Top 5 similar datasets within the same category
3. Top 5 similar datasets within the same organization

## Why Similarity First

Joinability and thematic similarity are different problems. For a first version, similarity is the better target because it is:

- easier to implement and validate
- easier to explain to users
- useful for dataset discovery immediately
- a good foundation for a later joinability layer

## Inputs

The pipeline should use these local artifacts:

- `artifacts/metadata.json`
- `artifacts/column_metadata.json`
- optionally `artifacts/qdrant_storage/` if the embedding index is available

## Expected Output

For a target dataset ID, the script should return three ranked lists:

- `global_top_5`
- `category_top_5`
- `organization_top_5`

Each result should include at least:

- dataset ID
- dataset title
- similarity score
- shared normalized columns
- short explanation

Example output shape:

```json
{
  "target_dataset_id": "pd_...",
  "target_title": "Cambodia Selected Indicators of Money and Prices (2008-2023)",
  "global_top_5": [
    {
      "dataset_id": "pd_...",
      "title": "...",
      "score": 0.91,
      "shared_columns": ["year", "forecasting"],
      "reason": "Very similar macro time-series schema and overlapping indicator structure."
    }
  ],
  "category_top_5": [],
  "organization_top_5": []
}
```

## Pipeline Stages

### 1. Load Data

Read dataset-level metadata from `metadata.json` and schema-level metadata from `column_metadata.json`.

Join them by dataset `id` so each working record contains:

- title
- categories
- organization
- frequency
- coverage dates
- column definitions

### 2. Normalize Dataset Features

Build a normalization layer before any scoring.

Normalize titles by:

- lowercasing
- removing punctuation noise
- removing year tokens such as `2024`, `FY2025`, `(2008-2023)`

Normalize columns by:

- lowercasing
- replacing spaces and hyphens with underscores
- stripping language suffixes like `_en`, `_kh`, `_km`
- mapping common aliases to canonical keys

Recommended alias examples:

- `ref_year`, `year`, `Year` -> `year`
- `ref_month`, `month_num`, `month` -> `month`
- `ref_quarter`, `quarter` -> `quarter`
- `country_partner`, `partner_country_en` -> `country_partner`
- `province`, `province_en`, `capital_province` -> `province`

### 3. Build Features

For each dataset, derive:

- `id`
- `title`
- `normalized_title`
- `series_key`
- `organization_id`
- `organization_name`
- category slugs
- `frequency`
- `coverage_start`
- `coverage_end`
- raw column names
- normalized column names
- optional embedding lookup metadata

The `series_key` should be a normalized title with year markers removed. This helps reduce domination by annual editions of the same dataset family.

### 4. Candidate Generation

The pipeline should support two modes.

#### Mode A: Pure local heuristic mode

Used when Qdrant is not available.

Compare the target dataset against all other datasets in scope.

This is acceptable for the current artifact size and is easier to debug.

#### Mode B: Embedding-assisted mode

Used when `artifacts/qdrant_storage/` exists and the target dataset has an indexed vector.

Use Qdrant to retrieve a broader candidate pool first, for example top 50 nearest neighbors, then rerank with schema and title heuristics.

This should be optional rather than required.

#### Mode C: Embedding-only retrieval

Used when the immediate goal is just `global_top_5` by vector similarity, with no local reranking.

In this mode:

- locate the target dataset point in Qdrant by `dataset_id`
- retrieve its stored vector
- query nearest neighbors directly from the local collection
- skip schema/title/temporal reranking entirely
- return the top 5 global matches ordered only by embedding score

This is the simplest way to validate whether the embedding space is useful before adding heuristic reranking.

### 5. Similarity Scoring

For v1, score only thematic or structural similarity.

If running in embedding-only mode, the score is just the Qdrant cosine similarity returned by the vector search.

Recommended components:

- embedding similarity
- normalized column overlap
- title similarity
- light temporal compatibility bonus

Recommended v1 score:

```text
similarity_score =
  0.45 * embedding_score
+ 0.30 * column_overlap_score
+ 0.15 * title_similarity_score
+ 0.10 * temporal_compatibility_score
```

Where:

- `embedding_score` comes from Qdrant cosine similarity if available, else `0`
- `column_overlap_score` is based on normalized column set intersection
- `title_similarity_score` comes from normalized title token overlap or a string similarity metric
- `temporal_compatibility_score` gives a small bonus for matching frequency or overlapping coverage windows

### 6. Ranking By Scope

Produce rankings in three scopes.

#### Global

All datasets except the target itself.

#### Category

Only datasets sharing at least one category slug with the target.

#### Organization

Only datasets with the same organization ID as the target.

Sort by `similarity_score` descending and return the top 5 per scope.

### 7. Result Explanation

Each returned match should include a short rationale based on evidence from the score inputs.

Useful explanation fragments include:

- shared normalized columns
- same category
- same organization
- similar title family
- similar time-series structure

This makes the pipeline easier to evaluate and tune.

## Implementation Structure

Recommended script path:

- `scripts/find_dataset_similarity.py`

Recommended function structure:

```python
def load_data():
    ...

def normalize_title(title: str) -> str:
    ...

def normalize_column(name: str) -> str:
    ...

def build_dataset_features(metadata_record, column_record):
    ...

def generate_candidates(target, records, scope, use_qdrant=False):
    ...

def score_pair(target, candidate):
    ...

def explain_match(target, candidate, score_details):
    ...

def rank_scope(target, records, scope):
    ...

def main():
    ...
```

## CLI Recommendation

Suggested commands:

```bash
uv run scripts/find_dataset_similarity.py <dataset_id>
uv run scripts/find_dataset_similarity.py <dataset_id> --top-k 5
uv run scripts/find_dataset_similarity.py <dataset_id> --json
uv run scripts/find_dataset_similarity.py <dataset_id> --use-qdrant
```

## Development Order

Recommended implementation order:

1. Build a pure local heuristic version with no Qdrant dependency
2. Add title and column normalization
3. Add scoped ranking for global, category, and organization
4. Add explanation output
5. Add optional Qdrant candidate generation and embedding score

This order keeps the first version deterministic and easy to inspect.

## Known Risks

- annual variants of the same series can dominate rankings
- bilingual duplicate columns can inflate overlap if not normalized well
- some datasets are only weakly distinguishable by title alone
- embeddings should improve candidate quality, but heuristic reranking should remain the source of truth for explainable results

## Future V2

After similarity feels reliable, add a second scoring track for joinability.

That future layer should focus on:

- shared join keys
- grain compatibility
- type compatibility
- stronger schema reasoning across domains

For now, the script should optimize for dataset discovery, not merge readiness.
