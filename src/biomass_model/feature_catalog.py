"""Catalogo executavel de features de biomassa (docs/62).

O catalogo em ``data/reference/features_biomassa.csv`` descreve grupos, fontes,
prioridade e o status ADR de cada feature. Este modulo transforma o documento
em contrato verificavel:

- valida esquema, status e unicidade dos nomes;
- seleciona conjuntos de features por grupo e prioridade;
- **exclui sempre** o que o ADR-0022/0027 veda como feature (GEDI, LiDAR,
  ICESat-2) e trata experimental (SOC) como opt-in explicito;
- calcula um ``feature_set_hash`` estavel para o registro de modelos
  (ADR-0033), permitindo auditar qual conjunto treinou cada challenger.

O hash e do conjunto declarado no catalogo (grupo + feature + status +
prioridade), nao dos valores extraidos: ele identifica a *definicao* do
conjunto, nao a execucao.
"""

from __future__ import annotations

import hashlib
import unicodedata
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

REQUIRED_COLUMNS = (
    "grupo", "feature", "descricao", "fonte", "calculo", "uso_literatura",
    "disponivel_inferencia", "status_adr", "prioridade", "observacao",
)

ALLOWED_STATUS = {
    "permitida",
    "permitida_experimental",
    "vedada_como_feature",
}

FORBIDDEN_STATUS = "vedada_como_feature"
EXPERIMENTAL_STATUS = "permitida_experimental"


def _normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.casefold().split())


def load_catalog(path: str | Path) -> pd.DataFrame:
    """Le e valida o catalogo; falha explicitamente em esquema/status invalido."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    catalog = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in catalog.columns]
    if missing:
        raise ValueError(f"catalogo sem colunas obrigatorias: {missing}")

    catalog = catalog.copy()
    catalog["feature"] = catalog["feature"].astype(str).str.strip()
    catalog["grupo"] = catalog["grupo"].astype(str).str.strip()
    catalog["status_adr"] = catalog["status_adr"].astype(str).str.strip()
    duplicated = catalog.loc[catalog["feature"].duplicated(), "feature"].tolist()
    if duplicated:
        raise ValueError(f"features duplicadas no catalogo: {sorted(set(duplicated))}")

    invalid = catalog.loc[~catalog["status_adr"].isin(ALLOWED_STATUS), "status_adr"]
    if len(invalid):
        raise ValueError(
            f"status_adr invalido: {sorted(invalid.unique())}; "
            f"permitidos: {sorted(ALLOWED_STATUS)}"
        )

    catalog["prioridade"] = pd.to_numeric(catalog["prioridade"], errors="coerce")
    if catalog["prioridade"].isna().any() or not catalog["prioridade"].between(0, 3).all():
        raise ValueError("prioridade deve ser inteiro entre 0 e 3")

    forbidden = catalog["status_adr"].eq(FORBIDDEN_STATUS)
    if (catalog.loc[forbidden, "prioridade"] != 0).any():
        raise ValueError("features vedadas como feature devem ter prioridade 0")
    if catalog.loc[~forbidden, "prioridade"].eq(0).any():
        raise ValueError("somente features vedadas podem ter prioridade 0")

    return catalog


def select_features(
    catalog: pd.DataFrame,
    *,
    groups: Iterable[str] | None = None,
    max_priority: int | None = None,
    include_experimental: bool = False,
) -> pd.DataFrame:
    """Seleciona features permitidas, por grupo e prioridade maxima.

    ``include_experimental`` e obrigatorio para incluir ``permitida_experimental``
    (hoje apenas SOC), que exige ablacao e checagem de circularidade.
    """
    statuses = {"permitida"}
    if include_experimental:
        statuses.add(EXPERIMENTAL_STATUS)
    selected = catalog.loc[catalog["status_adr"].isin(statuses)].copy()

    if groups:
        wanted = {_normalize_text(g) for g in groups}
        mask = selected["grupo"].map(lambda value: _normalize_text(value) in wanted)
        selected = selected.loc[mask]
        if not len(selected):
            available = sorted(catalog["grupo"].unique())
            raise ValueError(
                f"nenhum grupo selecionado; grupos disponiveis: {available}"
            )

    if max_priority is not None:
        selected = selected.loc[selected["prioridade"] <= int(max_priority)]

    return selected.sort_values(["prioridade", "grupo", "feature"]).reset_index(drop=True)


def feature_set_hash(features: pd.DataFrame) -> str:
    """Hash estavel da definicao do conjunto (ordem independente)."""
    rows = features.sort_values(["grupo", "feature"])
    payload = "\n".join(
        f"{row.grupo}|{row.feature}|{row.status_adr}|{int(row.prioridade)}"
        for row in rows.itertuples(index=False)
    )
    return hashlib.sha256(f"feature_set_v1\n{payload}".encode("utf-8")).hexdigest()


def summarize(
    catalog: pd.DataFrame,
    selected: pd.DataFrame,
    *,
    include_experimental: bool = False,
) -> dict[str, Any]:
    """Resumo auditavel do conjunto selecionado e do que ficou de fora."""
    selected_names = set(selected["feature"])
    excluded = catalog.loc[~catalog["feature"].isin(selected_names)]

    def _reason(row) -> str:
        if row.status_adr == FORBIDDEN_STATUS:
            return "vedada_como_feature"
        if row.status_adr == EXPERIMENTAL_STATUS and not include_experimental:
            return "experimental_nao_habilitada"
        return "fora_do_filtro"

    reasons = {str(row.feature): _reason(row) for row in excluded.itertuples(index=False)}
    return {
        "n_catalogo": int(len(catalog)),
        "n_selecionadas": int(len(selected)),
        "feature_set_hash": feature_set_hash(selected),
        "por_grupo": {
            str(k): int(v)
            for k, v in selected.groupby("grupo").size().items()
        },
        "por_prioridade": {
            str(int(k)): int(v)
            for k, v in selected.groupby("prioridade").size().items()
        },
        "excluidas": reasons,
        "features": selected["feature"].tolist(),
    }
