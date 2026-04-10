#!/usr/bin/env python3
"""Find nearest-neighbor datasets by dataset ID using local Qdrant embeddings.

Usage:
    uv run scripts/nearest_neighbors_by_dataset_id.py <dataset_id>
    uv run scripts/nearest_neighbors_by_dataset_id.py <dataset_id> --top-k 5 --json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.http import models


ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = ROOT / "artifacts"
METADATA_PATH = ARTIFACTS_DIR / "metadata.json"
QDRANT_PATH = ARTIFACTS_DIR / "qdrant_storage"
COLLECTION_NAME = "data_ef_datasets"


@dataclass
class DatasetRecord:
    id: str
    title: str
    organization_id: int | None
    organization_name: str | None
    category_slug: str | None
    frequency: str | None
    coverage_start: str | None
    coverage_end: str | None


@dataclass
class SimilarityMatch:
    dataset_id: str
    title: str
    score: float
    category: str | None
    organization: str | None


def load_metadata() -> list[dict]:
    return json.loads(METADATA_PATH.read_text(encoding="utf-8"))


def build_records(metadata: list[dict]) -> dict[str, DatasetRecord]:
    records: dict[str, DatasetRecord] = {}
    for item in metadata:
        dataset_id = item.get("id")
        if not dataset_id:
            continue

        organization = item.get("organization") or {}
        categories = item.get("categories") or []
        first_category = categories[0] if categories else {}

        records[dataset_id] = DatasetRecord(
            id=dataset_id,
            title=item.get("name") or item.get("title") or "",
            organization_id=organization.get("organization_id") or organization.get("id"),
            organization_name=organization.get("name_en")
            or organization.get("name")
            or organization.get("abbreviation"),
            category_slug=first_category.get("slug"),
            frequency=item.get("frequency"),
            coverage_start=item.get("coverage_start"),
            coverage_end=item.get("coverage_end"),
        )
    return records


def get_target_point(client: QdrantClient, dataset_id: str):
    results, _next_offset = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="dataset_id",
                    match=models.MatchValue(value=dataset_id),
                )
            ]
        ),
        with_vectors=True,
        limit=1,
    )

    if not results:
        raise SystemExit(f"dataset_id '{dataset_id}' not found in local Qdrant collection")

    return results[0]


def get_nearest_neighbors(
    client: QdrantClient,
    records: dict[str, DatasetRecord],
    dataset_id: str,
    top_k: int,
) -> tuple[DatasetRecord, list[SimilarityMatch]]:
    target_point = get_target_point(client, dataset_id)
    target_vector = target_point.vector

    nearest_neighbors = client.query_points(
        collection_name=COLLECTION_NAME,
        query=target_vector,
        limit=top_k + 5,
    ).points

    target = records[dataset_id]
    matches: list[SimilarityMatch] = []
    for point in nearest_neighbors:
        payload = point.payload or {}
        match_id = payload.get("dataset_id")
        if not match_id or match_id == dataset_id:
            continue

        match_record = records.get(match_id)
        matches.append(
            SimilarityMatch(
                dataset_id=match_id,
                title=match_record.title if match_record else payload.get("name", ""),
                score=round(float(point.score), 4),
                category=payload.get("category"),
                organization=payload.get("org"),
            )
        )
        if len(matches) >= top_k:
            break

    return target, matches


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_id", help="Dataset ID like pd_...")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="Output JSON")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not METADATA_PATH.exists() or not QDRANT_PATH.exists():
        raise SystemExit("artifacts/metadata.json and artifacts/qdrant_storage are required")

    records = build_records(load_metadata())
    if args.dataset_id not in records:
        raise SystemExit(f"dataset_id '{args.dataset_id}' not found in metadata")

    client = QdrantClient(path=str(QDRANT_PATH))
    target, matches = get_nearest_neighbors(client, records, args.dataset_id, args.top_k)

    if args.json:
        print(
            json.dumps(
                {
                    "target": asdict(target),
                    "matches": [asdict(match) for match in matches],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    print(f"Target: {target.title} ({target.id})")
    print()
    for index, match in enumerate(matches, start=1):
        print(f"{index}. [{match.score}] {match.title}")
        print(f"   ID: {match.dataset_id}")
        print(f"   Category: {match.category}")
        print(f"   Org: {match.organization}")
        print()


if __name__ == "__main__":
    main()
