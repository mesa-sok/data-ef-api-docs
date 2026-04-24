#!/usr/bin/env python3
"""
generate_dataset_questions.py
-----------------------------
Data pipeline that uses GPT-5.4-mini (via LiteLLM) to generate diverse
evaluation questions for every dataset in ``artifacts/metadata.json``.

Design goals
~~~~~~~~~~~~
* At least ``--min-questions`` questions per dataset (default: 10).
* Datasets are processed in batches of ``--batch-size`` (default: 5) per LLM
  call so a single request covers multiple datasets and amortises the system
  prompt.
* To save tokens, each dataset is referenced in the prompt/response by a
  short MD5-derived id (first 12 hex chars of ``md5(dataset_id)``) instead of
  its full verbose slug. The LLM's structured output therefore only contains
  ``{id, questions}`` pairs. The full dataset identifier is re-linked
  client-side via an id map persisted alongside the output.
* Resume-friendly: already-processed short ids are tracked in a checkpoint
  file so repeated runs skip work that is already done.

Outputs (under ``artifacts/eval/``)
-----------------------------------
``dataset_questions.json``
    List of ``{id, dataset_id, name, questions}`` records — the fully linked
    output that downstream eval scripts should consume.

``dataset_id_map.json``
    Mapping ``short_id -> {dataset_id, name}``. This is the lookup table that
    re-links the token-saving ``id`` field back to the real dataset.

``questions_checkpoint.json``
    Sorted list of short ids already generated. Used for ``--resume``.

Usage
-----
::

    uv run scripts/eval/generate_dataset_questions.py
    uv run scripts/eval/generate_dataset_questions.py --limit 20
    uv run scripts/eval/generate_dataset_questions.py --batch-size 5 --min-questions 12

Environment
-----------
``OPENAI_API_KEY`` — required for the ``openai/gpt-5.4-mini`` route via
LiteLLM. Loaded from ``.env`` if present.

``QUESTION_MODEL`` — optional override for the LLM route (defaults to
``openai/gpt-5.4-mini``, matching ``scripts/eval/label_pairs_llm.py``).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import click
from dotenv import load_dotenv
from litellm import completion
from pydantic import BaseModel, Field

load_dotenv()


# ---------------------------------------------------------------------------
# Pydantic models for the LLM's structured output
# ---------------------------------------------------------------------------


class DatasetQuestions(BaseModel):
    """Questions generated for a single dataset, keyed by its short md5 id."""

    id: str = Field(
        ...,
        description=("Short md5-derived dataset id, echoed verbatim from the input prompt."),
    )
    questions: list[str] = Field(
        default_factory=list,
        description="Natural-language evaluation questions for this dataset.",
    )


class QuestionBatchResponse(BaseModel):
    """Top-level structured output returned by the LLM for one batch."""

    results: list[DatasetQuestions] = Field(
        default_factory=list,
        description="One entry per dataset in the batch, in any order.",
    )


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_DIR = ROOT / "artifacts"
EVAL_DIR = ARTIFACTS_DIR / "eval"
METADATA_FILE = ARTIFACTS_DIR / "metadata.json"

OUTPUT_FILE = EVAL_DIR / "dataset_questions.json"
ID_MAP_FILE = EVAL_DIR / "dataset_id_map.json"
CHECKPOINT_FILE = EVAL_DIR / "questions_checkpoint.json"

DEFAULT_MODEL = os.environ.get("QUESTION_MODEL", "openai/gpt-5.4-mini")
SHORT_ID_LEN = 12  # hex chars of md5 — 48 bits, collision-safe for <1M ids


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def short_id_for(dataset_id: str, length: int = SHORT_ID_LEN) -> str:
    """Return the first ``length`` hex chars of md5(dataset_id)."""
    return hashlib.md5(dataset_id.encode("utf-8")).hexdigest()[:length]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def build_id_map(datasets: list[dict]) -> dict[str, dict[str, str]]:
    """Build ``short_id -> {dataset_id, name}`` and fail fast on collisions."""
    id_map: dict[str, dict[str, str]] = {}
    for ds in datasets:
        ds_id = ds.get("id")
        if not ds_id:
            continue
        sid = short_id_for(ds_id)
        if sid in id_map and id_map[sid]["dataset_id"] != ds_id:
            raise RuntimeError(
                f"MD5 short-id collision at {SHORT_ID_LEN} hex chars: "
                f"{sid} -> {id_map[sid]['dataset_id']} and {ds_id}. "
                "Increase SHORT_ID_LEN."
            )
        id_map[sid] = {"dataset_id": ds_id, "name": ds.get("name", "") or ""}
    return id_map


def summarise_dataset(ds: dict) -> dict[str, Any]:
    """Return the minimal dataset payload sent to the LLM."""
    categories = [c.get("name_en") for c in ds.get("categories") or [] if c.get("name_en")]
    org = ds.get("organization") or {}
    return {
        "name": ds.get("name") or "",
        "description": ds.get("description") or "",
        "organization": org.get("name_en") or org.get("abbreviation") or "",
        "categories": categories,
        "frequency": ds.get("frequency") or "",
        "coverage_start": ds.get("coverage_start") or "",
        "coverage_end": ds.get("coverage_end") or "",
    }


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an analyst generating evaluation questions for a\
 semantic search system over Cambodian Ministry of Economy and Finance open\
 datasets. For each dataset provided, write diverse, realistic questions a\
 journalist, researcher, or policy analyst would ask that the dataset can\
 plausibly answer. Mix granularities: definitional, aggregate, comparative,\
 temporal, and geographic. Each question must be self-contained and\
 phrased in natural English.

Return ONLY a JSON object matching this schema:
{
  "results": [
    {"id": "<short_id>", "questions": ["q1", "q2", ...]}
  ]
}

Rules:
- Preserve every ``id`` exactly as provided; do not invent new ids.
- Provide at least ``min_questions`` questions per dataset.
- Do not repeat questions within a dataset.
- Do not include the dataset name verbatim inside every question.
- Do not add any prose outside the JSON object."""


