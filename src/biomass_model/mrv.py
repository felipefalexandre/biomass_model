"""Verificações de QA/MRV para produtos de biomassa (G3/G4/G6 de docs/44)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def check_predictions(
    csv_path: str | Path,
    out: str | Path | None = None,
    *,
    value_col: str = "pred",
    lo_col: str | None = "lo",
    hi_col: str | None = "hi",
    obs_col: str | None = "agbd",
    class_col: str | None = "mapbiomas_class",
    aoa_col: str | None = "aoa_inside",
    domain_classes: tuple[int, ...] = (3, 4),
    max_agbd: float = 600.0,
) -> dict[str, Any]:
    """Checa consistência mínima de uma tabela de predições.

    Não substitui validação de campo (G2) nem auditoria (G7); cobre G3 (incerteza, quando
    disponível), G4 (estratificação/domínio) e G6 (QA/QC).
    """
    df = pd.read_csv(csv_path)
    checks: list[dict[str, Any]] = []

    def add(gate, name, status, detail):
        checks.append({"gate": gate, "check": name, "status": status, "detail": detail})

    if value_col not in df:
        add("G6", "coluna de valor", "fail", f"{value_col} ausente")
        result = {"csv": str(csv_path), "checks": checks, "status": "fail"}
        if out:
            Path(out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return result

    y = pd.to_numeric(df[value_col], errors="coerce").to_numpy()
    add("G6", "valores finitos", "pass" if np.isfinite(y).all() else "fail",
        f"{int(np.sum(~np.isfinite(y)))} não finitos de {len(y)}")
    below = int(np.sum(y[np.isfinite(y)] < 0))
    above = int(np.sum(y[np.isfinite(y)] > max_agbd))
    add("G6", "faixa de AGBD", "pass" if (below + above) == 0 else "warn",
        f"{below} <0; {above} >{max_agbd}")

    key_cols = [c for c in ("pixel_row", "pixel_col", "year") if c in df.columns]
    if key_cols:
        dup = int(df.duplicated(subset=key_cols).sum())
        add("G6", "duplicatas espaciais/temporais", "pass" if dup == 0 else "fail",
            f"{dup} duplicatas em {key_cols}")
    else:
        add("G6", "chave espacial/temporal", "warn", "sem pixel_row/pixel_col/year")

    if class_col and class_col in df.columns:
        counts = df[class_col].value_counts().to_dict()
        in_dom = df[class_col].isin(domain_classes).mean()
        add("G4", "cobertura de domínio", "pass" if in_dom > 0.99 else "warn",
            f"fração no domínio {in_dom:.3f}; classes {counts}")

    if aoa_col and aoa_col in df.columns:
        frac = float(df[aoa_col].astype(bool).mean())
        add("G4", "fração dentro da AOA", "pass" if frac >= 0.80 else "warn", f"{frac:.3f}")

    if lo_col and hi_col and lo_col in df and hi_col in df and obs_col and obs_col in df:
        lo = pd.to_numeric(df[lo_col], errors="coerce")
        hi = pd.to_numeric(df[hi_col], errors="coerce")
        obs = pd.to_numeric(df[obs_col], errors="coerce")
        ok = np.isfinite(lo) & np.isfinite(hi) & np.isfinite(obs)
        cov = float(((obs >= lo) & (obs <= hi))[ok].mean()) if ok.any() else np.nan
        width = float((hi - lo)[ok].mean()) if ok.any() else np.nan
        add("G3", "cobertura IC", "pass" if 0.85 <= cov <= 0.95 else "warn",
            f"cobertura={cov:.3f}; largura média={width:.1f}; n={int(ok.sum())}")
    else:
        add("G3", "intervalo de incerteza", "warn", "colunas lo/hi/obs ausentes")

    for gate, name in (("G1", "proveniência"), ("G2", "validação de campo"),
                       ("G5", "reprodutibilidade"), ("G7", "auditoria"),
                       ("G0", "escopo/model card")):
        add(gate, name, "manual", "requer artefato externo (manifesto/relatório/ADR)")

    statuses = {c["status"] for c in checks}
    status = "fail" if "fail" in statuses else ("warn" if "warn" in statuses else "pass")
    result = {"csv": str(csv_path), "n": int(len(df)), "status": status, "checks": checks}
    if out:
        Path(out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result
