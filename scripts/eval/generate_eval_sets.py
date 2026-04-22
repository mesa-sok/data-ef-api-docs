#!/usr/bin/env python3
"""Generate candidate evaluation pairs for the Data EF agent."""

import json
import re
from pathlib import Path
from collections import defaultdict
from itertools import combinations

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = ROOT / "artifacts"
EVAL_DIR = ARTIFACTS_DIR / "eval"

def load_json(path: Path) -> list[dict]:
    if not path.exists():
        print(f"Warning: {path} not found.")
        return []
    return json.loads(path.read_text(encoding="utf-8"))

def normalize_title(title: str) -> str:
    text = title.lower()
    text = re.sub(r"\b\d{4}\s*-\s*\d{4}\b", " ", text)
    text = re.sub(r"\b(?:fy\s*)?\d{4}\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

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

def jaccard_similarity(set1: set, set2: set) -> float:
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / len(set1 | set2)

def generate_temporal_pairs(metadata: list[dict]):
    """Group datasets by normalized title to find temporal variants (e.g. 2023 vs 2024)."""
    groups = defaultdict(list)
    for ds in metadata:
        if not ds.get("name"):
            continue
        series_key = normalize_title(ds["name"])
        if series_key:
            groups[series_key].append({
                "id": ds["id"],
                "title": ds["name"]
            })
    
    # We only care about groups with more than 1 dataset
    eval_data = []
    for series_key, items in groups.items():
        if len(items) > 1:
            for item in items:
                relevant_ids = [other["id"] for other in items if other["id"] != item["id"]]
                eval_data.append({
                    "track": "temporal_variant",
                    "query_dataset_id": item["id"],
                    "query_title": item["title"],
                    "series_key": series_key,
                    "relevant_dataset_ids": relevant_ids,
                    "label_source": "rule_based"
                })
    return eval_data

def generate_schema_pairs(metadata: list[dict], column_metadata: list[dict]):
    """Find pairs of datasets with high column overlap but potentially different categories."""
    # Build dataset dictionary
    ds_map = {ds["id"]: ds for ds in metadata if "id" in ds}
    
    # Build normalized columns for each dataset
    ds_columns = {}
    for col_record in column_metadata:
        ds_id = col_record.get("id")
        if not ds_id or ds_id not in ds_map:
            continue
            
        columns = set()
        for col in col_record.get("columns", []):
            if isinstance(col, dict) and col.get("title"):
                # Use english columns where possible, ignore khmer only
                if not col["title"].endswith("_kh"):
                    columns.add(normalize_column(col["title"]))
        
        if columns:
            ds_columns[ds_id] = columns
            
    # Compare all pairs (this is O(N^2) but N=800 is very small)
    candidate_pairs = []
    ds_ids = list(ds_columns.keys())
    
    print(f"Comparing columns for {len(ds_ids)} datasets...")
    for i in range(len(ds_ids)):
        id_a = ds_ids[i]
        cols_a = ds_columns[id_a]
        
        for j in range(i+1, len(ds_ids)):
            id_b = ds_ids[j]
            cols_b = ds_columns[id_b]
            
            score = jaccard_similarity(cols_a, cols_b)
            
            # If schema overlaps significantly (>= 60%), it's a candidate
            if score >= 0.6:
                cat_a = {c.get("slug") for c in ds_map[id_a].get("categories", [])}
                cat_b = {c.get("slug") for c in ds_map[id_b].get("categories", [])}
                
                same_category = len(cat_a & cat_b) > 0
                
                candidate_pairs.append({
                    "dataset_a_id": id_a,
                    "dataset_a_title": ds_map[id_a].get("name"),
                    "dataset_b_id": id_b,
                    "dataset_b_title": ds_map[id_b].get("name"),
                    "jaccard_score": round(score, 3),
                    "shared_columns": list(cols_a & cols_b),
                    "same_category": same_category,
                    "needs_llm_label": True
                })
                
    # Sort by score descending
    candidate_pairs.sort(key=lambda x: x["jaccard_score"], reverse=True)
    return candidate_pairs

def main():
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    
    metadata = load_json(ARTIFACTS_DIR / "metadata.json")
    col_metadata = load_json(ARTIFACTS_DIR / "column_metadata.json")
    
    if not metadata or not col_metadata:
        print("Missing required artifacts. Exiting.")
        return
        
    print(f"Loaded {len(metadata)} metadata records and {len(col_metadata)} column records.")
    
    # 1. Temporal variants
    temporal_eval = generate_temporal_pairs(metadata)
    out_path = EVAL_DIR / "temporal_pairs.json"
    out_path.write_text(json.dumps(temporal_eval, indent=2, ensure_ascii=False))
    print(f"Wrote {len(temporal_eval)} temporal query cases to {out_path.relative_to(ROOT)}")
    
    # 2. Schema pairs
    schema_pairs = generate_schema_pairs(metadata, col_metadata)
    out_path = EVAL_DIR / "schema_pairs.json"
    out_path.write_text(json.dumps(schema_pairs, indent=2, ensure_ascii=False))
    print(f"Wrote {len(schema_pairs)} schema overlap pairs to {out_path.relative_to(ROOT)}")
    
    # Summary of schema pairs
    cross_cat = sum(1 for p in schema_pairs if not p["same_category"])
    print(f"  -> {cross_cat} pairs are from DIFFERENT categories (great for testing surprise joinability)")

if __name__ == "__main__":
    main()
