"""Refresh the six existing paper figures in the root RESULTS directory."""
from __future__ import annotations

import json
from math import sqrt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "benchmarking" / "results"
OUT = ROOT / "RESULTS"
FIGURE_HEIGHTS = {3: 1004, 4: 882, 5: 922, 6: 1002, 7: 1442, 8: 1082}
DPI = 200
INK = "#242424"
MID = "#555555"
LIGHT = "#898989"
PALE = "#aaaaaa"


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def canvas(number: int, *, left: float = 0.18, right: float = 0.95,
           bottom: float = 0.14, top: float = 0.94):
    fig, ax = plt.subplots(figsize=(1422 / DPI, FIGURE_HEIGHTS[number] / DPI), dpi=DPI)
    fig.subplots_adjust(left=left, right=right, bottom=bottom, top=top)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(INK)
        ax.spines[spine].set_linewidth(1.5)
    ax.tick_params(axis="both", colors=INK, labelsize=15, width=1.4, length=7, pad=8)
    ax.grid(axis="y", color="#d9d9d9", linewidth=0.9)
    ax.set_axisbelow(True)
    return fig, ax


def save(fig, number: int) -> None:
    path = OUT / f"Figure_{number}.png"
    assert path.exists(), f"Refusing to create a new filename: {path}"
    fig.savefig(path, dpi=DPI, facecolor="white")
    plt.close(fig)


def gcsec_accuracy() -> None:
    configs = load("gc_sec_ablation_v2_summary.json")["configs"]
    assert [item["config_name"] for item in configs] == ["baseline", "gcsec1", "gcsec2"]
    fig, ax = canvas(3, left=0.16, bottom=0.14, top=0.78)
    x = np.arange(3)
    lines = [
        ("Final action", "final_action_accuracy", INK, "o", "-"),
        ("Grounding", "grounding_accuracy", MID, "s", "--"),
        ("Conflict resolution", "conflict_resolution_accuracy", LIGHT, "^", ":"),
        ("Correction", "grounding_correction_rate", PALE, "D", "-."),
    ]
    for label, key, color, marker, style in lines:
        ax.plot(x, [item[key] for item in configs], label=label, color=color,
                marker=marker, markersize=11, linewidth=2.4, linestyle=style)
    ax.set_xticks(x, ["Baseline", "GC–SEC–1", "GC–SEC–2"])
    ax.set_yticks(np.linspace(0, 1, 6))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_ylim(-0.03, 1.06)
    ax.set_ylabel("Accuracy or rate", fontsize=18, color=INK)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02), ncol=2,
              frameon=False, fontsize=15, handlelength=2.5, columnspacing=1.2)
    save(fig, 3)


def gcsec_latency() -> None:
    configs = load("gc_sec_ablation_v2_summary.json")["configs"]
    values = [item["mean_latency_ms"] for item in configs]
    fig, ax = canvas(4, left=0.19, bottom=0.17, top=0.92)
    x = np.arange(3)
    ax.vlines(x, 0, values, color=MID, linewidth=3)
    ax.scatter(x, values, color=INK, s=160, zorder=3)
    for position, value in zip(x, values):
        ax.text(position, value + 0.0018, f"{value:.3f}", ha="center", va="bottom", fontsize=15, color=INK)
    ax.set_xticks(x, ["Baseline", "GC–SEC–1", "GC–SEC–2"])
    ax.set_ylim(0, max(values) * 1.28)
    ax.set_ylabel("Mean component latency (ms)", fontsize=18, color=INK)
    save(fig, 4)


def routing() -> None:
    strata = load("routing_orchestration_summary.json")["overall"]["strata"]
    labels = ["Single intent", "Cross-agent", "Ambiguous", "Adversarial / OOS"]
    assert len(strata) == len(labels) == 4
    fig, ax = canvas(5, left=0.32, right=0.96, bottom=0.16, top=0.93)
    y = np.arange(4)
    for position, item in zip(y, strata):
        score = item["routing_accuracy"]
        total = item["total_queries"]
        correct = round(score * total)
        ax.hlines(position, 0, score, color=LIGHT, linewidth=3)
        ax.scatter(score, position, color=INK, s=135, zorder=3)
        ax.text(1.0, position - 0.13, f"{score:.1%}  ({correct}/{total})",
                ha="right", va="bottom", fontsize=14, color=INK)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.05)
    ax.set_xticks(np.linspace(0, 1, 6))
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel("Routing accuracy", fontsize=18, color=INK)
    ax.grid(axis="x", color="#d9d9d9", linewidth=0.9)
    ax.grid(axis="y", visible=False)
    save(fig, 5)


