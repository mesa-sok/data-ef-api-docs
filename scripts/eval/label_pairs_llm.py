#!/usr/bin/env python3
"""
label_pairs_llm.py
------------------
Uses an LLM as a judge to evaluate dataset pairs for similarity and joinability.
Reads candidate pairs, queries the LLM, and writes back the labeled dataset.

Usage:
    uv run scripts/label_pairs_llm.py --limit 50
"""

import json
from pathlib import Path

import click
from dotenv import load_dotenv
from litellm import completion

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = ROOT / "artifacts"
EVAL_DIR = ARTIFACTS_DIR / "eval"

# You can change the model here. gpt-5.4-mini is fast and cost-effective.
JUDGE_MODEL = "openai/gpt-5.4-mini"


def load_json(path: Path) -> list[dict]:
    if not path.exists():
        print(f"Warning: {path} not found.")
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_pair_with_llm(pair: dict) -> dict:
    """Ask the LLM to act as a judge and determine similarity and joinability."""
    prompt = f"""You are a data expert evaluating two datasets from the Cambodian Ministry of Economy and Finance.
    
Dataset A: "{pair['dataset_a_title']}"
Dataset B: "{pair['dataset_b_title']}"

These datasets share the following normalized columns:
{", ".join(pair['shared_columns'])}

Are these two datasets:
1. Thematically similar? (Do they cover the same general topic or domain?)
2. Joinable? (Do they share a strong entity or geographic key that would allow joining them for analysis? Note: just sharing 'year' or 'month' is a weak join key. 'province' or 'country' is strong.)

Respond with a JSON object exactly like this:
{{
    "similar": true/false,
    "joinable": true/false,
    "reasoning": "Brief explanation of your decision (max 2 sentences)."
}}
"""
    try:
        response = completion(
            model=JUDGE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=1.0,  # GPT-5.4 models typically require temperature=1
            reasoning_effort="low",
        )
        result_text = response.choices[0].message.content
        return json.loads(result_text)
    except Exception as e:
        print(f"Error evaluating pair {pair['dataset_a_id']} vs {pair['dataset_b_id']}: {e}")
        return {"similar": False, "joinable": False, "reasoning": f"Error: {e}"}


@click.command()
@click.option("--limit", type=int, default=10, show_default=True, help="Number of pairs to evaluate")
def main(limit: int) -> None:
    input_file = EVAL_DIR / "schema_pairs.json"
    output_file = EVAL_DIR / "labeled_schema_pairs.json"

    pairs = load_json(input_file)
    if not pairs:
        print("No pairs to evaluate. Run generate_eval_sets.py first.")
        return

    # Focus on cross-category pairs first as they are the most interesting for joinability
    interesting_pairs = [p for p in pairs if not p.get("same_category")]
    if not interesting_pairs:
        interesting_pairs = pairs

    sample = interesting_pairs[:limit]
    print(f"Evaluating {len(sample)} pairs using {JUDGE_MODEL}...")

    labeled_results = []
    for i, pair in enumerate(sample, 1):
        print(f"[{i}/{len(sample)}] Evaluating: '{pair['dataset_a_title']}' vs '{pair['dataset_b_title']}'")
        llm_judgment = evaluate_pair_with_llm(pair)
        
        # Merge the LLM judgment into the original pair data
        labeled_pair = {**pair, **llm_judgment, "label_source": f"llm_{JUDGE_MODEL}"}
        labeled_pair.pop("needs_llm_label", None)
        labeled_results.append(labeled_pair)

    # Save results
    output_file.write_text(json.dumps(labeled_results, indent=2, ensure_ascii=False))
    print(f"\nSaved {len(labeled_results)} labeled pairs to {output_file.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
