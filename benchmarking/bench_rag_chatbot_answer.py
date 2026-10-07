"""
Benchmark: RAG Chatbot Answer Quality
======================================

Runs the full ChatOrchestrator pipeline against 50 benchmark questions
and evaluates:

1. Fact-check accuracy against expected_answer_facts
2. RAGAS:
   - faithfulness
   - answer_relevancy
   - context_precision
3. Grounding checker correction rate
4. Chatbot errors
5. Retrieved citations/context

Run from the benchmarking directory:
    python bench_rag_chatbot_answer.py

NOTE: Uses db.supabase_client (the actual DB module in this project).
"""

from __future__ import annotations

import json
import os
import re
import sys
import traceback
from pathlib import Path
from typing import Any

# Force UTF-8 output on Windows cmd to prevent UnicodeEncodeError from emoji
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ============================================================================
# PATH SETUP — add backend/ so all project imports resolve
# ============================================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"

sys.path.insert(0, str(BACKEND))


# ============================================================================
# LOAD .ENV from backend/.env
# ============================================================================

env_path = BACKEND / ".env"

if env_path.exists():

    with open(env_path, encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            if (
                line
                and not line.startswith("#")
                and "=" in line
            ):

                key, _, value = line.partition("=")

                os.environ.setdefault(
                    key.strip(),
                    value.strip(),
                )


# ============================================================================
# FILE PATHS
# ============================================================================

CHATBOT_TEST_SET_PATH = (
    Path(__file__).parent
    / "rag_chatbot_answer_test_set.json"
)

REFERENCE_PROFILE_PATH = (
    Path(__file__).parent
    / "reference_user_profile.json"
)

RESULTS_DIR = (
    Path(__file__).parent
    / "results"
)

RESULTS_PATH = (
    RESULTS_DIR
    / "rag_chatbot_answer_results.json"
)


# ============================================================================
# CONFIGURATION
# ============================================================================

BENCH_USER_ID = "bench_test_user"

# IMPORTANT:
# False = use the database as-is.
# True = insert/update the basic user profile before testing.
#
# NOTE:
# The current seed function only seeds the users table.
# It does NOT automatically create holdings/transactions.
SEED_BEFORE_RUN = False

# The real LLM must be called for a meaningful benchmark.
DRY_RUN = False

# RAGAS evaluation — DISABLED: current langchain version is missing
# langchain_community.chat_models.vertexai which RAGAS imports internally.
# Re-enable once ragas is updated or langchain-community is pinned.
RAGAS_ENABLED = False

# Timeout (seconds) per chatbot call — prevents Gemini API from hanging.
CHATBOT_TIMEOUT_SECONDS = 30

# Print the actual chatbot answer for every question.
PRINT_ANSWERS = True

# Print full citations for debugging.
PRINT_CITATIONS = False


# ============================================================================
# FACT CHECK
# ============================================================================

def near_match_facts(
    answer: str,
    expected_facts: list[str],
) -> tuple[bool, list[str], list[str]]:
    """
    Check whether expected facts appear in the chatbot answer.

    A fact is considered matched if at least one meaningful token/value
    from the expected fact appears in the answer.
    """

    answer_norm = re.sub(
        r"[₹,\s]",
        "",
        answer.lower(),
    )

    matched: list[str] = []
    missed: list[str] = []

    for fact in expected_facts:

        fact_norm = re.sub(
            r"[₹,\s]",
            "",
            fact.lower(),
        )

        # Numbers
        numbers = re.findall(
            r"\d+(?:\.\d+)?",
            fact_norm,
        )

        # Dates
        dates = re.findall(
            r"\d{4}-\d{2}-\d{2}",
            fact,
        )

        # Meaningful words
        words = [
            word
            for word in re.split(
                r"[\s,.()\-]",
                fact.lower(),
            )
            if len(word) > 3
            and not word.isdigit()
        ]

        tokens_to_check = (
            numbers
            + dates
            + words
        )

        if any(
            token
            and token in answer_norm
            for token in tokens_to_check
        ):

            matched.append(fact)

        else:

            missed.append(fact)

    return (
        len(missed) == 0,
        matched,
        missed,
    )


# ============================================================================
# RAGAS
# ============================================================================

def run_ragas(
    question: str,
    answer: str,
    contexts: list[str],
) -> dict[str, float | None]:

    if not RAGAS_ENABLED:

        return {
            "faithfulness": None,
            "answer_relevancy": None,
            "context_precision": None,
            "ragas_error": "RAGAS disabled",
        }

    # ---------------------------------------------------------------
    # Import RAGAS
    # ---------------------------------------------------------------

    try:

        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            faithfulness,
        )

    except Exception as exc:

        error = (
            f"{type(exc).__name__}: {exc}"
        )

        print(
            f"         RAGAS ERROR: {error}"
        )

        return {
            "faithfulness": None,
            "answer_relevancy": None,
            "context_precision": None,
            "ragas_error": error,
        }

    # ---------------------------------------------------------------
    # Run RAGAS
    # ---------------------------------------------------------------

    try:

        data = {
            "question": [question],
            "answer": [answer],
            "contexts": [
                contexts
                if contexts
                else ["No context retrieved."]
            ],

            # Keep the benchmark's existing evaluation setup.
            "ground_truth": [question],
        }

        dataset = Dataset.from_dict(data)

        result = evaluate(
            dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
            ],
        )

        scores = (
            result
            .to_pandas()
            .iloc[0]
        )

        return {
            "faithfulness": round(
                float(
                    scores.get(
                        "faithfulness",
                        0,
                    )
                    or 0
                ),
                4,
            ),

            "answer_relevancy": round(
                float(
                    scores.get(
                        "answer_relevancy",
                        0,
                    )
                    or 0
                ),
                4,
            ),

            "context_precision": round(
                float(
                    scores.get(
                        "context_precision",
                        0,
                    )
                    or 0
                ),
                4,
            ),
        }

    except Exception as exc:

        error = (
            f"{type(exc).__name__}: {exc}"
        )

        print(
            f"         RAGAS ERROR: {error}"
        )

        return {
            "faithfulness": None,
            "answer_relevancy": None,
            "context_precision": None,
            "ragas_error": error,
        }


