"""Baixa janelas S2 e DEM para as observacoes do target (piloto de features).

Uso:
  python tools/fetch_target_features.py \
    --observations data/processed/features/sample_obs.csv \
    --out-dir data/processed/features/rasters \
    --size 256 --half 0.02

Regras:
- S2: tenta o ano do inventario e, se nao houver cena com nuvem aceitavel,
  anos adjacentes (±1, ±2); registra o ano efetivamente usado;
- DEM: Copernicus GLO-30 em EPSG:4326, janela de ~4 km;
- idempotente: pula arquivos existentes e nao vazios;
- grava `fetch_status.csv` a cada site (progresso duravel);
- nao baixa nada se a linha nao tiver lon/lat/ano.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd

from biomass_model.datasets.dem import fetch_dem
from biomass_model.datasets.s2 import fetch_window


def _try_s2(lon: float, lat: float, year: int, out: Path, *,
            size: int, max_cloud: float) -> dict | None:
    for delta in (0, -1, 1, -2, 2):
        candidate = year + delta
        start, end = f"{candidate}-01-01", f"{candidate}-12-31"
        try:
            return fetch_window(
                lon, lat, start, end, out, size=size,
                max_cloud=max_cloud, manifest=False,
            )
        except Exception:
            continue
    return None


def _with_retries(func, *args, attempts: int = 3, **kwargs):
    last = None
    for attempt in range(attempts):
        try:
            return func(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - falha de rede e esperada
            last = exc
            time.sleep(2 * (attempt + 1))
    raise last


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--observations", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--size", type=int, default=256,
                    help="lado da janela S2 em pixels de 10 m (256 ~ 2,6 km)")
    ap.add_argument("--half", type=float, default=0.02,
                    help="meia-janela do DEM em graus (~2,2 km)")
    ap.add_argument("--max-cloud", type=float, default=80.0)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--only", default=None,
                    help="lista de sites separada por virgula")
    ap.add_argument("--status-file", default=None,
                    help="CSV de status (padrao: <out-dir>/fetch_status.csv)")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    table = pd.read_csv(args.observations)
    required = {"site", "lon", "lat", "reference_date"}
    missing = sorted(required - set(table.columns))
    if missing:
        raise SystemExit(f"observacoes sem colunas: {missing}")
    if args.only:
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
        table = table[table["site"].astype(str).isin(wanted)]
    if args.limit:
        table = table.head(args.limit)

    out_dir = Path(args.out_dir)
    s2_dir, dem_dir = out_dir / "s2", out_dir / "dem"
    s2_dir.mkdir(parents=True, exist_ok=True)
    dem_dir.mkdir(parents=True, exist_ok=True)
    status_path = (
        Path(args.status_file) if args.status_file
        else out_dir / "fetch_status.csv"
    )
    status_path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []

    for pos, (_, row) in enumerate(table.iterrows(), start=1):
        site = str(row["site"])
        lon, lat = float(row["lon"]), float(row["lat"])
        year = int(str(row["reference_date"])[:4])
        s2_path = s2_dir / f"{site}.tif"
        dem_path = dem_dir / f"{site}.tif"
        record = {"site": site, "lon": lon, "lat": lat,
                  "year_target": year, "s2_year": None, "s2_item": None,
                  "s2_cloud": None, "s2_ok": False, "dem_ok": False,
                  "error": ""}
        try:
            if args.overwrite or not (s2_path.exists() and s2_path.stat().st_size > 0):
                result = _try_s2(lon, lat, year, s2_path, size=args.size,
                                 max_cloud=args.max_cloud)
                if result is None:
                    raise RuntimeError("sem cena S2 em ±2 anos")
                record.update({
                    "s2_year": int(result["datetime"][:4]),
                    "s2_item": result.get("item_id"),
                    "s2_cloud": result.get("cloud_cover"),
                    "s2_ok": True,
                })
            else:
                record["s2_ok"] = True
            if args.overwrite or not (dem_path.exists() and dem_path.stat().st_size > 0):
                _with_retries(fetch_dem, lon, lat, dem_path,
                              half=args.half, manifest=False)
            record["dem_ok"] = True
        except Exception as exc:  # noqa: BLE001
            record["error"] = f"{type(exc).__name__}: {exc}"
        rows.append(record)
        pd.DataFrame(rows).to_csv(status_path, index=False, encoding="utf-8")
        print(f"[{pos}/{len(table)}] {site} s2={record['s2_ok']} "
              f"({record['s2_year']}) dem={record['dem_ok']} "
              f"{record['error'][:80]}", flush=True)

    status = pd.DataFrame(rows)
    print("\nresumo:")
    print(status[["s2_ok", "dem_ok"]].sum().to_string())
    print(f"status: {status_path}")
    return 0 if status["s2_ok"].all() and status["dem_ok"].all() else 1


if __name__ == "__main__":
    raise SystemExit(main())
