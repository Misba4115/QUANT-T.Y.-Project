"""
Benchmark: RAG Retrieval Quality (Recall@k, MRR)
==================================================
Runs each question from rag_retrieval_test_set.json through the project's
PublicKnowledgeService retriever, checks whether the expected chunk appears
in the top-k results, and computes:
  - Recall@1, Recall@3, Recall@5
  - Mean Reciprocal Rank (MRR)

Results are written to results/rag_retrieval_results.json

HOW TO RUN (from the repo root — Qdrant + embedder must be available):
    python benchmarking/bench_rag_retrieval.py

PREREQUISITES:
  1. Your Qdrant instance must be running and the knowledge base must be
     ingested (run the ingest script / admin endpoint first).
  2. The environment variables used by services/qdrant_rag_service.py must
     be set (QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION, etc.).
  3. pip install sentence-transformers qdrant-client

IMPORTANT -- Fill in expected_source_chunk_id FIRST:
  The test set ships with `expected_source_chunk_id = "FILL_IN_FROM_YOUR_ACTUAL_CORPUS"`
  as a placeholder.  Before running this benchmark, open rag_retrieval_test_set.json,
  retrieve each question manually (or via your UI), identify the best-matching
  chunk ID in Qdrant, and fill in those IDs.  The script will skip (and flag)
  any questions that still have the placeholder value.

HOW chunk IDs are matched:
  The retriever returns `citation_id` in the format "public:<uuid>".
  The expected_source_chunk_id should be that exact string, e.g.
  "public:3f7a1c2b-...".
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# -- Adjust path so we can import from backend --------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND))

# Load .env if present (useful when running outside Docker)
env_path = BACKEND / ".env"
if env_path.exists():
    with open(env_path) as _fenv:
        for _line in _fenv:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip())

from services.qdrant_rag_service import PublicKnowledgeService  # noqa: E402

# -- File paths ---------------------------------------------------------------
TEST_SET_PATH = Path(__file__).parent / "rag_retrieval_test_set.json"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_PATH = RESULTS_DIR / "rag_retrieval_results.json"

PLACEHOLDER = "FILL_IN_FROM_YOUR_ACTUAL_CORPUS"
K_VALUES = [1, 3, 5]


# -- Metrics ------------------------------------------------------------------

def reciprocal_rank(ranked_ids: list[str], target_id: str) -> float:
    for rank, cid in enumerate(ranked_ids, start=1):
        if cid == target_id:
            return 1.0 / rank
    return 0.0


def recall_at_k(ranked_ids: list[str], target_id: str, k: int) -> bool:
    return target_id in ranked_ids[:k]


# -- Main ---------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("BENCHMARK: RAG Retrieval Quality")
    print("=" * 60)

    with open(TEST_SET_PATH, encoding="utf-8") as f:
        test_set = json.load(f)

    questions = test_set["questions"]
    print(f"\nLoaded {len(questions)} questions.\n")

    # Init retriever (will fail fast if Qdrant is not reachable)
    try:
        retriever = PublicKnowledgeService()
    except Exception as exc:
        print(f"ERROR: Could not connect to Qdrant — {type(exc).__name__}: {exc}")
        print("Make sure Qdrant is running and the knowledge base is ingested.")
        sys.exit(1)

    results = []
    skipped = 0
    rr_scores: list[float] = []
    recall_hits: dict[int, int] = {k: 0 for k in K_VALUES}
    evaluated = 0

    print(f"{'ID':<10} {'Topic':<35} {'RR':>6} {'R@1':>5} {'R@3':>5} {'R@5':>5}  Status")
    print("-" * 75)

    for q in questions:
        qid = q["question_id"]
        question = q["question"]
        expected_id = q.get("expected_source_chunk_id", PLACEHOLDER)
        topic = q.get("topic", "")[:34]

        if expected_id == PLACEHOLDER:
            print(f"{qid:<10} {topic:<35} {'N/A':>6} {'N/A':>5} {'N/A':>5} {'N/A':>5}  SKIPPED (fill chunk ID)")
            skipped += 1
            results.append(
                {
                    "question_id": qid,
                    "question": question,
                    "topic": q.get("topic"),
                    "expected_chunk_id": expected_id,
                    "status": "skipped_placeholder",
                    "retrieved_ids": [],
                    "reciprocal_rank": None,
                    "recall_at_1": None,
                    "recall_at_3": None,
                    "recall_at_5": None,
                }
            )
            continue

        # Retrieve top-5
        try:
            hits = retriever.search(question, limit=5)
        except Exception as exc:
            print(f"{qid:<10} {topic:<35}  ERROR: {type(exc).__name__}: {exc}")
            results.append(
                {
                    "question_id": qid,
                    "question": question,
                    "topic": q.get("topic"),
                    "expected_chunk_id": expected_id,
                    "status": "retrieval_error",
                    "error": str(exc),
                    "retrieved_ids": [],
                    "reciprocal_rank": None,
                    "recall_at_1": None,
                    "recall_at_3": None,
                    "recall_at_5": None,
                }
            )
            continue

        ranked_ids = [h["citation_id"] for h in hits]
        rr = reciprocal_rank(ranked_ids, expected_id)
        recalls = {k: recall_at_k(ranked_ids, expected_id, k) for k in K_VALUES}

        rr_scores.append(rr)
        for k in K_VALUES:
            if recalls[k]:
                recall_hits[k] += 1
        evaluated += 1

        r_str = {k: "Y" if recalls[k] else "N" for k in K_VALUES}
        print(
            f"{qid:<10} {topic:<35} {rr:>6.4f} {r_str[1]:>5} {r_str[3]:>5} {r_str[5]:>5}  "
            f"{'FOUND' if rr > 0 else 'MISS'}"
        )

        results.append(
            {
                "question_id": qid,
                "question": question,
                "topic": q.get("topic"),
                "expected_chunk_id": expected_id,
                "status": "evaluated",
                "retrieved_ids": ranked_ids,
                "top_results": [
                    {"rank": i + 1, "id": h["citation_id"], "title": h.get("title"), "score": h.get("similarity")}
                    for i, h in enumerate(hits)
                ],
                "reciprocal_rank": rr,
                "recall_at_1": recalls[1],
                "recall_at_3": recalls[3],
                "recall_at_5": recalls[5],
            }
        )

    # -- Aggregate metrics ------------------------------------------------
    mrr = round(sum(rr_scores) / len(rr_scores), 4) if rr_scores else 0.0
    recall_at = {k: round(recall_hits[k] / evaluated, 4) if evaluated > 0 else 0.0 for k in K_VALUES}

    print(f"\nEvaluated: {evaluated}/{len(questions)} questions  (skipped {skipped} with placeholder IDs)")
    print(f"\n{'Metric':<20} {'Value':>8}")
    print("-" * 30)
    print(f"{'MRR':<20} {mrr:>8.4f}")
    for k in K_VALUES:
        print(f"{'Recall@' + str(k):<20} {recall_at[k]:>8.4f}")

    # -- Write results --------------------------------------------------------
    RESULTS_DIR.mkdir(exist_ok=True)
    output = {
        "component": "rag_retrieval",
        "total_questions": len(questions),
        "evaluated": evaluated,
        "skipped": skipped,
        "metrics": {
            "mrr": mrr,
            "recall_at_1": recall_at[1],
            "recall_at_3": recall_at[3],
            "recall_at_5": recall_at[5],
        },
        "questions": results,
    }
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResults written to: {RESULTS_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
