#!/usr/bin/env python3
"""Find similar datasets using local metadata and column schema heuristics.

Usage:
    uv run scripts/find_dataset_similarity.py <dataset_id>
    uv run scripts/find_dataset_similarity.py <dataset_id> --top-k 5 --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from math import sqrt

import httpx

from qdrant_client import QdrantClient
from qdrant_client.http import models


ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = ROOT / "artifacts"
METADATA_PATH = ARTIFACTS_DIR / "metadata.json"
COLUMN_METADATA_PATH = ARTIFACTS_DIR / "column_metadata.json"
QDRANT_PATH = ARTIFACTS_DIR / "qdrant_storage"
COLLECTION_NAME = "data_ef_datasets"
API_BASE = os.environ.get("EMBEDDING_API_BASE", "http://localhost:8081/v1")
EMBEDDING_MODEL = "embeddinggemma"
_KHMER_RE = re.compile(r"[\u1780-\u17ff]+")


def load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_title(title: str) -> str:
    text = title.lower()
    text = re.sub(r"\b\d{4}\s*-\s*\d{4}\b", " ", text)
    text = re.sub(r"\b(?:fy\s*)?\d{4}\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def strip_khmer(text: str | None) -> str:
    if not text:
        return ""
    cleaned = _KHMER_RE.sub(" ", text)
    return " ".join(cleaned.split())


def normalize_column(name: str) -> str:
    text = name.lower().strip()
    text = re.sub(r"(_en|_kh|_km)$", "", text)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")

    aliases = {
        "ref_year": "year",
        "ref_month": "month",
        "month_num": "month",
        "ref_quarter": "quarter",
        "partner_country_en": "country_partner",
        "country_partner_en": "country_partner",
        "province_en": "province",
        "capital_province": "province",
    }
    return aliases.get(text, text)


def jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def token_overlap(left: str, right: str) -> float:
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def temporal_compatibility(record: dict, candidate: dict) -> float:
    score = 0.0

    if record.get("frequency") and candidate.get("frequency"):
        if record["frequency"] == candidate["frequency"]:
            score += 0.5

    if (
        record.get("coverage_start")
        and record.get("coverage_end")
        and candidate.get("coverage_start")
        and candidate.get("coverage_end")
    ):
        score += 0.5

    return min(score, 1.0)


def build_records(metadata: list[dict], column_metadata: list[dict]) -> dict[str, dict]:
    column_map = {row["id"]: row for row in column_metadata if row.get("id")}
    records: dict[str, dict] = {}

    for item in metadata:
        dataset_id = item.get("id")
        if not dataset_id:
            continue

        column_row = column_map.get(dataset_id, {})
        columns = []
        for col in column_row.get("columns") or []:
            if isinstance(col, dict):
                title = col.get("title")
                if title:
                    columns.append(title)

        organization = item.get("organization") or {}
        categories = item.get("categories") or []

        title = item.get("name") or ""
        profile_parts = []
        if columns:
            english_columns = [c for c in columns if not c.endswith("_kh")]
            if english_columns:
                profile_parts.append(f"Schema: {', '.join(english_columns)}")

        clean_title = strip_khmer(title)
        if clean_title:
            profile_parts.append(f"Dataset: {clean_title}")

        org_name = strip_khmer(
            organization.get("name_en") or organization.get("abbreviation") or ""
        )
        if org_name:
            profile_parts.append(f"Organization: {org_name}")

        cat_names = [strip_khmer(c.get("name_en", "")) for c in categories]
        cat_names = [c for c in cat_names if c]
        if cat_names:
            profile_parts.append(f"Categories: {', '.join(cat_names)}")

        records[dataset_id] = {
            "id": dataset_id,
            "title": title,
            "normalized_title": normalize_title(title),
            "series_key": normalize_title(title),
            "organization_id": organization.get("organization_id"),
            "organization_name": organization.get("name_en") or organization.get("abbreviation"),
            "category_slugs": [c.get("slug") for c in categories if c.get("slug")],
            "frequency": item.get("frequency"),
            "coverage_start": item.get("coverage_start"),
            "coverage_end": item.get("coverage_end"),
            "raw_columns": columns,
            "normalized_columns": {normalize_column(c) for c in columns if c},
            "profile": "\n".join(profile_parts),
        }

    return records


def score_similarity(record: dict, candidate: dict) -> tuple[float, dict]:
    column_score = jaccard_similarity(
        record["normalized_columns"], candidate["normalized_columns"]
    )
    title_score = token_overlap(record["normalized_title"], candidate["normalized_title"])
    temporal_score = temporal_compatibility(record, candidate)

    score = (0.65 * column_score) + (0.25 * title_score) + (0.10 * temporal_score)
    return score, {
        "column_overlap": round(column_score, 4),
        "title_similarity": round(title_score, 4),
        "temporal_compatibility": round(temporal_score, 4),
    }


def explain_match(record: dict, candidate: dict) -> str:
    reasons = []

    shared_columns = sorted(record["normalized_columns"] & candidate["normalized_columns"])
    if shared_columns:
        reasons.append(f"shared columns: {', '.join(shared_columns[:5])}")

    if set(record["category_slugs"]) & set(candidate["category_slugs"]):
        reasons.append("same category")

    if record.get("organization_id") and record.get("organization_id") == candidate.get(
        "organization_id"
    ):
        reasons.append("same organization")

    if not reasons:
        reasons.append("similar title and schema")

    return "; ".join(reasons)


def rank_candidates(record: dict, candidates: list[dict], top_k: int) -> list[dict]:
    scored = []
    for candidate in candidates:
        if candidate["id"] == record["id"]:
            continue

        score, details = score_similarity(record, candidate)
        scored.append(
            {
                "dataset_id": candidate["id"],
                "title": candidate["title"],
                "series_key": candidate["series_key"],
                "score": score,
                "shared_columns": sorted(
                    record["normalized_columns"] & candidate["normalized_columns"]
                ),
                "reason": explain_match(record, candidate),
                "score_details": details,
            }
        )

    scored.sort(key=lambda row: row["score"], reverse=True)

    # Keep only one result per series family so yearly clones do not flood top results.
    results = []
    seen_series = set()
    for row in scored:
        if row["series_key"] in seen_series:
            continue
        seen_series.add(row["series_key"])
        row["score"] = round(row["score"], 4)
        row.pop("series_key")
        results.append(row)
        if len(results) >= top_k:
            break

    return results


def rank_embedding_only_global(record: dict, records: dict[str, dict], top_k: int) -> list[dict]:
    if not QDRANT_PATH.exists():
        raise SystemExit("artifacts/qdrant_storage is required for --embedding-only")

    client = QdrantClient(path=str(QDRANT_PATH))
    search_result = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="dataset_id",
                    match=models.MatchValue(value=record["id"]),
                )
            ]
        ),
        with_vectors=True,
        limit=1,
    )

    points = search_result[0]
    if not points:
        raise SystemExit(f"dataset_id '{record['id']}' not found in local Qdrant collection")

    target_vector = points[0].vector
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=target_vector,
        limit=top_k + 10,
    ).points

    output = []
    for point in results:
        payload = point.payload or {}
        dataset_id = payload.get("dataset_id")
        if not dataset_id or dataset_id == record["id"]:
            continue
        candidate = records.get(dataset_id)
        if not candidate:
            continue
        output.append(
            {
                "dataset_id": dataset_id,
                "title": candidate["title"],
                "score": round(float(point.score), 4),
                "shared_columns": [],
                "reason": "embedding similarity from local Qdrant index",
            }
        )
        if len(output) >= top_k:
            break

    return output


def embed_texts(texts: list[str]) -> list[list[float]]:
    with httpx.Client() as client:
        response = client.post(
            f"{API_BASE}/embeddings",
            json={"model": EMBEDDING_MODEL, "input": texts},
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()
    items = sorted(data["data"], key=lambda item: item["index"])
    return [item["embedding"] for item in items]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def rank_embedding_live(record: dict, candidates: list[dict], top_k: int) -> list[dict]:
    if not record["profile"]:
        raise SystemExit(f"dataset_id '{record['id']}' has an empty semantic profile")

    candidate_profiles = [
        candidate["profile"] for candidate in candidates if candidate["id"] != record["id"]
    ]
    candidate_records = [candidate for candidate in candidates if candidate["id"] != record["id"]]
    vectors = embed_texts([record["profile"], *candidate_profiles])
    target_vector = vectors[0]
    candidate_vectors = vectors[1:]

    scored = []
    for candidate, vector in zip(candidate_records, candidate_vectors, strict=False):
        score = cosine_similarity(target_vector, vector)
        scored.append(
            {
                "dataset_id": candidate["id"],
                "title": candidate["title"],
                "series_key": candidate["series_key"],
                "score": score,
                "shared_columns": sorted(
                    record["normalized_columns"] & candidate["normalized_columns"]
                ),
                "reason": "embedding similarity from live embedding server",
            }
        )

    scored.sort(key=lambda row: row["score"], reverse=True)

    results = []
    seen_series = set()
    for row in scored:
        if row["series_key"] in seen_series:
            continue
        seen_series.add(row["series_key"])
        row["score"] = round(row["score"], 4)
        row.pop("series_key")
        results.append(row)
        if len(results) >= top_k:
            break

    return results


def get_qdrant_candidate_records(
    record: dict,
    records: dict[str, dict],
    limit: int,
) -> list[dict]:
    if not QDRANT_PATH.exists():
        raise SystemExit("artifacts/qdrant_storage is required for --use-qdrant")

    client = QdrantClient(path=str(QDRANT_PATH))
    search_result = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="dataset_id",
                    match=models.MatchValue(value=record["id"]),
                )
            ]
        ),
        with_vectors=True,
        limit=1,
    )

    points = search_result[0]
    if not points:
        raise SystemExit(f"dataset_id '{record['id']}' not found in local Qdrant collection")

    target_vector = points[0].vector
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=target_vector,
        limit=limit,
    ).points

    candidates: list[dict] = []
    seen_ids = set()
    for point in results:
        payload = point.payload or {}
        dataset_id = payload.get("dataset_id")
        if not dataset_id or dataset_id == record["id"] or dataset_id in seen_ids:
            continue
        candidate = records.get(dataset_id)
        if not candidate:
            continue
        seen_ids.add(dataset_id)
        candidates.append(candidate)

    return candidates


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_id", help="Dataset ID like pd_...")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument(
        "--use-qdrant",
        action="store_true",
        help="Use local Qdrant to generate a candidate pool before reranking",
    )
    parser.add_argument(
        "--candidate-pool",
        type=int,
        default=75,
        help="Candidate pool size when using Qdrant-assisted retrieval",
    )
    parser.add_argument(
        "--embedding-only",
        action="store_true",
        help="Return global top-k using only local Qdrant embedding similarity",
    )
    parser.add_argument(
        "--embedding-live",
        action="store_true",
        help="Use the live embedding server for global/category/organization ranking",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not METADATA_PATH.exists() or not COLUMN_METADATA_PATH.exists():
        raise SystemExit("artifacts/metadata.json and artifacts/column_metadata.json are required")

    metadata = load_json(METADATA_PATH)
    column_metadata = load_json(COLUMN_METADATA_PATH)
    records = build_records(metadata, column_metadata)

    if args.dataset_id not in records:
        raise SystemExit(f"dataset_id '{args.dataset_id}' not found")

    record = records[args.dataset_id]
    all_records = list(records.values())

    if args.embedding_only:
        output = {
            "target_dataset_id": record["id"],
            "target_title": record["title"],
            "global_top_5": rank_embedding_only_global(record, records, args.top_k),
            "category_top_5": [],
            "organization_top_5": [],
        }

        if args.json:
            print(json.dumps(output, indent=2, ensure_ascii=False))
            return

        print(f"Target: {record['title']} ({record['id']})")
        print("\nGlobal Top Matches (Embedding Only):")
        for index, row in enumerate(output["global_top_5"], start=1):
            print(f"{index}. [{row['score']}] {row['title']} ({row['dataset_id']})")
            print(f"   {row['reason']}")
        return

    if args.embedding_live:
        category_candidates = [
            candidate
            for candidate in all_records
            if set(candidate["category_slugs"]) & set(record["category_slugs"])
        ]
        organization_candidates = [
            candidate
            for candidate in all_records
            if candidate["organization_id"] == record["organization_id"]
        ]

        output = {
            "target_dataset_id": record["id"],
            "target_title": record["title"],
            "global_top_5": rank_embedding_live(record, all_records, args.top_k),
            "category_top_5": rank_embedding_live(record, category_candidates, args.top_k),
            "organization_top_5": rank_embedding_live(record, organization_candidates, args.top_k),
        }

        if args.json:
            print(json.dumps(output, indent=2, ensure_ascii=False))
            return

        print(f"Target: {record['title']} ({record['id']})")
        print("\nGlobal Top Matches (Live Embedding):")
        for index, row in enumerate(output["global_top_5"], start=1):
            print(f"{index}. [{row['score']}] {row['title']} ({row['dataset_id']})")
            print(f"   {row['reason']}")

        print("\nCategory Top Matches (Live Embedding):")
        for index, row in enumerate(output["category_top_5"], start=1):
            print(f"{index}. [{row['score']}] {row['title']} ({row['dataset_id']})")
            print(f"   {row['reason']}")

        print("\nOrganization Top Matches (Live Embedding):")
        for index, row in enumerate(output["organization_top_5"], start=1):
            print(f"{index}. [{row['score']}] {row['title']} ({row['dataset_id']})")
            print(f"   {row['reason']}")
        return

    candidate_records = all_records
    if args.use_qdrant:
        candidate_records = get_qdrant_candidate_records(
            record,
            records,
            max(args.candidate_pool, args.top_k + 10),
        )

    category_candidates = [
        candidate
        for candidate in candidate_records
        if set(candidate["category_slugs"]) & set(record["category_slugs"])
    ]
    organization_candidates = [
        candidate
        for candidate in candidate_records
        if candidate["organization_id"] == record["organization_id"]
    ]

    output = {
        "target_dataset_id": record["id"],
        "target_title": record["title"],
        "global_top_5": rank_candidates(record, candidate_records, args.top_k),
        "category_top_5": rank_candidates(record, category_candidates, args.top_k),
        "organization_top_5": rank_candidates(record, organization_candidates, args.top_k),
    }

    if args.json:
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    print(f"Target: {record['title']} ({record['id']})")
    print("\nGlobal Top Matches:")
    for index, row in enumerate(output["global_top_5"], start=1):
        print(f"{index}. [{row['score']}] {row['title']} ({row['dataset_id']})")
        print(f"   {row['reason']}")

    print("\nCategory Top Matches:")
    for index, row in enumerate(output["category_top_5"], start=1):
        print(f"{index}. [{row['score']}] {row['title']} ({row['dataset_id']})")
        print(f"   {row['reason']}")

    print("\nOrganization Top Matches:")
    for index, row in enumerate(output["organization_top_5"], start=1):
        print(f"{index}. [{row['score']}] {row['title']} ({row['dataset_id']})")
        print(f"   {row['reason']}")


if __name__ == "__main__":
    main()
