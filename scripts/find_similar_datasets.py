#!/usr/bin/env python3
"""
find_similar_datasets.py
------------------------
Find the top N closest dataset matches to a specific dataset using Retrieval.

Usage:
    uv run scripts/find_similar_datasets.py "pd_..."
"""

import sys
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configuration
REPO_ROOT = Path(__file__).resolve().parent.parent
QDRANT_PATH = REPO_ROOT / "artifacts" / "qdrant_storage"
COLLECTION_NAME = "data_ef_datasets"

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run scripts/find_similar_datasets.py <dataset_id> [top_k]")
        print("Example: uv run scripts/find_similar_datasets.py pd_675fb32b255e6c0001248206 10")
        return

    dataset_id = sys.argv[1]
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    
    # 1. Initialize Qdrant Client
    client = QdrantClient(path=str(QDRANT_PATH))
    
    # 2. Retrieve the target dataset's vector using a payload filter
    print(f"Locating dataset '{dataset_id}'...")
    search_result = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="dataset_id",
                    match=models.MatchValue(value=dataset_id)
                )
            ]
        ),
        with_vectors=True,
        limit=1
    )
    
    records = search_result[0]
    if not records:
        print(f"Error: Dataset ID '{dataset_id}' not found in the Qdrant collection.")
        return
        
    target_point = records[0]
    target_vector = target_point.vector
    target_payload = target_point.payload
    
    print(f"\nTarget Dataset: {target_payload['name']} ({target_payload['dataset_id']})")
    print(f"Category: {target_payload['category']} | Org: {target_payload['org']}")
    print("-" * 60)
    
    # 3. Search Qdrant for closest matches (Retrieval)
    print(f"\nFinding Top {top_k} Closest Matches (Threshold: {threshold})...")
    
    # We ask for top_k + 1 because the target dataset itself will be the #1 match (score ~1.0)
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=target_vector,
        score_threshold=threshold if threshold > 0 else None,
        limit=top_k + 1
    ).points
    
    # 4. Display Results (skipping the first result which is the query itself)
    if not results or (len(results) == 1 and results[0].payload["dataset_id"] == dataset_id):
        print(f"\nNo other datasets found matching the criteria (Threshold: {threshold}).")
        return

    print("\nTop Schema/Structural Matches:")
    print("-" * 60)
    rank = 1
    for res in results:
        p = res.payload
        # Skip the dataset we are querying with
        if p["dataset_id"] == dataset_id:
            continue
            
        print(f"{rank}. [{res.score:.4f}] {p['name']}")
        print(f"   ID: {p['dataset_id']}")
        print(f"   Category: {p['category']}")
        print(f"   Org: {p['org']}")
        print("-" * 60)
        rank += 1
        
        if rank > top_k:
            break

if __name__ == "__main__":
    main()
