"""Figuras do plano de features e abordagem (docs/62).

Gera:
  1. fluxograma do pipeline (campo -> target -> features -> modelo -> mapa);
  2. grupos de features e o que e vedado como feature;
  3. histogramas reais do target (AGB por tier e contagem por fitofisionomia).

Uso:
  python tools/plot_plan_features.py --out-dir docs/figuras \
    --gpkg data/processed/ifn_enrich_footprint/ifn_candidatos_espaciais.gpkg
"""
from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

DATA = "#2f855a"
METHOD = "#2b6cb0"
PRODUCT = "#c05621"
VEDADO = "#c53030"
GRAY = "#4b5563"
TEXT = "#1f2937"
BG = "#f9fafb"


def _box(ax, x, y, w, h, title, lines, color):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                         facecolor=BG, edgecolor=color, linewidth=2)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h - 0.16, title, ha="center", va="top",
            fontsize=12.5, fontweight="bold", color=color)
    ax.text(x + w / 2, y + h - 0.42, "\n".join(lines), ha="center", va="top",
            fontsize=10.2, color=TEXT)


def _arrow(ax, x1, y1, x2, y2, color=GRAY):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                                 arrowstyle="-|>", mutation_scale=18,
                                 color=color, linewidth=1.8))


def figura_fluxo(out: Path) -> Path:
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")

    _box(ax, 0.3, 6.3, 3.4, 2.2, "1. Dados de campo",
         ["IFN/SFB: 7.466 UAs", "PLOS, CEDA, ORNL",
          "RAINFOR / Maracá / Vourlitis", "(fontes independentes)"], DATA)
    _box(ax, 4.2, 6.3, 3.4, 2.2, "2. Normalização",
         ["esquema canônico", "área, data, coordenada",
          "equação + variáveis", "proveniência e licença"], METHOD)
    _box(ax, 8.1, 6.3, 3.4, 2.2, "3. Target observado",
         ["Tier A: 604 pixels / 96 UAs", "Tier B: 1.088 células",
          "AGB mín · mediana · máx", "1 target por UA"], DATA)
    _box(ax, 12.0, 6.3, 3.4, 2.2, "4. Features",
         ["S2/S1/Landsat", "terreno, clima, solo",
          "histórico MapBiomas", "mesmo suporte do target"], METHOD)

    _box(ax, 12.0, 2.6, 3.4, 2.2, "5. Modelo",
         ["por bioma e grupo", "CV espacial com buffer",
          "alvo intervalar", "hierárquico por fitofisionomia"], METHOD)
    _box(ax, 8.1, 2.6, 3.4, 2.2, "6. Incerteza",
         ["conformal + faixa de equações", "AOA por suporte",
          "cobertura de IC", "declarar componentes"], METHOD)
    _box(ax, 4.2, 2.6, 3.4, 2.2, "7. Mapa 30 m",
         ["AGB + IC90 + AOA", "máscara do ano (3/4)",
          "sem GEDI/LiDAR como feature", "COG + metadados"], PRODUCT)
    _box(ax, 0.3, 2.6, 3.4, 2.2, "8. Validação e MRV",
         ["holdout por fonte/região", "G0–G7 (docs/44)",
          "model card por versão", "promoção ADR-0033"], PRODUCT)

    _arrow(ax, 3.7, 7.4, 4.2, 7.4)
    _arrow(ax, 7.6, 7.4, 8.1, 7.4)
    _arrow(ax, 11.5, 7.4, 12.0, 7.4)
    _arrow(ax, 13.7, 6.3, 13.7, 4.8)
    _arrow(ax, 12.0, 3.7, 11.5, 3.7)
    _arrow(ax, 8.1, 3.7, 7.6, 3.7)
    _arrow(ax, 4.2, 3.7, 3.7, 3.7)
    _arrow(ax, 2.0, 4.8, 2.0, 6.3, color=GRAY)
    ax.text(2.15, 5.55, "retroalimenta\n(iteração)", fontsize=9.5,
            color=GRAY, va="center")

    ax.text(0.3, 8.85, "Fluxo proposto: do inventário observado ao mapa de AGB",
            fontsize=17, fontweight="bold", color=TEXT)
    ax.text(8.0, 1.6,
            "Regra central: o target vem do campo e das equações; as features vêm de "
            "sensores disponíveis na inferência.\nGEDI e LiDAR são referência "
            "(ADR-0022/0027), nunca feature; coordenadas só em splits.",
            ha="center", fontsize=11.5, color=GRAY)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.97, bottom=0.03)
    path = out / "plano_1_fluxo.png"
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)
    return path


