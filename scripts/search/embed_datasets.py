#!/usr/bin/env python3
"""
embed_datasets.py
-----------------
Build semantic embeddings for every dataset in artifacts/metadata.json +
artifacts/column_metadata.json and store them in a local Qdrant collection.

Usage:
    uv run scripts/embed_datasets.py

The collection is persisted on disk at artifacts/qdrant_storage/ so subsequent
searches do not need to re-embed.

Environment variables (optional):
    EMBEDDING_API_BASE   – base URL for the llama.cpp /v1/embeddings endpoint
                           (default: http://localhost:8081/v1)
    BATCH_SIZE           – number of texts per embedding request (default: 16)
    COLLECTION_NAME      – Qdrant collection name (default: data_ef_datasets)
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from litellm import embedding
from qdrant_client import QdrantClient, models

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
METADATA_FILE = REPO_ROOT / "artifacts" / "metadata.json"
COLUMN_METADATA_FILE = REPO_ROOT / "artifacts" / "column_metadata.json"
QDRANT_PATH = REPO_ROOT / "artifacts" / "qdrant_storage"
CHECKPOINT_FILE = REPO_ROOT / "artifacts" / "embed_checkpoint.json"

BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "128"))
INTER_BATCH_SLEEP = float(os.environ.get("INTER_BATCH_SLEEP", "0.0"))  # seconds between batches
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "data_ef_datasets")
EMBEDDING_DIM = 1536          # text-embedding-3-small produces 1536-d vectors
EMBEDDING_MODEL = "text-embedding-3-small"
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")

# Regex to strip Khmer unicode block (U+1780 – U+17FF) and surrounding spaces
_KHMER_RE = re.compile(r"[\u1780-\u17ff]+")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def strip_khmer(text: str | None) -> str:
    """Remove Khmer characters and normalise whitespace."""
    if not text:
        return ""
    cleaned = _KHMER_RE.sub(" ", text)
    return " ".join(cleaned.split())


def build_semantic_profile(meta: dict[str, Any], col_entry: dict[str, Any] | None) -> str:
    """
    Build a profile focused on 'Joinability' by prioritizing column titles (schema)
    above all else, and removing noisy linguistic descriptions.
    """
    parts: list[str] = []

    # 1. Schema / Join Keys (TOP PRIORITY)
    if col_entry:
        # Extract English titles, skipping Khmer variants
        columns = [
            col.get("title", "") 
            for col in col_entry.get("columns", [])
            if col.get("title") and not col.get("title", "").endswith("_kh")
        ]
        if columns:
            parts.append(f"Schema: {', '.join(columns)}")

    # 2. Key Metadata (Secondary)
    name = strip_khmer(meta.get("name", ""))
    if name:
        parts.append(f"Dataset: {name}")

    org = meta.get("organization", {})
    org_name = strip_khmer(org.get("name_en", "") or org.get("abbreviation", ""))
    if org_name:
        parts.append(f"Organization: {org_name}")

    cats = [strip_khmer(c.get("name_en", "")) for c in meta.get("categories", [])]
    cats = [c for c in cats if c]
    if cats:
        parts.append(f"Categories: {', '.join(cats)}")

    # We omit 'description' and column descriptions to focus strictly on 
    # joinability/structural similarity as requested by the user.
    return "\n".join(parts)


def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Send a batch of texts to the embedding model via litellm.
    Returns a list of embedding vectors in the same order.
    """
    response = embedding(
        model=EMBEDDING_MODEL,
        input=texts
    )
    # litellm returns data sorted by index by default, but we can ensure it
    items = sorted(response.data, key=lambda x: x["index"])
    return [item["embedding"] for item in items]


def load_checkpoint() -> set[str]:
    """Return set of dataset IDs already embedded (from checkpoint file)."""
    if CHECKPOINT_FILE.exists():
        with CHECKPOINT_FILE.open() as f:
            return set(json.load(f))
    return set()


