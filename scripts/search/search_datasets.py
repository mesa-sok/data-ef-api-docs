#!/usr/bin/env python3
"""
search_datasets.py
------------------
Search for datasets using semantic similarity via a Qdrant server.

Usage:
    uv run scripts/search_datasets.py "your search query here"
    uv run scripts/search_datasets.py "budget by province" --top-k 10 --threshold 0.3
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from litellm import embedding
from qdrant_client import QdrantClient

load_dotenv()

# Configuration
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "data_ef_datasets")
EMBEDDING_MODEL = "text-embedding-3-small"
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: uv run scripts/search_datasets.py "<query>" [--top-k N] [--threshold F]')
        sys.exit(1)

    query = sys.argv[1]
    top_k = 5
    threshold = 0.0

    args = sys.argv[2:]
    for i, arg in enumerate(args):
        if arg == "--top-k" and i + 1 < len(args):
            top_k = int(args[i + 1])
        elif arg == "--threshold" and i + 1 < len(args):
            threshold = float(args[i + 1])

    # 1. Connect to Qdrant server
    client = QdrantClient(url=QDRANT_URL)

    # 2. Embed the query using litellm → OpenAI text-embedding-3-small
    print(f"Embedding query via {EMBEDDING_MODEL}…")
    response = embedding(model=EMBEDDING_MODEL, input=[query])
    query_vector = response.data[0]["embedding"]

    # 3. Search Qdrant
    print(f"Searching '{COLLECTION_NAME}' for top {top_k} matches…")
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        score_threshold=threshold if threshold > 0 else None,
        limit=top_k,
    ).points

    # 4. Display results
    if not results:
        print(f"\nNo datasets found (threshold={threshold}).")
        return

    print("\nTop Semantic Matches:")
    print("-" * 60)
    for i, res in enumerate(results, 1):
        p = res.payload
        print(f"{i}. [{res.score:.4f}] {p['name']}")
        print(f"   ID: {p['dataset_id']}")
        print(f"   Category: {p['category']}")
        print(f"   Org: {p['org']}")
        print("-" * 60)


if __name__ == "__main__":
    main()
