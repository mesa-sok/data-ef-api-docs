from pathlib import Path
import json
import sys

# Resolve project root relative to this script
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from data_ef_api import DataEFClient
# import CategoryOption
from data_ef_api.models import CategoryOption
from typing import List
import datetime
from datetime import datetime, timezone 

# Resolve project root relative to this script
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from data_ef_api import DataEFClient

with DataEFClient(verify=False) as client:
    print("Fetching filter options....")
    options = client.get_filter_options()
    
categories: List[CategoryOption] = options.categories or []

# sorted the categories by dataset_count
categories_sorted = sorted(categories, key=lambda c: (c.dataset_count or 0), reverse=True)

print(f"\n{'#':<4} {'Slug (value)':<45} {'Datasets':<10} English Name")
print("-" * 85)
for i, cat in enumerate(categories_sorted, start=1):
    print(
        f"{i:<4} {cat.value or '?':<45} "
        f"{cat.dataset_count or 0:<10} {cat.label_en or 'Unknown'}"
    )
print(f"\nTotal categories: {len(categories)}")

fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

payload = {
    "fetched_at": fetched_at,
    "total": len(categories),
    "categories": [cat.model_dump() for cat in categories_sorted] 
}

timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
output_dir = Path("artifacts")
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / f"categories_{timestamp}.json"

with open(output_file, "w", encoding="utf-8") as f:
   json.dump(payload, f, indent=2, ensure_ascii=False)

print(f"\nSaved to: {output_file} (fetched_at: {fetched_at})")







