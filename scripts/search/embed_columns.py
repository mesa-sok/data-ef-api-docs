#!/usr/bin/env python3
"""
embed_columns.py
----------------
Extracts unique columns from column_metadata.json and generates embeddings
using text-embedding-3-small. Saves the mapping to artifacts/column_embeddings.json.

Usage:
    uv run scripts/embed_columns.py
"""

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from litellm import embedding
from qdrant_client import QdrantClient, models
import uuid

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = ROOT / "artifacts"
COLUMN_METADATA_PATH = ARTIFACTS_DIR / "column_metadata.json"

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
BATCH_SIZE = 500
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLUMNS_COLLECTION = os.environ.get("COLUMNS_COLLECTION", "data_ef_columns")


def main():
    if not COLUMN_METADATA_PATH.exists():
        print(f"Error: {COLUMN_METADATA_PATH} not found.")
        return

    print("Loading column metadata...")
    col_meta = json.loads(COLUMN_METADATA_PATH.read_text(encoding="utf-8"))

    # 1. Collect unique columns
    # We map the exact column title to its "semantic string" (title + description)
    unique_cols = {}
    for dataset in col_meta:
        for col in dataset.get("columns", []):
            title = col.get("title", "")
            if not title:
                continue
            
            # Skip purely Khmer columns as they are usually redundant with the English/normalized ones
            if title.endswith("_kh"):
                continue

            desc = col.get("description", "")
            
            # Format: "title: description" or just "title" if no description
            semantic_string = f"{title}: {desc}".strip(" :")
            unique_cols[title] = semantic_string

    titles = list(unique_cols.keys())
    texts_to_embed = list(unique_cols.values())
    total_cols = len(titles)

    print(f"Found {total_cols} unique non-Khmer columns to embed.")

    # 2. Setup Qdrant
    print(f"Connecting to Qdrant at {QDRANT_URL} ...")
    qclient = QdrantClient(url=QDRANT_URL)
    
    existing = {c.name for c in qclient.get_collections().collections}
    if COLUMNS_COLLECTION not in existing:
        print(f"Creating collection '{COLUMNS_COLLECTION}' ...")
        qclient.create_collection(
            collection_name=COLUMNS_COLLECTION,
            vectors_config=models.VectorParams(
                size=EMBEDDING_DIM,
                distance=models.Distance.COSINE,
            ),
        )

    # 3. Embed and Upsert in batches
    total_embedded = 0
    for batch_start in range(0, total_cols, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total_cols)
        batch_titles = titles[batch_start:batch_end]
        batch_texts = texts_to_embed[batch_start:batch_end]
        
        print(f"Embedding batch {batch_start // BATCH_SIZE + 1} ({batch_start+1} to {batch_end} of {total_cols})...")
        
        points = []
        try:
            response = embedding(model=EMBEDDING_MODEL, input=batch_texts)
            items = sorted(response.data, key=lambda x: x["index"])
            
            for i, item in enumerate(items):
                points.append(
                    models.PointStruct(
                        # We use a UUID generated from the title to be deterministic
                        id=str(uuid.uuid5(uuid.NAMESPACE_URL, batch_titles[i])),
                        vector=item["embedding"],
                        payload={"title": batch_titles[i], "semantic_string": batch_texts[i]}
                    )
                )
                
        except Exception as e:
            print(f"Error embedding batch: {e}")
            print("Trying one-by-one for this batch...")
            for i, text in enumerate(batch_texts):
                try:
                    res = embedding(model=EMBEDDING_MODEL, input=[text])
                    points.append(
                        models.PointStruct(
                            id=str(uuid.uuid5(uuid.NAMESPACE_URL, batch_titles[i])),
                            vector=res.data[0]["embedding"],
                            payload={"title": batch_titles[i], "semantic_string": batch_texts[i]}
                        )
                    )
                except Exception as e_single:
                    print(f"  Failed to embed '{batch_titles[i]}': {e_single}")

        if points:
            qclient.upsert(collection_name=COLUMNS_COLLECTION, points=points)
            total_embedded += len(points)
            
        time.sleep(0.1) # small pause

    print(f"Successfully embedded and stored {total_embedded} columns in Qdrant collection '{COLUMNS_COLLECTION}'.")


if __name__ == "__main__":
    main()
