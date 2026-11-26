"""Figuras explicativas da metodologia IFN -> pegada -> composição (docs/60).

Uso:
  python tools/plot_ifn_methodology.py --out-dir docs/figuras

Gera:
  1. ponto publicado -> pegada (Cruz de Malta) e o empilhamento de registros;
  2. dentro da cruz: subparcelas, solo, necromassa e classes de uso (ilustrativo);
  3. escalas: pegada x pixel MapBiomas x arredondamento da coordenada.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402

EDGE = "#374151"
GRID = "#9ca3af"
FOREST = "#2f855a"
SAVANNA = "#dd6b20"
PASTURE = "#f6e05e"
TEXT = "#1f2937"
SOIL = "#2b6cb0"
NECRO = "#6b46c1"


def _arm_rects(length: float = 50.0, width: float = 20.0,
               gap: float = 10.0):
    """Retângulos dos 4 braços (N, E, S, W) em metros relativos ao centro."""
    return [
        (-width / 2, gap, width, length),                       # N (1)
        (gap, -width / 2, length, width),                       # E (2)
        (-width / 2, -(gap + length), width, length),           # S (3)
        (-(gap + length), -width / 2, length, width),           # W (4)
    ]


def _draw_cross(ax, length=50, width=20, gap=10, face="#f9fafb"):
    for x, y, w, h in _arm_rects(length, width, gap):
        ax.add_patch(Rectangle((x, y), w, h, facecolor=face,
                               edgecolor=EDGE, linewidth=1.8, zorder=2))
    ax.plot(0, 0, "o", color="black", markersize=7, zorder=8)


def _draw_grid(ax, length=50, width=20, gap=10):
    for x, y, w, h in _arm_rects(length, width, gap):
        for step in range(10, int(w), 10):
            ax.plot([x + step, x + step], [y, y + h], color=GRID,
                    linewidth=0.6, zorder=3)
        for step in range(10, int(h), 10):
            ax.plot([x, x + w], [y + step, y + step], color=GRID,
                    linewidth=0.6, zorder=3)


def _subcells(length=50, width=20, gap=10):
    out = []
    for k, (x, y, w, h) in enumerate(_arm_rects(length, width, gap)):
        for i in range(int(w // 10)):
            for j in range(int(h // 10)):
                out.append((x + 10 * i, y + 10 * j, k, i, j))
    return out


def figura_1(out: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(15, 7.6))

    # ---- painel A ----
    ax = axes[0]
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.25, 1.15)
    ax.axis("off")
    for i, (dx, dy) in enumerate([(0.16, 0.14), (0.12, 0.105),
                                  (0.08, 0.07), (0.04, 0.035)]):
        ax.add_patch(Circle((dx, dy), 0.03, facecolor="#9ca3af",
                            edgecolor="white", linewidth=1.2, alpha=0.9,
                            zorder=3 + i))
    ax.plot(0, 0, "o", color="black", markersize=12, zorder=10)
    ax.annotate("ponto publicado\n(centro do conglomerado)",
                xy=(0, 0), xytext=(-1.3, -0.35), fontsize=13, color=TEXT,
                arrowprops=dict(arrowstyle="->", color=EDGE, lw=1.5),
                ha="left")
    ax.annotate("≈ 59 registros no MESMO ponto\n(classe de uso × equação)",
                xy=(0.14, 0.13), xytext=(-0.05, 0.85), fontsize=13,
                color=TEXT, ha="left",
                arrowprops=dict(arrowstyle="->", color=EDGE, lw=1.5))
    ax.text(-1.3, -0.72,
            "Exemplo (mesma UA):\n"
            "• Floresta Natural · Eq. 209 · 16,1 Mg/ha\n"
            "• Savana · Eq. 78 · 24,9 Mg/ha\n"
            "• … mais ~57 registros",
            fontsize=11.5, color=TEXT, va="top",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#f3f4f6",
                      edgecolor=GRID))
    ax.set_title("1. O que o IFN publica", fontsize=16, color=TEXT,
                 loc="left", fontweight="bold")

    # ---- painel B ----
    ax = axes[1]
    ax.set_aspect("equal")
    ax.set_xlim(-85, 85)
    ax.set_ylim(-80, 85)
    ax.axis("off")
    _draw_cross(ax)
    _draw_grid(ax)
    for label, (x, y) in {"1": (0, 65), "2": (65, 0),
                          "3": (0, -65), "4": (-65, 0)}.items():
        ax.text(x, y, label, fontsize=15, ha="center", va="center",
                color=TEXT, fontweight="bold")

    # cotas fora da cruz
    ax.annotate("", xy=(-22, 10), xytext=(-22, 60),
                arrowprops=dict(arrowstyle="<->", color=EDGE, lw=1.4))
    ax.text(-25, 35, "50 m", rotation=90, va="center", ha="right",
            fontsize=12, color=TEXT)
    ax.annotate("", xy=(-10, 78), xytext=(10, 78),
                arrowprops=dict(arrowstyle="<->", color=EDGE, lw=1.4))
    ax.text(0, 80, "20 m", ha="center", va="bottom", fontsize=12, color=TEXT)
    ax.annotate("10 m\nde vão", xy=(4, 6), xytext=(30, -22), fontsize=12,
                color=TEXT, ha="left",
                arrowprops=dict(arrowstyle="->", color=EDGE, lw=1.4))
    ax.annotate("sobreposição dos registros:\nmesmo centro, mesma pegada",
                xy=(0.5, 0.5), xytext=(28, 52), fontsize=11.5, color=EDGE,
                ha="left",
                arrowprops=dict(arrowstyle="->", color=GRID, lw=1.2,
                                linestyle=":"))
    ax.set_title("2. O que foi medido: a pegada", fontsize=16, color=TEXT,
                 loc="left", fontweight="bold")
    for a in axes:
        a.title.set_position((0.0, 1.02))

    fig.text(0.5, 0.035,
             "Cruz de Malta: 4 braços de 20 × 50 m (20 × 100 m no bioma Amazônia), "
             "a 10 m do centro.\nA coordenada é o centro; as árvores são medidas nos braços. "
             "Nenhum pixel é extraído no centro.",
             ha="center", fontsize=12.2, color=EDGE)
    fig.subplots_adjust(left=0.03, right=0.98, top=0.90, bottom=0.12,
                        wspace=0.08)
    path = out / "ifn_metodologia_1_ponto_pegada.png"
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)
    return path


def figura_2(out: Path) -> Path:
    fig, ax = plt.subplots(figsize=(11, 10))
    ax.set_aspect("equal")
    ax.set_xlim(-80, 80)
    ax.set_ylim(-80, 88)
    ax.axis("off")
    _draw_cross(ax)

    colors = {(0, 0): FOREST, (0, 1): FOREST, (1, 0): FOREST,
              (1, 1): SAVANNA, (2, 0): SAVANNA, (2, 1): SAVANNA,
              (3, 0): PASTURE, (3, 1): FOREST}
    for x, y, arm, col, row in _subcells():
        color = colors.get((arm, col))
        if color:
            ax.add_patch(Rectangle((x + 0.6, y + 0.6), 8.8, 8.8,
                                   facecolor=color, alpha=0.85,
                                   edgecolor="white", linewidth=0.8,
                                   zorder=4))
    _draw_grid(ax)

    ax.add_patch(Circle((0, 0), 5, facecolor="none", edgecolor=SOIL,
                        linewidth=2, linestyle="--", zorder=9))
    ax.annotate("solo: raio de 5 m", xy=(0, 4), xytext=(20, -18),
                fontsize=12, color=SOIL,
                arrowprops=dict(arrowstyle="->", color=SOIL, lw=1.4))

    ax.plot([-3.54, 3.54], [-3.54, 3.54], color=NECRO, linewidth=2.2,
            zorder=10)
    ax.plot([-3.54, 3.54], [3.54, -3.54], color=NECRO, linewidth=2.2,
            zorder=10)
    ax.annotate("necromassa: 2 transectos de 10 m\na 45° do centro",
                xy=(3, 3), xytext=(22, 28), fontsize=12, color=NECRO,
                arrowprops=dict(arrowstyle="->", color=NECRO, lw=1.4))

    ax.add_patch(Rectangle((-10, 50), 5, 5, facecolor="none",
                           edgecolor="#975a16", linewidth=2, zorder=11))
    ax.annotate("regeneração: 5 × 5 m\n(no último quadrante)",
                xy=(-7, 52), xytext=(-72, 70), fontsize=12, color="#975a16",
                arrowprops=dict(arrowstyle="->", color="#975a16", lw=1.4))
    ax.annotate("subparcelas de 10 × 10 m\n(2 colunas × 5 linhas por braço)",
                xy=(12, 50), xytext=(28, 78), fontsize=12, color=TEXT,
                ha="left",
                arrowprops=dict(arrowstyle="->", color=EDGE, lw=1.2))
    ax.set_title("Dentro da cruz: como as amostras são recolhidas",
                 fontsize=16, color=TEXT, loc="left", fontweight="bold")

    handles = [
        Rectangle((0, 0), 1, 1, facecolor=FOREST,
                  label="floresta (exemplo)"),
        Rectangle((0, 0), 1, 1, facecolor=SAVANNA, label="savana (exemplo)"),
        Rectangle((0, 0), 1, 1, facecolor=PASTURE,
                  label="pastagem (exemplo)"),
        Line2D([0], [0], color=NECRO, lw=2, label="transecto de necromassa"),
        Line2D([0], [0], color=SOIL, lw=2, ls="--", label="raio de solo (5 m)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=10.5,
               frameon=True, bbox_to_anchor=(0.5, 0.09))
    fig.text(0.5, 0.015,
             "Cores: classes de uso (EXEMPLO). A posição das subparcelas de cada "
             "classe não é publicada;\na composição é calculada na pegada inteira, "
             "nunca no centro.",
             ha="center", fontsize=11.5, color=TEXT)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.20)
    path = out / "ifn_metodologia_2_dentro_da_cruz.png"
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)
    return path


def figura_3(out: Path) -> Path:
    fig, ax = plt.subplots(figsize=(15, 5.4))
    ax.set_xscale("log")
    ax.plot([15, 150_000], [0, 0], color=EDGE, linewidth=2.2, zorder=2)

    markers = [
        (30, "pixel MapBiomas\n(30 m)", FOREST, 0.55, "bottom"),
        (60.8, "raio da pegada\nCerrado etc. (61 m)", FOREST, -0.55, "top"),
        (110.5, "raio da pegada\nAmazônia (110 m)", FOREST, 0.95, "bottom"),
        (557, "metade do arredondamento\n2 casas (±557 m)", "#c05621",
         -0.95, "top"),
        (5566, "1 casa decimal\n(±5,6 km)", "#c05621", 0.55, "bottom"),
        (55660, "grau inteiro\n(±55,7 km)", "#c05621", -0.55, "top"),
    ]
    for x, label, color, dy, va in markers:
        ax.plot([x, x], [0, dy], color=color, linewidth=1.4, zorder=3)
        ax.plot(x, 0, "o", color=color, markersize=7, zorder=4)
        ax.text(x, dy + (0.08 if dy > 0 else -0.08), label, ha="center",
                va=va, fontsize=11.5, color=color)

    ax.text(0.015, 1.02, "O que medimos (pegada)", transform=ax.transAxes,
            fontsize=13, color=FOREST, fontweight="bold", va="bottom")
    ax.text(0.42, 1.02, "Incerteza de ONDE está a pegada (coordenada arredondada)",
            transform=ax.transAxes, fontsize=13, color="#c05621",
            fontweight="bold", va="bottom")

    ax.set_xlim(15, 200_000)
    ax.set_ylim(-1.35, 1.45)
    ax.set_autoscalex_on(False)
    ax.set_autoscaley_on(False)
    ax.axis("off")
    fig.text(0.02, 0.90, "Escalas: pegada × pixel × arredondamento da coordenada",
             fontsize=16, color=TEXT, fontweight="bold")
    fig.text(0.5, 0.06,
             "Escala logarítmica (metros). A pegada tem ~2–3 pixels de largura; "
             "o arredondamento da coordenada pode ser dezenas de vezes maior.",
             ha="center", fontsize=12, color=EDGE)
    fig.subplots_adjust(left=0.03, right=0.98, top=0.80, bottom=0.16)
    path = out / "ifn_metodologia_3_escalas.png"
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)
    return path


def figura_4(out: Path) -> Path:
    """Como a composição é calculada: pegada sobre pixels e polígono IBGE."""
    from matplotlib.patches import Polygon as MplPolygon

    fig, ax = plt.subplots(figsize=(9.8, 9.4))
    ax.set_aspect("equal")
    ax.set_xlim(-115, 115)
    ax.set_ylim(-105, 100)
    ax.axis("off")

    # grade de pixels de 30 m
    for v in range(-90, 91, 30):
        ax.plot([v, v], [-90, 90], color=GRID, linewidth=0.8, zorder=1)
        ax.plot([-90, 90], [v, v], color=GRID, linewidth=0.8, zorder=1)

    # classes ilustrativas dos pixels (verde=floresta, laranja=savana,
    # amarelo=pastagem), só para mostrar que a pegada cruza classes
    pattern = [
        (FOREST, FOREST, FOREST, SAVANNA, SAVANNA, SAVANNA),
        (FOREST, FOREST, FOREST, SAVANNA, SAVANNA, SAVANNA),
        (FOREST, FOREST, FOREST, SAVANNA, SAVANNA, SAVANNA),
        (PASTURE, PASTURE, FOREST, SAVANNA, SAVANNA, SAVANNA),
        (PASTURE, PASTURE, FOREST, FOREST, SAVANNA, SAVANNA),
        (PASTURE, PASTURE, PASTURE, FOREST, SAVANNA, SAVANNA),
    ]
    xs = list(range(-90, 90, 30))
    ys = list(range(90, -90, -30))
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            ax.add_patch(Rectangle((x, y - 30), 30, 30,
                                   facecolor=pattern[j][i], alpha=0.28,
                                   edgecolor="none", zorder=0))

    # limite IBGE (exemplo): vegetação natural à esquerda
    ibge = MplPolygon([(-95, -88), (-20, -88), (-10, -40), (-30, 10),
                       (-25, 60), (-95, 88)], closed=True, fill=False,
                      edgecolor="#111827", linestyle="--", linewidth=2.2,
                      zorder=7)
    ax.add_patch(ibge)

    _draw_cross(ax, face="none")
    _draw_grid(ax)

    ax.annotate("pegada (Cruz de Malta)", xy=(60, 0), xytext=(72, 78),
                fontsize=12, color=EDGE, ha="left",
                arrowprops=dict(arrowstyle="->", color=EDGE, lw=1.4))
    ax.annotate("pixels MapBiomas de 30 m", xy=(45, -75), xytext=(-110, -100),
                fontsize=12, color=EDGE, ha="left",
                arrowprops=dict(arrowstyle="->", color=EDGE, lw=1.2))
    ax.annotate("limite do IBGE (exemplo)", xy=(-35, 20), xytext=(15, -100),
                fontsize=12, color="#111827", ha="left",
                arrowprops=dict(arrowstyle="->", color="#111827", lw=1.2,
                                linestyle="--"))
    ax.text(0, 95, "Como a composição é calculada",
            fontsize=16, color=TEXT, ha="center", fontweight="bold")
    fig.text(0.5, 0.03,
             "Cada pixel tocado pela pegada entra com o peso da ÁREA da pegada "
             "dentro dele.\nA classe do pixel NÃO é atribuída à parcela: a "
             "composição é um atributo da unidade amostral.",
             ha="center", fontsize=11.5, color=TEXT)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.94, bottom=0.10)
    path = out / "ifn_metodologia_4_composicao.png"
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", default="docs/figuras")
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = [figura_1(out), figura_2(out), figura_3(out), figura_4(out)]
    for p in paths:
        print(f"gerado: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