# ============================================================================
# DATABASE CHECK
# ============================================================================

def check_database() -> tuple[Any | None, str | None]:
    """Connect using the actual db module: db.supabase_client."""

    try:

        from db.supabase_client import get_supabase_client

        db = get_supabase_client()

        # Quick connectivity check — will raise if credentials are wrong
        db.table("users").select("user_id").limit(1).execute()

        return db, None

    except Exception as exc:

        return (
            None,
            f"{type(exc).__name__}: {exc}",
        )


# ============================================================================
# SEED BASIC USER PROFILE
# ============================================================================

def seed_reference_profile(
    profile: dict,
    user_id: str,
    db: Any,
) -> bool:

    try:

        profile_data = profile["profile"]

        db.table("users").upsert(
            {
                "user_id": user_id,
                "risk_profile": profile_data[
                    "risk_profile"
                ],
                "monthly_income": (
                    profile_data[
                        "annual_income"
                    ]
                    // 12
                ),
            }
        ).execute()

        print(
            f"  Seeded basic user profile "
            f"for user_id={user_id!r}"
        )

        print(
            "  WARNING: This only seeds the users "
            "table. Holdings/transactions must already "
            "exist in the benchmark database."
        )

        return True

    except Exception as exc:

        print(
            "  SEED ERROR: "
            f"{type(exc).__name__}: {exc}"
        )

        traceback.print_exc()

        return False


# ============================================================================
# OPTIONAL DATABASE USER CHECK
# ============================================================================

