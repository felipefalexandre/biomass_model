"""Sugere tiles piloto combinando adensamento do IFN com as classes 3/4 do MapBiomas.

Le a base aberta do Painel de Biomassa e Carbono (SFB/IFN, CSV com separador ';'),
agrupa os pontos em celulas de ~0,15 grau (~16 km), seleciona as celulas com mais
pontos e calcula a fracao das classes 3 e 4 do MapBiomas em uma janela ao redor do
centro da celula.

Uso:
    python tools/suggest_pilots_from_ifn.py --bioma Amazonia --raster E:/.../2025.tif
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def parse_coord(value: str) -> float:
    return float(value.replace(".", "").replace(",", "."))


def cell_key(lon: float, lat: float, step: float) -> tuple[int, int]:
    return (round(lon / step), round(lat / step))


def window_for_center(ds, lon: float, lat: float, size: int) -> Window:
    col = int((lon - ds.transform.c) / ds.transform.a)
    row = int((lat - ds.transform.f) / ds.transform.e)
    half = size // 2
    col_off = max(0, col - half)
    row_off = max(0, row - half)
    return Window(col_off, row_off, min(size, ds.width - col_off), min(size, ds.height - row_off))


def fractions(values: np.ndarray) -> tuple[float, float, float]:
    valid = values[values != 0]
    if valid.size == 0:
        return 0.0, 0.0, 0.0
    counts = np.bincount(valid.astype(np.uint8), minlength=256)
    total = valid.size
    return counts[3] / total, counts[4] / total, (counts[3] + counts[4]) / total


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=str(ROOT / "data" / "raw" / "inventarios" / "sfb" / "biomassa.csv"))
    parser.add_argument("--raster", required=True)
    parser.add_argument("--bioma", default="Amazonia", choices=["Amazonia", "Cerrado"])
    parser.add_argument("--step", type=float, default=0.15)
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--out", default=str(ROOT / "data" / "reference" / "pilotos_ifn.csv"))
    args = parser.parse_args()

    bioma = "Amazônia" if args.bioma == "Amazonia" else "Cerrado"
    cells: dict[tuple[int, int], list[tuple[float, float]]] = defaultdict(list)
    with open(args.csv, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh, delimiter=";"):
            if row["bioma"] != bioma:
                continue
            try:
                cells[cell_key(parse_coord(row["lon_pc"]), parse_coord(row["lat_pc"]), args.step)].append(
                    (parse_coord(row["lon_pc"]), parse_coord(row["lat_pc"]))
                )
            except ValueError:
                continue

    ranked = sorted(cells.items(), key=lambda kv: len(kv[1]), reverse=True)[: args.top]

    out_rows = []
    with rasterio.open(args.raster) as ds:
        for (cx, cy), pts in ranked:
            lon = cx * args.step
            lat = cy * args.step
            win = window_for_center(ds, lon, lat, args.size)
            f3, f4, f34 = fractions(ds.read(1, window=win))
            out_rows.append(
                {
                    "bioma": args.bioma,
                    "lon": round(lon, 4),
                    "lat": round(lat, 4),
                    "n_ifn": len(pts),
                    "frac_3": round(f3, 4),
                    "frac_4": round(f4, 4),
                    "frac_3_4": round(f34, 4),
                    "col_off": int(win.col_off),
                    "row_off": int(win.row_off),
                }
            )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)

    for r in out_rows[:15]:
        print(
            f"{r['bioma']:9s} lon={r['lon']:8.3f} lat={r['lat']:8.3f} "
            f"n_ifn={r['n_ifn']:5d} f3={r['frac_3']:.3f} f4={r['frac_4']:.3f} f34={r['frac_3_4']:.3f}"
        )
    print(f"\nCSV: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
