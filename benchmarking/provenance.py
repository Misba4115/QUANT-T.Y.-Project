"""Reproducibility metadata for local development benchmarks."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


def provenance(dataset_path: Path, scope: str) -> dict[str, object]:
    repo = Path(__file__).resolve().parents[1]

    def git(*args: str) -> str:
        result = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
        return result.stdout.strip()

    try:
        commit = git("rev-parse", "HEAD")
        dirty = bool(git("status", "--porcelain"))
    except (OSError, subprocess.CalledProcessError):
        commit, dirty = "unavailable", None
    return {
        "dataset_sha256": hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
        "source_commit": commit,
        "working_tree_dirty": dirty,
        "evaluation_scope": scope,
    }
