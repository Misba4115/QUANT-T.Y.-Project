"""Generate paper-ready PNG and PDF figures from benchmark result files."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
BLUE = "#1F5A94"
MID_BLUE = "#4E79A7"
GREY = "#A7B0BE"
INK = "#1F2937"
GRID = "#D8DEE8"


def load(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    filename = "arialbd.ttf" if bold else "arial.ttf"
    try:
        return ImageFont.truetype(filename, size)
    except OSError:
        return ImageFont.load_default()


def centered(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, selected_font, fill=INK) -> None:
    box = draw.multiline_textbbox((0, 0), text, font=selected_font, align="center", spacing=5)
    width = box[2] - box[0]
    draw.multiline_text((xy[0] - width / 2, xy[1]), text, font=selected_font, fill=fill, align="center", spacing=5)


def bar_chart(filename: str, title: str, labels: list[str], values: list[float], colors: list[str]) -> None:
    width, height = 1600, 850
    left, top, right, bottom = 150, 120, 60, 180
    chart_width = width - left - right
    chart_height = height - top - bottom
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    draw.text((left, 35), title, font=font(34, bold=True), fill=INK)
    for value in range(0, 101, 20):
        y = top + chart_height - chart_height * value / 100
        draw.line((left, y, width - right, y), fill=GRID, width=2)
        label = f"{value}%"
        box = draw.textbbox((0, 0), label, font=font(20))
        draw.text((left - 18 - (box[2] - box[0]), y - 11), label, font=font(20), fill=INK)
    draw.line((left, top, left, top + chart_height), fill=INK, width=2)
    draw.line((left, top + chart_height, width - right, top + chart_height), fill=INK, width=2)

    slot = chart_width / len(values)
    bar_width = slot * 0.58
    for index, (label, value, color) in enumerate(zip(labels, values, colors)):
        centre = left + slot * (index + 0.5)
        bar_top = top + chart_height * (1 - value / 100)
        draw.rounded_rectangle(
            (centre - bar_width / 2, bar_top, centre + bar_width / 2, top + chart_height),
            radius=7,
            fill=color,
        )
        centered(draw, (centre, bar_top - 42), f"{value:.1f}%", font(23, bold=True))
        centered(draw, (centre, top + chart_height + 28), label, font(20))

    image.save(RESULTS / f"{filename}.png", dpi=(220, 220))
    image.save(RESULTS / f"{filename}.pdf", "PDF", resolution=220)


def gcsec_ablation() -> None:
    configs = load("gc_sec_ablation_v2_summary.json")["configs"]
    bar_chart(
        "gcsec_ablation",
        "GC-SEC v2 Controlled Fixture: Final-Action Accuracy",
        ["Baseline", "Grounding", "Grounding +\nArbitration"],
        [item["final_action_accuracy"] * 100 for item in configs],
        [GREY, MID_BLUE, BLUE],
    )


def component_scores() -> None:
    functional = load("functional_stress_results.json")
    routing = load("routing_orchestration_summary.json")
    tax = load("tax_engine_results.json")
    portfolio = load("portfolio_analytics_results.json")
    security = load("security_matrix_summary.json")
    completed_security = security["totals"]["passed"] + security["totals"]["inspection_pass"]
    security_total = completed_security + security["totals"]["failed"]
    comparable_portfolios = portfolio["passed"] + portfolio["failed"]

    bar_chart(
        "component_benchmark_scores",
        "QUANT-T.Y. Component Benchmark Results",
        ["Categorization\naccuracy", "Guardian\nF1", "Routing\naccuracy", "Tax exact\nmatch", "Portfolio\nreference pass", "Security\ncheck pass"],
        [
            functional["cashflow_categorization"]["accuracy"] * 100,
            functional["guardian"]["f1"] * 100,
            routing["overall"]["routing_accuracy"] * 100,
            tax["exact_match_rate"] * 100,
            portfolio["passed"] / comparable_portfolios * 100,
            completed_security / security_total * 100,
        ],
        [BLUE] * 6,
    )


if __name__ == "__main__":
    gcsec_ablation()
    component_scores()
    print(f"Wrote benchmark figures to {RESULTS}")