def check_benchmark_user(
    db: Any,
    user_id: str,
) -> dict[str, Any]:

    result = {
        "user_lookup_attempted": True,
        "user_exists": None,
        "user_lookup_error": None,
    }

    try:

        response = (
            db.table("users")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        rows = response.data or []

        result["user_exists"] = len(rows) > 0

        if rows:

            print(
                f"Database user check: FOUND "
                f"{user_id!r}"
            )

        else:

            print(
                f"Database user check: NOT FOUND "
                f"{user_id!r}"
            )

    except Exception as exc:

        error = (
            f"{type(exc).__name__}: {exc}"
        )

        result["user_lookup_error"] = error

        print(
            f"Database user check ERROR: {error}"
        )

    return result


# ============================================================================
# CHATBOT
# ============================================================================

def run_chatbot(
    user_id: str,
    question: str,
    dry_run: bool,
) -> dict[str, Any]:

    if dry_run:

        return {
            "reply": (
                f"[DRY RUN] Stub answer for: "
                f"{question}"
            ),
            "citations": [],
            "warnings": [],
            "errors": [],
            "_dry_run": True,
        }

    try:

        import signal
        from agents.chat_orchestrator import (
            ChatOrchestrator,
        )
        from db.supabase_client import get_supabase_client

        db = get_supabase_client()

        orchestrator = ChatOrchestrator(db)

        # Run with a thread-based timeout to prevent Gemini API hangs
        import threading
        result_box: list = [None]
        error_box: list = [None]

        def _run():
            try:
                result_box[0] = orchestrator.run(
                    user_id=user_id,
                    user_message=question,
                    conversation_id="bench_session",
                )
            except Exception as exc:
                error_box[0] = exc

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=CHATBOT_TIMEOUT_SECONDS)

        if t.is_alive():
            return {
                "reply": "",
                "citations": [],
                "warnings": [],
                "errors": [f"TIMEOUT after {CHATBOT_TIMEOUT_SECONDS}s — Gemini API did not respond"],
                "_timeout": True,
            }

        if error_box[0] is not None:
            raise error_box[0]

        response = result_box[0]

        # Make sure we always return a dictionary.
        if not isinstance(response, dict):

            return {
                "reply": str(response),
                "citations": [],
                "warnings": [],
                "errors": [
                    "ChatOrchestrator returned "
                    "a non-dict response."
                ],
            }

        return response

    except Exception as exc:

        error = (
            f"{type(exc).__name__}: {exc}"
        )

        return {
            "reply": "",
            "citations": [],
            "warnings": [],
            "errors": [error],
            "_error": error,
        }


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:

    print("=" * 60)
    print("BENCHMARK: RAG Chatbot Answer Quality")
    print("=" * 60)

    print(
        f"\nBenchmark user ID : {BENCH_USER_ID}"
    )

    print(
        f"DRY_RUN           : {DRY_RUN}"
    )

    print(
        f"RAGAS enabled     : {RAGAS_ENABLED}"
    )

    print(
        f"Seed before run   : {SEED_BEFORE_RUN}"
    )

    # ------------------------------------------------------------------------
    # Check benchmark files
    # ------------------------------------------------------------------------

    if not CHATBOT_TEST_SET_PATH.exists():

        print(
            f"\nERROR: Test set not found:\n"
            f"{CHATBOT_TEST_SET_PATH}"
        )

        return

    if not REFERENCE_PROFILE_PATH.exists():

        print(
            f"\nERROR: Reference profile not found:\n"
            f"{REFERENCE_PROFILE_PATH}"
        )

        return

    # ------------------------------------------------------------------------
    # Load test set
    # ------------------------------------------------------------------------

    with open(
        CHATBOT_TEST_SET_PATH,
        encoding="utf-8",
    ) as f:

        test_set = json.load(f)

    with open(
        REFERENCE_PROFILE_PATH,
        encoding="utf-8",
    ) as f:

        reference_profile = json.load(f)

    questions = test_set["questions"]

    print(
        f"\nLoaded {len(questions)} questions."
    )

    print(
        f"Reference user: "
        f"{reference_profile['profile']['name']}"
    )

    # ------------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------------

    db, db_error = check_database()

    if db_error:

        print(
            "[FAIL] DATABASE CONNECTION FAILED"
        )

        print(
            f"   {db_error}"
        )

        print(
            "\nThe chatbot benchmark cannot "
            "work without the database."
        )

        return

    print(
        "\nDatabase connection: OK"
    )

    # ------------------------------------------------------------------------
    # Optional seed
    # ------------------------------------------------------------------------

    if SEED_BEFORE_RUN:

        print(
            "\nSeeding benchmark user..."
        )

        seed_reference_profile(
            reference_profile,
            BENCH_USER_ID,
            db,
        )

    # ------------------------------------------------------------------------
    # Verify benchmark user
    # ------------------------------------------------------------------------

    print(
        "\nChecking benchmark user..."
    )

    user_check = check_benchmark_user(
        db,
        BENCH_USER_ID,
    )

    if user_check["user_exists"] is False:

        print(
            "\n[WARN] WARNING:"
        )

        print(
            f"User {BENCH_USER_ID!r} "
            "does not exist in the database."
        )

        print(
            "The chatbot will probably not be able "
            "to retrieve portfolio/transaction data."
        )

    # ------------------------------------------------------------------------
    # Counters
    # ------------------------------------------------------------------------

    results: list[dict] = []

    grounding_corrections = 0

    fact_all_matched = 0

    chatbot_errors = 0

    empty_answers = 0

    no_context_count = 0

    ragas_sums = {
        "faithfulness": 0.0,
        "answer_relevancy": 0.0,
        "context_precision": 0.0,
    }

    ragas_counts = {
        "faithfulness": 0,
        "answer_relevancy": 0,
        "context_precision": 0,
    }

    # ------------------------------------------------------------------------
    # Run benchmark
    # ------------------------------------------------------------------------

    for i, q in enumerate(
        questions,
        start=1,
    ):

        qid = q["question_id"]

        question = q["question"]

        expected_facts = q.get(
            "expected_answer_facts",
            [],
        )

        grounding_source = q.get(
            "requires_grounding_from",
            "",
        )

        print()
        print(
            f"[{i:>3}/{len(questions)}] "
            f"{qid}  {question[:70]}"
        )

        # ------------------------------------------------------------
        # Run chatbot
        # ------------------------------------------------------------

        response = run_chatbot(
            BENCH_USER_ID,
            question,
            DRY_RUN,
        )

        answer = response.get(
            "reply",
            "",
        )

        citations = response.get(
            "citations",
            [],
        )

        warnings = response.get(
            "warnings",
            [],
        )

        errors = response.get(
            "errors",
            [],
        )

        # ------------------------------------------------------------
        # Error tracking
        # ------------------------------------------------------------

        if errors:

            chatbot_errors += 1

            print(
                "         [ERROR] CHATBOT ERROR:"
            )

            for error in errors:

                print(
                    f"            {error}"
                )

        # ------------------------------------------------------------
        # Empty answer
        # ------------------------------------------------------------

        if not answer.strip():

            empty_answers += 1

            print(
                "         ⚠️ EMPTY ANSWER"
            )

        # ------------------------------------------------------------
        # Show answer
        # ------------------------------------------------------------

        if PRINT_ANSWERS:

            print(
                f"         ANSWER: "
                f"{answer[:500]}"
            )

        # ------------------------------------------------------------
        # Citations/context
        # ------------------------------------------------------------

        contexts = [
            c.get("excerpt", "")
            for c in citations
            if isinstance(c, dict)
            and c.get("excerpt")
        ]

        if not contexts:

            no_context_count += 1

            print(
                "         CONTEXT: NONE RETRIEVED"
            )

        else:

            print(
                f"         CONTEXT: "
                f"{len(contexts)} citation(s)"
            )

        if PRINT_CITATIONS and citations:

            print(
                "         CITATIONS:"
            )

            for citation in citations:

                print(
                    f"            {citation}"
                )

        # ------------------------------------------------------------
        # Grounding checker
        # ------------------------------------------------------------

        correction_fired = any(
            "unverified citation"
            in str(warning).lower()
            for warning in warnings
        )

        if correction_fired:

            grounding_corrections += 1

        # ------------------------------------------------------------
        # Fact check
        # ------------------------------------------------------------

        (
            all_matched,
            matched_facts,
            missed_facts,
        ) = near_match_facts(
            answer,
            expected_facts,
        )

        if all_matched:

            fact_all_matched += 1

        fact_status = (
            "PASS"
            if all_matched
            else "MISS"
        )

        print(
            f"         Fact-check: {fact_status}"
            f" | Grounding correction: "
            f"{'YES' if correction_fired else 'no'}"
        )

        if missed_facts:

            for missing_fact in missed_facts:

                print(
                    f"         MISSING FACT: "
                    f"{missing_fact}"
                )

        # ------------------------------------------------------------
        # RAGAS
        # ------------------------------------------------------------

        ragas_scores = run_ragas(
            question,
            answer,
            contexts,
        )

        for metric in (
            "faithfulness",
            "answer_relevancy",
            "context_precision",
        ):

            value = ragas_scores.get(
                metric
            )

            if value is not None:

                ragas_sums[metric] += value

                ragas_counts[metric] += 1

        # ------------------------------------------------------------
        # Save result
        # ------------------------------------------------------------

        results.append(
            {
                "question_id": qid,
                "question": question,
                "requires_grounding_from": grounding_source,

                "expected_answer_facts":
                    expected_facts,

                "chatbot_answer": answer,

                "citations": citations,

                "warnings": warnings,

                "errors": errors,

                "fact_check_passed":
                    all_matched,

                "matched_facts":
                    matched_facts,

                "missed_facts":
                    missed_facts,

                "grounding_correction_fired":
                    correction_fired,

                "context_count":
                    len(contexts),

                "ragas_scores":
                    ragas_scores,
            }
        )

    # =========================================================================
    # SUMMARY
    # =========================================================================

    total = len(questions)

    fact_accuracy = (
        round(
            fact_all_matched / total,
            4,
        )
        if total > 0
        else 0.0
    )

    grounding_correction_rate = (
        round(
            grounding_corrections / total,
            4,
        )
        if total > 0
        else 0.0
    )

    avg_ragas: dict[
        str,
        float | None,
    ] = {}

    for metric in (
        "faithfulness",
        "answer_relevancy",
        "context_precision",
    ):

        if ragas_counts[metric] > 0:

            avg_ragas[
                f"avg_{metric}"
            ] = round(
                ragas_sums[metric]
                / ragas_counts[metric],
                4,
            )

        else:

            avg_ragas[
                f"avg_{metric}"
            ] = None

    # =========================================================================
    # PRINT SUMMARY
    # =========================================================================

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print(
        f"Total questions       : "
        f"{total}"
    )

    print(
        f"Fact-check accuracy   : "
        f"{fact_all_matched}/{total}"
        f" -> {fact_accuracy * 100:.2f}%"
    )

    print(
        f"Chatbot errors        : "
        f"{chatbot_errors}/{total}"
    )

    print(
        f"Empty answers         : "
        f"{empty_answers}/{total}"
    )

    print(
        f"No context retrieved  : "
        f"{no_context_count}/{total}"
    )

    print(
        f"Grounding corrections : "
        f"{grounding_corrections}/{total}"
        f" -> "
        f"{grounding_correction_rate * 100:.2f}%"
    )

    for metric, value in avg_ragas.items():

        if value is None:

            value_string = "N/A"

        else:

            value_string = f"{value:.4f}"

        print(
            f"{metric:<25}: "
            f"{value_string}"
        )

    # =========================================================================
    # WRITE RESULTS
    # =========================================================================

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {

        "component":
            "rag_chatbot_answer",

        "bench_user_id":
            BENCH_USER_ID,

        "dry_run":
            DRY_RUN,

        "seed_before_run":
            SEED_BEFORE_RUN,

        "ragas_enabled":
            RAGAS_ENABLED,

        "total":
            total,

        "fact_check_accuracy":
            fact_accuracy,

        "chatbot_errors":
            chatbot_errors,

        "empty_answers":
            empty_answers,

        "no_context_retrieved":
            no_context_count,

        "grounding_correction_rate":
            grounding_correction_rate,

        **avg_ragas,

        "database_user_check":
            user_check,

        "questions":
            results,
    }

    with open(
        RESULTS_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print(
        f"Results written to: "
        f"{RESULTS_PATH}"
    )

    print("=" * 60)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()