def save_checkpoint(embedded_ids: set[str]) -> None:
    with CHECKPOINT_FILE.open("w") as f:
        json.dump(sorted(embedded_ids), f)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # ------------------------------------------------------------------
    # 1. Load source data
    # ------------------------------------------------------------------
    print(f"Loading metadata from {METADATA_FILE} …")
    with METADATA_FILE.open() as f:
        metadata: list[dict[str, Any]] = json.load(f)

    print(f"Loading column metadata from {COLUMN_METADATA_FILE} …")
    with COLUMN_METADATA_FILE.open() as f:
        raw_cols: list[dict[str, Any]] = json.load(f)

    col_by_id: dict[str, dict[str, Any]] = {entry["id"]: entry for entry in raw_cols}
    print(f"  Loaded {len(metadata)} datasets, {len(col_by_id)} column entries.")

    # ------------------------------------------------------------------
    # 2. Build semantic profiles
    # ------------------------------------------------------------------
    print("Building semantic profiles …")
    records: list[dict[str, Any]] = []
    for meta in metadata:
        ds_id = meta["id"]
        col_entry = col_by_id.get(ds_id)
        profile = build_semantic_profile(meta, col_entry)
        records.append({
            "id": ds_id,
            "name": strip_khmer(meta.get("name", "")),
            "category": ", ".join(
                strip_khmer(c.get("name_en", "")) for c in meta.get("categories", [])
            ),
            "org": strip_khmer(
                (meta.get("organization") or {}).get("name_en", "")
                or (meta.get("organization") or {}).get("abbreviation", "")
            ),
            "frequency": meta.get("frequency", ""),
            "coverage_start": meta.get("coverage_start", ""),
            "coverage_end": meta.get("coverage_end", ""),
            "profile": profile,
        })

    # ------------------------------------------------------------------
    # 3. Initialise Qdrant (local disk-based)
    # ------------------------------------------------------------------
    QDRANT_PATH.mkdir(parents=True, exist_ok=True)
    print(f"Connecting to Qdrant at {QDRANT_URL} …")
    qclient = QdrantClient(url=QDRANT_URL)

    existing_collections = {c.name for c in qclient.get_collections().collections}
    if COLLECTION_NAME not in existing_collections:
        print(f"Creating collection '{COLLECTION_NAME}' (dim={EMBEDDING_DIM}, cosine) …")
        qclient.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=EMBEDDING_DIM,
                distance=models.Distance.COSINE,
            ),
        )
    else:
        print(f"Collection '{COLLECTION_NAME}' already exists.")

    # ------------------------------------------------------------------
    # 4. Resume from checkpoint
    # ------------------------------------------------------------------
    embedded_ids = load_checkpoint()
    pending = [r for r in records if r["id"] not in embedded_ids]
    print(f"{len(embedded_ids)} already embedded. {len(pending)} remaining.")

    if not pending:
        print("Nothing to embed. Done!")
        return

    # ------------------------------------------------------------------
    # 5. Batch embed and upsert
    # ------------------------------------------------------------------
    total = len(pending)
    done = 0

    for batch_start in range(0, total, BATCH_SIZE):
        batch = pending[batch_start : batch_start + BATCH_SIZE]
        texts = [r["profile"] for r in batch]

        print(
            f"  Embedding batch {batch_start // BATCH_SIZE + 1}"
            f"/{(total + BATCH_SIZE - 1) // BATCH_SIZE}"
            f"  [{done + 1}–{min(done + len(batch), total)}/{total}] …",
            end="",
            flush=True,
        )
        t0 = time.perf_counter()
        vectors = embed_batch(texts)
        elapsed = time.perf_counter() - t0
        print(f" {elapsed:.1f}s")

        # Build Qdrant points — use numeric IDs derived from enumeration
        # (Qdrant requires integer or UUID point IDs)
        # We store the original string ID in the payload for lookup.
        base_idx = len(embedded_ids)
        points: list[models.PointStruct] = []
        for i, (rec, vec) in enumerate(zip(batch, vectors)):
            # Use a deterministic numeric ID: index in the full records list
            global_idx = next(
                j for j, r in enumerate(records) if r["id"] == rec["id"]
            )
            points.append(
                models.PointStruct(
                    id=global_idx,
                    vector=vec,
                    payload={
                        "dataset_id": rec["id"],
                        "name": rec["name"],
                        "category": rec["category"],
                        "org": rec["org"],
                        "frequency": rec["frequency"],
                        "coverage_start": rec["coverage_start"],
                        "coverage_end": rec["coverage_end"],
                    },
                )
            )

        qclient.upsert(collection_name=COLLECTION_NAME, points=points)

        for rec in batch:
            embedded_ids.add(rec["id"])
        done += len(batch)

        # Save checkpoint after every batch so we can resume on failure
        save_checkpoint(embedded_ids)

        # Small pause to avoid overwhelming the server
        time.sleep(INTER_BATCH_SLEEP)

    # ------------------------------------------------------------------
    # 6. Summary
    # ------------------------------------------------------------------
    info = qclient.get_collection(COLLECTION_NAME)
    print(f"\nDone! Collection '{COLLECTION_NAME}' now has {info.points_count} points.")
    print(f"Qdrant storage: {QDRANT_PATH}")
    print(f"Checkpoint:     {CHECKPOINT_FILE}")


if __name__ == "__main__":
    main()
