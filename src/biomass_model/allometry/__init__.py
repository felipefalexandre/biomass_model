"""Alometria de árvores individuais e incerteza associada.

As equações abaixo são as já registradas no projeto (Chave et al. 2005 e as equações de
palmeira/liana usadas pelo adaptador ORNL). Elas não substituem equações locais; o domínio de
validade e a referência devem acompanhar cada uso.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np

CHAVE2005_REFERENCE = "Chave et al. 2005, Oecologia, doi:10.1007/s00442-005-0100-x"
PALM_REFERENCE = "Equação de palmeira usada no adaptador ORNL (ver docs/38)"
LIANA_REFERENCE = "Equação de liana usada no adaptador ORNL (ver docs/38)"


def chave2005(dbh_cm: float, height_m: float, wood_density_g_cm3: float) -> float:
    """AGB de árvore individual em Mg (matéria seca), equação pantropical de Chave 2005."""
    dbh = float(dbh_cm)
    height = float(height_m)
    rho = float(wood_density_g_cm3)
    if not (np.isfinite(dbh) and np.isfinite(height) and np.isfinite(rho)):
        return float("nan")
    if dbh <= 0 or height <= 0 or rho <= 0:
        return float("nan")
    return float(0.0509 * rho * dbh ** 2 * height / 1000.0)


def palm_agb(dbh_cm: float) -> float:
    dbh = float(dbh_cm)
    if not np.isfinite(dbh) or dbh <= 0:
        return float("nan")
    return float(np.exp(0.9285 * np.log(dbh ** 2) + 5.7236) * 1.05001 / 1e3)


def liana_agb(dbh_cm: float) -> float:
    dbh = float(dbh_cm)
    if not np.isfinite(dbh) or dbh <= 0:
        return float("nan")
    return float(np.exp(-1.484 + 2.657 * np.log(dbh)) / 1e3)


def tree_agb(
    dbh_cm: float,
    height_m: float | None = None,
    wood_density_g_cm3: float | None = None,
    *,
    life_form: str = "tree",
) -> float:
    """AGB individual em Mg; escolhe a equação pela forma de vida."""
    form = str(life_form or "tree").strip().upper()
    if form in {"P", "PT", "PALM", "PALMEIRA"}:
        return palm_agb(dbh_cm)
    if form in {"L", "LIANA"}:
        return liana_agb(dbh_cm)
    if height_m is None or wood_density_g_cm3 is None:
        return float("nan")
    return chave2005(dbh_cm, height_m, wood_density_g_cm3)


def tree_agb_array(
    dbh_cm: Iterable[float],
    height_m: Iterable[float],
    wood_density_g_cm3: Iterable[float],
) -> np.ndarray:
    dbh = np.asarray(list(dbh_cm), dtype="float64")
    height = np.asarray(list(height_m), dtype="float64")
    rho = np.asarray(list(wood_density_g_cm3), dtype="float64")
    out = np.full(dbh.shape, np.nan, dtype="float64")
    valid = np.isfinite(dbh) & np.isfinite(height) & np.isfinite(rho) & (dbh > 0) & (height > 0) & (rho > 0)
    out[valid] = 0.0509 * rho[valid] * dbh[valid] ** 2 * height[valid] / 1000.0
    return out


def allometric_reference(life_form: str = "tree") -> str:
    form = str(life_form or "tree").strip().upper()
    if form in {"P", "PT", "PALM", "PALMEIRA"}:
        return PALM_REFERENCE
    if form in {"L", "LIANA"}:
        return LIANA_REFERENCE
    return CHAVE2005_REFERENCE
