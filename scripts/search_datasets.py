#!/usr/bin/env python3
"""
search_datasets.py
------------------
Search for datasets using semantic similarity via the local Qdrant collection.

Usage:
    uv run scripts/search_datasets.py "your search query here"
"""

import os
import sys
from pathlib import Path

import httpx
from qdrant_client import QdrantClient

# Configuration
REPO_ROOT = Path(__file__).resolve().parent.parent
QDRANT_PATH = REPO_ROOT / "artifacts" / "qdrant_storage"
COLLECTION_NAME = "data_ef_datasets"
API_BASE = os.environ.get("EMBEDDING_API_BASE", "http://localhost:8081/v1")
EMBEDDING_MODEL = "embeddinggemma"

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run scripts/search_datasets.py \"<query>\"")
        return

    query = sys.argv[1]
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    
    # 1. Initialize Qdrant Client
    client = QdrantClient(path=str(QDRANT_PATH))
    
    # 2. Embed the query using the same local server
    print(f"Embedding query: '{query}' (Threshold: {threshold})...")
    with httpx.Client() as http_client:
        resp = http_client.post(
            f"{API_BASE}/embeddings",
            json={"model": EMBEDDING_MODEL, "input": query},
            timeout=30.0
        )
        resp.raise_for_status()
        query_vector = resp.json()["data"][0]["embedding"]
    
    # 3. Search Qdrant
    print(f"Searching collection '{COLLECTION_NAME}'...")
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        score_threshold=threshold if threshold > 0 else None,
        limit=5
    ).points
    
    # 4. Display Results
    if not results:
        print(f"\nNo datasets found matching the criteria (Threshold: {threshold}).")
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
