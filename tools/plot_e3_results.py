"""Figura do E3: observado vs predito, residuos e importancia de features."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

DATA = "#2f855a"
PRODUCT = "#c05621"
METHOD = "#2b6cb0"
GRAY = "#4b5563"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--predictions", required=True)
    ap.add_argument("--metrics", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--target", default="agb_mg_ha")
    args = ap.parse_args()

    pred = pd.read_csv(args.predictions)
    metrics = json.loads(Path(args.metrics).read_text(encoding="utf-8"))
    pred = pred[pred["pred"].notna()].copy()

    fig, axes = plt.subplots(1, 3, figsize=(18, 5.6),
                             gridspec_kw={"width_ratios": [1.2, 1.1, 1.4]})

    ax = axes[0]
    colors = {"Amazônia": DATA, "Cerrado": PRODUCT}
    for biome, group in pred.groupby("biome"):
        ax.scatter(group[args.target], group["pred"], s=42, alpha=0.85,
                   color=colors.get(str(biome), METHOD), label=str(biome))
    lim = [0, max(pred[args.target].max(), pred["pred"].max()) * 1.08]
    ax.plot(lim, lim, color=GRAY, linestyle="--", linewidth=1.2)
    overall = metrics["overall"]
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("AGB observada (Mg/ha)")
    ax.set_ylabel("AGB predita (Mg/ha)")
    ax.set_title(f"Validação espacial (n={overall['n']})", fontsize=13)
    ax.text(0.04, 0.96,
            f"R² = {overall['r2']:.2f}\nRMSE = {overall['rmse']:.1f}\n"
            f"viés = {overall['bias']:.1f}",
            transform=ax.transAxes, va="top", fontsize=10,
            bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "#ddd"})
    ax.legend(fontsize=9.5)
    ax.grid(alpha=0.2)

    ax = axes[1]
    pred["residual"] = pred["pred"] - pred[args.target]
    groups = [g["residual"].to_numpy() for _, g in
              pred.groupby("fitofisionomia_group")]
    labels = [str(k) for k, _ in pred.groupby("fitofisionomia_group")]
    ax.boxplot(groups, tick_labels=labels, patch_artist=True,
               boxprops={"facecolor": "#bee3f8"},
               medianprops={"color": METHOD, "linewidth": 2})
    ax.axhline(0, color=GRAY, linestyle="--", linewidth=1)
    ax.set_ylabel("Resíduo (predito − observado, Mg/ha)")
    ax.set_title("Resíduo por fitofisionomia", fontsize=13)
    ax.grid(axis="y", alpha=0.2)

    ax = axes[2]
    importance = pd.DataFrame(metrics["importance"], columns=["feature", "value"])
    importance = importance.sort_values("value").tail(14)
    ax.barh(importance["feature"], importance["value"], color=METHOD, alpha=0.85)
    ax.set_xlabel("importância (RF)")
    ax.set_title("Features mais importantes", fontsize=13)
    ax.tick_params(axis="y", labelsize=9)
    ax.grid(axis="x", alpha=0.2)

    fig.suptitle("E3 — piloto Tier B (~1,1 km): baseline por estrato vs RF",
                 fontsize=16, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, facecolor="white")
    plt.close(fig)
    print(f"gerado: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
