#!/usr/bin/env python3
"""
run_eval.py
-----------
Evaluates the dataset similarity and search agent against ground-truth evaluation sets.

Usage:
    uv run scripts/run_eval.py --track temporal --top-k 5
    uv run scripts/run_eval.py --track schema --top-k 5
"""

from importlib import import_module
import sys
from pathlib import Path
from types import ModuleType

import click

ROOT = Path(__file__).resolve().parent.parent

ARTIFACTS_DIR = ROOT / "artifacts"
EVAL_DIR = ARTIFACTS_DIR / "eval"
METADATA_PATH = ARTIFACTS_DIR / "metadata.json"
COLUMN_METADATA_PATH = ARTIFACTS_DIR / "column_metadata.json"


def load_similarity_module() -> ModuleType:
    for path in (ROOT / "src", ROOT / "scripts"):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.append(path_str)

    return import_module("find_dataset_similarity")


def eval_temporal_track(
    similarity_module: ModuleType, records: dict[str, dict], top_k: int
) -> None:
    """
    Evaluates Hit Rate @ K for temporal variants.
    A hit is when AT LEAST ONE of the known 'relevant_dataset_ids' appears in the top-K.
    """
    eval_file = EVAL_DIR / "temporal_pairs.json"
    if not eval_file.exists():
        print(f"Eval file {eval_file} not found.")
        return

    queries = similarity_module.load_json(eval_file)
    hits_heuristic = 0
    hits_embedding = 0
    total = len(queries)

    print(f"Evaluating Temporal Track ({total} queries, Top-{top_k})...")
    
    # Pre-build candidate list for heuristic search
    all_candidates = list(records.values())

    for q in queries:
        target_id = q["query_dataset_id"]
        relevant_ids = set(q["relevant_dataset_ids"])
        
        if target_id not in records:
            continue
            
        target_record = records[target_id]

        # 1. Test Heuristic (Column + Title + Temporal)
        heur_results = similarity_module.rank_candidates(target_record, all_candidates, top_k)
        heur_retrieved_ids = {r["dataset_id"] for r in heur_results}
        
        if heur_retrieved_ids & relevant_ids:
            hits_heuristic += 1
            
        # 2. Test Embedding Only (Qdrant)
        try:
            emb_results = similarity_module.rank_embedding_only_global(target_record, records, top_k)
            emb_retrieved_ids = {r["dataset_id"] for r in emb_results}
            
            if emb_retrieved_ids & relevant_ids:
                hits_embedding += 1
        except Exception:
            # If Qdrant isn't ready or fails
            pass

    print("-" * 40)
    print("Results: Temporal Variants (Similarity)")
    print(f"Hit Rate @ {top_k} (Heuristic): {hits_heuristic / total:.2%}")
    print(f"Hit Rate @ {top_k} (Embedding): {hits_embedding / total:.2%}")
    print("-" * 40)


def eval_schema_track(similarity_module: ModuleType, records: dict[str, dict], top_k: int) -> None:
    """
    Evaluates Precision/Recall for Joinability based on LLM labels.
    """
    eval_file = EVAL_DIR / "labeled_schema_pairs.json"
    if not eval_file.exists():
        print(f"Eval file {eval_file} not found. Run label_pairs_llm.py first.")
        return

    labeled_pairs = similarity_module.load_json(eval_file)
    
    # We want to see if the system ranks the 'joinable' pairs highly.
    # This is a bit different since our system currently ranks for "similarity".
    # But we can test if "similarity" correlates with "joinability".
    
    joinable_pairs = [p for p in labeled_pairs if p.get("joinable") is True]
    similar_pairs = [p for p in labeled_pairs if p.get("similar") is True]
    
    print(f"Loaded {len(labeled_pairs)} LLM-labeled pairs.")
    print(f"  - {len(joinable_pairs)} are Joinable")
    print(f"  - {len(similar_pairs)} are Similar")
    
    print("\nNote: The current agent is optimized for Similarity, not Joinability.")
    print("If it struggles with Joinable pairs, we need to build a separate Joinability scoring track (V2).")

    if not joinable_pairs:
        return

    hits = 0
    total = len(joinable_pairs)
    all_candidates = list(records.values())

    print(f"\nEvaluating Joinability Track ({total} targets, Top-{top_k})...")
    
    for q in joinable_pairs:
        target_id = q["dataset_a_id"]
        relevant_id = q["dataset_b_id"]
        
        if target_id not in records or relevant_id not in records:
            continue
            
        target_record = records[target_id]
        results = similarity_module.rank_candidates(target_record, all_candidates, top_k)
        
        result_ids = [r["dataset_id"] for r in results]
        if relevant_id in result_ids:
            hits += 1

    print("-" * 40)
    print("Results: Schema Variants (Joinability)")
    print(f"Hit Rate @ {top_k} (Semantic Columns): {hits / total:.2%}")
    print("-" * 40)

@click.command()
@click.option(
    "--track",
    type=click.Choice(["temporal", "schema", "all"], case_sensitive=False),
    default="all",
    show_default=True,
)
@click.option("--top-k", type=int, default=5, show_default=True)
def main(track: str, top_k: int) -> None:
    similarity_module = load_similarity_module()

    # Load system data
    similarity_module.load_column_embeddings()
    metadata = similarity_module.load_json(METADATA_PATH)
    col_metadata = similarity_module.load_json(COLUMN_METADATA_PATH)
    records = similarity_module.build_records(metadata, col_metadata)

    if track in ["temporal", "all"]:
        eval_temporal_track(similarity_module, records, top_k)
        
    if track in ["schema", "all"]:
        eval_schema_track(similarity_module, records, top_k)


if __name__ == "__main__":
    main()
