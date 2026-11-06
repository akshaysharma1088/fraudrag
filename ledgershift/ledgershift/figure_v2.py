"""Operating-point figure for LedgerShift v2 (false alarm vs false clearance).

  python -m ledgershift.figure_v2 [out.png]

Reads results_v2/analysis.json written by analyze_v2.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
CURVES = [("fuzzy", "String similarity", "#2a78d6"), ("ditto", "Ditto-style", "#eb6834"),
          ("embed_bge", "BGE", "#1baf7a"), ("embed_minilm", "MiniLM", "#eda100")]
POINTS = [("fuzzy", "Fuzzy, statement-tuned", "s"), ("alias", "Alias (upper bound)", "D"),
          ("llm_llama3.1_8b", "Llama 3.1 8B", "o"), ("llm_gemma3_12b", "Gemma 3 12B", "o"),
          ("llm_qwen2.5_14b", "Qwen2.5 14B", "o"), ("escalate_llm", "Escalation, Qwen2.5 14B", "^")]
INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#e4e3de"


def main(out):
    a = json.loads((ROOT / "results_v2" / "analysis.json").read_text())["v2"]
    fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=200)
    for k, label, col in CURVES:
        pts = a["curves"].get(k)
        if not pts:
            continue
        xs = [100 * p["false_alarm"] for p in pts]; ys = [100 * p["false_clearance"] for p in pts]
        ax.plot(xs, ys, color=col, lw=2, label=f"{label} (threshold sweep)", zorder=2)
    offs = {"fuzzy": (6, 4), "alias": (6, 4), "llm_llama3.1_8b": (4, -12), "llm_gemma3_12b": (4, -12),
            "llm_qwen2.5_14b": (4, -12), "escalate_llm": (-6, -36)}
    for k, label, mk in POINTS:
        o = a["overall"].get(k)
        if not o:
            continue
        x, y = 100 * o["false_alarm"], 100 * o["false_clearance"]
        ax.scatter([x], [y], s=46, marker=mk, color=INK, edgecolor="white", linewidth=1.5, zorder=4)
        ax.annotate(label, (x, y), xytext=offs.get(k, (6, 4)), textcoords="offset points", fontsize=7.5, color=INK,
                    ha="right" if k == "escalate_llm" else "left",
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.7) if k == "escalate_llm" else None)
    ax.set_xlabel("False alarms (% of genuine statements)", fontsize=9, color=INK)
    ax.set_ylabel("False clearances (% of altered or\nunsupported statements)", fontsize=9, color=INK)
    ax.set_xlim(-2, 80); ax.set_ylim(-0.7, 5.2)
    ax.grid(color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.legend(fontsize=7.5, frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(out)
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "results_v2" / "operating_points.png"))