def wilson(success: int, total: int, z: float = 1.96) -> tuple[float, float]:
    p = success / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return center - radius, center + radius


def guardian() -> None:
    metrics = load("guardian_anomaly_results.json")["per_anomaly_type"]
    kinds = [
        ("Amount spike", "amount_spike"),
        ("Duplicate", "duplicate_transaction"),
        ("Large transfer", "large_round_transfer"),
        ("Odd hour", "odd_hour"),
        ("First-seen category", "unusual_category_first_seen"),
    ]
    fig, ax = canvas(6, left=0.33, bottom=0.15, top=0.95)
    y = np.arange(len(kinds))
    for position, (_, key) in zip(y, kinds):
        item = metrics[key]
        success, total = item["tp"], item["tp"] + item["fn"]
        lo, hi = wilson(success, total)
        rate = success / total
        ax.hlines(position, lo, hi, color=MID, linewidth=3)
        ax.vlines([lo, hi], position - 0.09, position + 0.09, color=MID, linewidth=2)
        ax.scatter(rate, position, color=INK, s=145, zorder=3)
        ax.text(1.03, position + 0.05, f"{success}/{total}", fontsize=16, color=INK)
    ax.set_yticks(y, [label for label, _ in kinds])
    ax.invert_yaxis()
    ax.set_xlim(0, 1.18)
    ax.set_xticks(np.linspace(0, 1, 6))
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel("Recall (95% Wilson interval)", fontsize=18, color=INK)
    ax.grid(axis="x", color="#d9d9d9", linewidth=0.9)
    ax.grid(axis="y", visible=False)
    save(fig, 6)


def cashflow() -> None:
    result = load("cashflow_categorization_results.json")
    metrics = result["per_category_metrics"]
    rows = [(name, item) for name, item in metrics.items() if item["support"] > 0]
    unsupported = [name for name, item in metrics.items() if item["support"] == 0]
    fig, ax = canvas(7, left=0.26, bottom=0.19, top=0.97)
    y = np.arange(len(rows))
    for position, (_, item) in zip(y, rows):
        f1 = item["f1"]
        ax.hlines(position, 0, f1, color=PALE, linewidth=2.5)
        ax.scatter(f1, position, color=INK, s=110, zorder=3)
        ax.text(1.03, position + 0.05, f"n={item['support']}", fontsize=15, color=INK)
    ax.set_yticks(y, [name for name, _ in rows])
    ax.invert_yaxis()
    ax.set_xlim(0, 1.20)
    ax.set_xticks(np.linspace(0, 1, 5))
    ax.set_xlabel("F1 score; support shown at right", fontsize=18, color=INK)
    ax.grid(axis="x", color="#d9d9d9", linewidth=0.9)
    ax.grid(axis="y", visible=False)
    if unsupported:
        fig.text(0.26, 0.035, "No labeled examples: " + ", ".join(unsupported), fontsize=13, color=MID)
    save(fig, 7)


def portfolio() -> None:
    result = load("portfolio_analytics_results.json")
    rows = [item for item in result["portfolios"] if item["status"] == "PASS"]
    assert len(rows) == result["passed"]
    x = [item["ppo_sharpe"] for item in rows]
    y = [(item["engine_sharpe"] - item["ppo_sharpe"]) * 1_000_000 for item in rows]
    fig, ax = canvas(8, left=0.19, bottom=0.14, top=0.95)
    ax.axhline(0, color=MID, linewidth=1.6)
    ax.scatter(x, y, facecolors="white", edgecolors=INK, linewidths=1.6, s=155, zorder=3)
    ax.set_xlim(0, max(x) * 1.06)
    spread = max(abs(min(y)), abs(max(y))) + 0.5
    ax.set_ylim(-spread, spread)
    ax.set_xlabel("PyPortfolioOpt Sharpe ratio", fontsize=18, color=INK)
    ax.set_ylabel("QUANT − reference\nSharpe ratio (×10⁻⁶)", fontsize=18, color=INK)
    ax.text(0.98, 0.96, f"{len(rows)} completed comparisons\n{result['errored']} solver errors excluded",
            transform=ax.transAxes, ha="right", va="top", fontsize=15, color=INK)
    save(fig, 8)


def main() -> None:
    expected = {f"Figure_{n}.png" for n in FIGURE_HEIGHTS}
    actual = {path.name for path in OUT.glob("Figure_*.png")}
    assert actual == expected, f"Unexpected figure filenames: {sorted(actual ^ expected)}"
    gcsec_accuracy()
    gcsec_latency()
    routing()
    guardian()
    cashflow()
    portfolio()
    print("Updated:", ", ".join(sorted(expected)))


if __name__ == "__main__":
    main()
