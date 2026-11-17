"""Seleciona tiles piloto com base na fracao das classes 3 e 4 do MapBiomas.

Uso:
    python tools/select_pilots.py --raster E:/Mapbiomas/mapbiomas_col11_2025.tif

O script le janelas pequenas em torno de centros candidatos, calcula a fracao
de pixels das classes 3 (Formacao Florestal) e 4 (Formacao Savanica) e grava um
CSV com o resultado. Nao le o raster inteiro.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CANDIDATES = [
    # nome, bioma, lon, lat
    ("manaus_terra_firme", "Amazonia", -60.00, -3.00),
    ("belterra_tapajos", "Amazonia", -54.90, -2.80),
    ("acre_rio_branco", "Amazonia", -67.60, -9.60),
    ("altamira", "Amazonia", -53.00, -6.50),
    ("brasilia_df", "Cerrado", -47.90, -15.80),
    ("chapada_veadeiros", "Cerrado", -47.60, -14.10),
    ("emas", "Cerrado", -52.90, -18.30),
    ("serra_do_cipo", "Cerrado", -43.60, -19.30),
]


def window_for_center(ds, lon: float, lat: float, size: int) -> Window:
    col = int((lon - ds.transform.c) / ds.transform.a)
    row = int((lat - ds.transform.f) / ds.transform.e)
    half = size // 2
    col_off = max(0, col - half)
    row_off = max(0, row - half)
    width = min(size, ds.width - col_off)
    height = min(size, ds.height - row_off)
    return Window(col_off, row_off, width, height)


def class_fractions(values: np.ndarray) -> dict:
    valid = values[values != 0]
    total = valid.size
    if total == 0:
        return {"valid_px": 0, "frac_3": 0.0, "frac_4": 0.0, "frac_3_4": 0.0}
    counts = np.bincount(valid.astype(np.uint8), minlength=256)
    return {
        "valid_px": int(total),
        "frac_3": float(counts[3] / total),
        "frac_4": float(counts[4] / total),
        "frac_3_4": float((counts[3] + counts[4]) / total),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raster", required=True)
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--out", default=str(ROOT / "data" / "reference" / "pilotos.csv"))
    args = parser.parse_args()

    rows = []
    with rasterio.open(args.raster) as ds:
        for name, biome, lon, lat in CANDIDATES:
            win = window_for_center(ds, lon, lat, args.size)
            values = ds.read(1, window=win)
            frac = class_fractions(values)
            rows.append(
                {
                    "nome": name,
                    "bioma": biome,
                    "lon": lon,
                    "lat": lat,
                    "window_size": args.size,
                    "col_off": int(win.col_off),
                    "row_off": int(win.row_off),
                    **frac,
                }
            )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    for r in sorted(rows, key=lambda x: (x["bioma"], -x["frac_3_4"])):
        print(
            f"{r['bioma']:9s} {r['nome']:20s} "
            f"f3={r['frac_3']:.3f} f4={r['frac_4']:.3f} f34={r['frac_3_4']:.3f}"
        )
    print(f"\nCSV: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