def figura_features(out: Path) -> Path:
    fig, ax = plt.subplots(figsize=(15, 8.5))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 9)
    ax.axis("off")

    groups = [
        (0.3, 5.6, "Óptico (S2 / Landsat)", DATA,
         ["bandas B2–B12, B8A", "NDVI, EVI, SAVI, NDRE",
          "CIgreen/CIre, NBR, NDFI", "textura GLCM e fenologia"]),
        (4.0, 5.6, "SAR (Sentinel-1)", DATA,
         ["VV, VH, razão VH/VV", "RVI", "textura SAR", "série anual"]),
        (7.7, 5.6, "Terreno e clima", METHOD,
         ["elevação, declividade", "TPI, curvatura, HAND",
          "chuva anual e sazonalidade", "temperatura e VPD/DEF"]),
        (11.4, 5.6, "Solo", METHOD,
         ["argila, areia, silte", "CTC", "profundidade/drenagem",
          "SOC (experimental, com ablacao)"]),
        (0.3, 2.0, "Histórico e paisagem", METHOD,
         ["classe MapBiomas do ano", "idade desde conversão",
          "estabilidade e fogo", "borda e tamanho de fragmento"]),
        (4.0, 2.0, "Alometria (não é feature)", PRODUCT,
         ["DAP, H, WD, palmeiras", "definem o target",
          "equações confirmadas", "incerteza min–med–máx"]),
        (7.7, 2.0, "Vedado como feature", VEDADO,
         ["GEDI L2A/L4A", "LiDAR aerotransportado",
          "ICESat-2 ATL08", "lon/lat (só splits)"]),
        (11.4, 2.0, "Modelo", PRODUCT,
         ["por bioma/grupo", "CV espacial", "alvo intervalar",
          "AOA + conformal"]),
    ]
    for x, y, title, color, lines in groups:
        _box(ax, x, y, 3.4, 2.9, title, lines, color)

    for x in (2.0, 5.7, 9.4):
        _arrow(ax, x, 5.5, x, 5.0)
    _arrow(ax, 13.1, 5.5, 13.1, 5.0)
    ax.text(7.5, 8.7, "Grupos de features: o que entra no modelo e o que é vedado",
            ha="center", fontsize=16.5, fontweight="bold", color=TEXT)
    ax.text(7.5, 1.2,
            "Critério: a variável precisa existir na inferência, no mesmo suporte, "
            "com ganho demonstrado em validação espacial e sem vazamento.",
            ha="center", fontsize=11, color=GRAY)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.96, bottom=0.02)
    path = out / "plano_2_features.png"
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)
    return path


def figura_target(out: Path, gpkg: Path) -> Path:
    px = gpd.read_file(gpkg, layer="pixels_confirmados")
    cl = gpd.read_file(gpkg, layer="celulas_confirmadas")
    ua_px = px.drop_duplicates("ua")
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.4),
                             gridspec_kw={"width_ratios": [1.2, 1.2, 1.6]})

    ax = axes[0]
    ax.hist(ua_px["agb_mediana_mg_ha"].dropna(), bins=20, color=DATA,
            alpha=0.85, edgecolor="white")
    ax.set_title(f"Tier A — pixel (n={len(ua_px)} UAs)", fontsize=13)
    ax.set_xlabel("AGB mediana (Mg/ha)")
    ax.set_ylabel("UAs")
    ax.grid(alpha=0.2)

    ax = axes[1]
    ax.hist(cl["agb_mediana_mg_ha"].dropna(), bins=30, color=PRODUCT,
            alpha=0.85, edgecolor="white")
    ax.set_title(f"Tier B — célula (n={len(cl)})", fontsize=13)
    ax.set_xlabel("AGB mediana (Mg/ha)")
    ax.set_ylabel("células")
    ax.grid(alpha=0.2)

    ax = axes[2]
    counts = pd.DataFrame({
        "pixel": ua_px.groupby("fitofisionomia").size(),
        "celula": cl.groupby("fitofisionomia").size(),
    }).fillna(0).sort_values("celula")
    y = np.arange(len(counts))
    ax.barh(y - 0.2, counts["pixel"], height=0.4, color=DATA,
            label="pixel (UAs)")
    ax.barh(y + 0.2, counts["celula"], height=0.4, color=PRODUCT,
            label="célula")
    ax.set_yticks(y)
    ax.set_yticklabels([s.replace("Floresta ", "F. ") for s in counts.index],
                       fontsize=9.5)
    ax.set_xlabel("amostras independentes")
    ax.set_title("Composição do target por fitofisionomia", fontsize=13)
    ax.legend(fontsize=9.5)
    ax.grid(axis="x", alpha=0.2)

    fig.suptitle("Target observado: distribuição de AGB e cobertura por "
                 "fitofisionomia", fontsize=16, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    path = out / "plano_3_target_hist.png"
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", default="docs/figuras")
    ap.add_argument("--gpkg",
                    default="data/processed/ifn_enrich_footprint/"
                            "ifn_candidatos_espaciais.gpkg")
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = [figura_fluxo(out), figura_features(out),
             figura_target(out, Path(args.gpkg))]
    for p in paths:
        print(f"gerado: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
