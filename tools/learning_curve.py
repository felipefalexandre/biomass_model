"""Curva de aprendizado para o modelo campo-first (E3).

Treina o mesmo protocolo em subamostras crescentes e reporta RMSE/R² do modelo e
do baseline por estrato. Serve para distinguir "falta de dados" de "falta de sinal"
antes de investir em mais features.

Uso:
  python tools/learning_curve.py \
    --csv data/processed/features/features_sample.csv \
    --out-dir data/processed/features/e3_learning_curve
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from biomass_model.training.field import train_field_model  # noqa: E402


def _stratified_sample(df: pd.DataFrame, n: int, by: list[str], seed: int) -> pd.DataFrame:
    keys = [c for c in by if c in df.columns]
    if not keys:
        return df.sample(n=min(n, len(df)), random_state=seed)
    frac = n / len(df)
    parts = []
    for _, group in df.groupby(keys, dropna=False):
        take = max(1, int(round(len(group) * frac)))
        parts.append(group.sample(n=min(take, len(group)), random_state=seed))
    sampled = pd.concat(parts).drop_duplicates("observation_id")
    if len(sampled) > n:
        sampled = sampled.sample(n=n, random_state=seed)
    return sampled


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--sizes", default="20,30,40,50,60")
    ap.add_argument("--target", default="agb_mg_ha")
    ap.add_argument("--block-size-m", type=float, default=200000.0)
    ap.add_argument("--buffer-m", type=float, default=25000.0)
    ap.add_argument("--trees", type=int, default=400)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--by", default="bioma,fitofisionomia_group")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    if args.target not in df.columns:
        raise SystemExit(f"alvo {args.target!r} ausente")
    sizes = [int(s) for s in args.sizes.split(",") if s.strip()]
    sizes = [s for s in sizes if s <= len(df)]
    if not sizes:
        raise SystemExit("nenhum tamanho valido para a amostra")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    by = [b.strip() for b in args.by.split(",") if b.strip()]

    rows = []
    for size in sizes:
        subset = _stratified_sample(df, size, by, args.seed)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            csv_path = tmp / "sample.csv"
            subset.to_csv(csv_path, index=False, encoding="utf-8")
            try:
                result = train_field_model(
                    csv_path, tmp / "model", target=args.target,
                    block_size_m=args.block_size_m, buffer_m=args.buffer_m,
                    n_estimators=args.trees, seed=args.seed,
                    min_test=3, max_folds=20,
                )
                overall, baseline = result["overall"], result["baseline"]
                rows.append({
                    "n": int(result["n"]),
                    "n_requested": size,
                    "rmse": overall.get("rmse"),
                    "r2": overall.get("r2"),
                    "bias": overall.get("bias"),
                    "rmse_baseline": baseline.get("rmse"),
                    "r2_baseline": baseline.get("r2"),
                    "cv_mode": result["cv_mode"],
                })
            except Exception as exc:  # noqa: BLE001 - runs pequenos podem falhar
                rows.append({"n": 0, "n_requested": size, "error": str(exc)})
            shutil.rmtree(tmp / "model", ignore_errors=True)

    table = pd.DataFrame(rows)
    table.to_csv(out_dir / "learning_curve.csv", index=False, encoding="utf-8")
    (out_dir / "learning_curve.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    ok = table[table["n"] > 0]
    if not ok.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(ok["n"], ok["rmse"], marker="o", color="#2b6cb0", label="RF")
        ax.plot(ok["n"], ok["rmse_baseline"], marker="s", linestyle="--",
                color="#c05621", label="baseline por estrato")
        ax.set_xlabel("UAs de treino")
        ax.set_ylabel("RMSE (Mg/ha)")
        ax.set_title("Curva de aprendizado — piloto Tier B (~1,1 km)")
        ax.legend()
        ax.grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(out_dir / "learning_curve.png", dpi=180, facecolor="white")
        plt.close(fig)
    print(table.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