def build_user_prompt(batch: list[tuple[str, dict]], min_questions: int) -> str:
    payload = {
        "min_questions": min_questions,
        "datasets": [{"id": sid, **summarise_dataset(ds)} for sid, ds in batch],
    }
    return (
        f"Generate at least {min_questions} evaluation questions for each of the "
        f"following {len(batch)} datasets. Use the short ``id`` field verbatim "
        f"in your response.\n\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )


def call_llm(
    batch: list[tuple[str, dict]],
    *,
    model: str,
    min_questions: int,
    max_retries: int,
) -> dict[str, list[str]]:
    """Call the LLM once for a batch, returning ``{short_id: [questions]}``.

    The LLM response is parsed into :class:`QuestionBatchResponse` (Pydantic v2)
    so downstream code works with typed objects instead of raw dicts. We pass
    the Pydantic model as ``response_format`` which LiteLLM converts to the
    provider's structured-output schema when supported.
    """
    user_prompt = build_user_prompt(batch, min_questions)
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = completion(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=QuestionBatchResponse,
                temperature=1.0,  # GPT-5.4 models typically require temperature=1
                reasoning_effort="low",
            )
            raw = response.choices[0].message.content or ""
            parsed = QuestionBatchResponse.model_validate_json(raw)

            # Map results by id; fall back to positional alignment if the LLM
            # dropped/renamed ids so we still get partial progress.
            by_id: dict[str, list[str]] = {}
            expected_ids = [sid for sid, _ in batch]
            for idx, item in enumerate(parsed.results):
                rid = item.id
                if rid not in expected_ids and idx < len(expected_ids):
                    rid = expected_ids[idx]
                # De-duplicate while preserving order; drop blanks.
                seen: set[str] = set()
                unique: list[str] = []
                for q in item.questions:
                    text = q.strip()
                    if not text:
                        continue
                    key = text.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    unique.append(text)
                if rid:
                    by_id[rid] = unique
            return by_id
        except Exception as exc:  # noqa: BLE001 — retry on any LLM/parse failure
            last_error = exc
            wait = 2 ** (attempt - 1)
            print(
                f"  ! LLM attempt {attempt}/{max_retries} failed: {exc!s}. Retrying in {wait}s...",
                file=sys.stderr,
            )
            time.sleep(wait)
    assert last_error is not None
    raise last_error


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def chunked(seq: list, size: int):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


@click.command(context_settings={"show_default": True})
@click.option("--limit", type=int, default=None, help="Max datasets to process.")
@click.option("--batch-size", type=int, default=5, help="Datasets per LLM call.")
@click.option(
    "--min-questions",
    type=int,
    default=10,
    help="Minimum questions per dataset.",
)
@click.option(
    "--model",
    default=DEFAULT_MODEL,
    help="LiteLLM model route (env: QUESTION_MODEL).",
)
@click.option(
    "--resume/--no-resume",
    default=True,
    help="Skip datasets already in the checkpoint file.",
)
@click.option(
    "--max-retries",
    type=int,
    default=3,
    help="Max retries per batch on LLM / JSON errors.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print the first batch prompt and exit without calling the LLM.",
)
def main(
    limit: int | None,
    batch_size: int,
    min_questions: int,
    model: str,
    resume: bool,
    max_retries: int,
    dry_run: bool,
) -> None:
    if batch_size < 1:
        raise click.BadParameter("--batch-size must be >= 1")
    if min_questions < 1:
        raise click.BadParameter("--min-questions must be >= 1")

    # ------------------------------------------------------------------
    # Load datasets
    # ------------------------------------------------------------------
    if not METADATA_FILE.exists():
        raise click.ClickException(
            f"{METADATA_FILE} not found. Run scripts/harvest/fetch_all_datasets.py first."
        )
    datasets: list[dict] = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    datasets = [ds for ds in datasets if ds.get("id")]
    if limit is not None:
        datasets = datasets[:limit]
    print(f"Loaded {len(datasets)} datasets from {METADATA_FILE.relative_to(ROOT)}")

    id_map = build_id_map(datasets)
    save_json(ID_MAP_FILE, id_map)

    # ------------------------------------------------------------------
    # Resume
    # ------------------------------------------------------------------
    already_done: set[str] = set(load_json(CHECKPOINT_FILE, []))
    existing_results: list[dict] = load_json(OUTPUT_FILE, [])
    existing_by_id = {r["id"]: r for r in existing_results if "id" in r}

    pending: list[tuple[str, dict]] = []
    for ds in datasets:
        sid = short_id_for(ds["id"])
        if resume and sid in already_done:
            continue
        pending.append((sid, ds))

    print(
        f"{len(pending)} datasets to process "
        f"({len(already_done)} already done; batch_size={batch_size}, "
        f"min_questions={min_questions}, model={model})"
    )
    if not pending:
        print("Nothing to do.")
        return

    # ------------------------------------------------------------------
    # Dry run
    # ------------------------------------------------------------------
    if dry_run:
        first_batch = pending[:batch_size]
        print("--- SYSTEM PROMPT ---")
        print(SYSTEM_PROMPT)
        print("\n--- USER PROMPT (first batch) ---")
        print(build_user_prompt(first_batch, min_questions))
        return

    # ------------------------------------------------------------------
    # Batch processing
    # ------------------------------------------------------------------
    total_batches = (len(pending) + batch_size - 1) // batch_size
    for batch_idx, batch in enumerate(chunked(pending, batch_size), 1):
        titles = ", ".join(ds.get("name", "<no-name>")[:40] for _, ds in batch)
        print(f"[{batch_idx}/{total_batches}] Generating for: {titles}")

        by_id = call_llm(
            batch,
            model=model,
            min_questions=min_questions,
            max_retries=max_retries,
        )

        for sid, ds in batch:
            questions = by_id.get(sid, [])
            if len(questions) < min_questions:
                print(
                    f"  ! {sid} ({ds.get('name', '')[:60]}) returned "
                    f"{len(questions)} questions (<{min_questions}); keeping partial.",
                    file=sys.stderr,
                )
            record = {
                "id": sid,
                "dataset_id": ds["id"],
                "name": ds.get("name") or "",
                "questions": questions,
            }
            existing_by_id[sid] = record
            already_done.add(sid)

        # Persist after every batch so crashes don't lose work.
        save_json(OUTPUT_FILE, list(existing_by_id.values()))
        save_json(CHECKPOINT_FILE, sorted(already_done))

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    all_records = list(existing_by_id.values())
    total_questions = sum(len(r["questions"]) for r in all_records)
    short_records = [r for r in all_records if len(r["questions"]) < min_questions]
    print()
    print("=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Datasets with questions : {len(all_records)}")
    print(f"  Total questions         : {total_questions}")
    print(f"  Datasets below minimum  : {len(short_records)} (min_questions={min_questions})")
    print(f"  Output                  : {OUTPUT_FILE.relative_to(ROOT)}")
    print(f"  Id map                  : {ID_MAP_FILE.relative_to(ROOT)}")
    print(f"  Checkpoint              : {CHECKPOINT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
