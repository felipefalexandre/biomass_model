"""Testes do catalogo executavel de features (docs/62)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from biomass_model.feature_catalog import (
    ALLOWED_STATUS,
    FORBIDDEN_STATUS,
    feature_set_hash,
    load_catalog,
    select_features,
    summarize,
)

CATALOG_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "reference"
    / "features_biomassa.csv"
)


def _write_catalog(path: Path, rows: list[dict]) -> Path:
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")
    return path


def _row(feature: str, *, grupo: str = "Optico S2", status: str = "permitida",
         prioridade: int = 1) -> dict:
    return {
        "grupo": grupo, "feature": feature, "descricao": "teste",
        "fonte": "teste", "calculo": "teste", "uso_literatura": "teste",
        "disponivel_inferencia": "sim", "status_adr": status,
        "prioridade": prioridade, "observacao": "",
    }


def test_real_catalog_loads_and_respects_contract():
    catalog = load_catalog(CATALOG_PATH)
    assert len(catalog) >= 50
    assert set(catalog["status_adr"]).issubset(ALLOWED_STATUS)
    forbidden = catalog[catalog["status_adr"] == FORBIDDEN_STATUS]
    assert not forbidden.empty
    assert (forbidden["prioridade"] == 0).all()
    assert catalog["feature"].is_unique


def test_default_selection_excludes_forbidden_and_experimental():
    catalog = load_catalog(CATALOG_PATH)
    selected = select_features(catalog)
    names = set(selected["feature"])

    assert not names & set(
        catalog.loc[catalog["status_adr"] == FORBIDDEN_STATUS, "feature"]
    )
    experimental = set(
        catalog.loc[catalog["status_adr"] == "permitida_experimental", "feature"]
    )
    assert not names & experimental
    assert (selected["prioridade"] >= 1).all()


def test_include_experimental_is_opt_in():
    catalog = load_catalog(CATALOG_PATH)
    selected = select_features(catalog, include_experimental=True)
    experimental = set(
        catalog.loc[catalog["status_adr"] == "permitida_experimental", "feature"]
    )
    assert experimental
    assert experimental.issubset(set(selected["feature"]))


def test_group_and_priority_filters():
    catalog = load_catalog(CATALOG_PATH)
    optical = select_features(catalog, groups=["optico s2"])
    assert set(optical["grupo"]) == {"Optico S2"}

    top = select_features(catalog, max_priority=1)
    assert (top["prioridade"] <= 1).all()

    with pytest.raises(ValueError, match="grupos disponiveis"):
        select_features(catalog, groups=["grupo inexistente"])


def test_hash_is_order_independent_and_changes_with_set():
    catalog = load_catalog(CATALOG_PATH)
    selected = select_features(catalog)
    shuffled = selected.sample(frac=1.0, random_state=7)

    assert feature_set_hash(selected) == feature_set_hash(shuffled)
    assert feature_set_hash(selected) != feature_set_hash(
        select_features(catalog, groups=["SAR S1"])
    )

    summary = summarize(catalog, selected)
    assert summary["feature_set_hash"] == feature_set_hash(selected)
    assert summary["n_selecionadas"] == len(selected)
    assert FORBIDDEN_STATUS in set(summary["excluidas"].values())


def test_exclusion_reasons_are_specific():
    catalog = load_catalog(CATALOG_PATH)
    top = select_features(catalog, max_priority=1)
    summary = summarize(catalog, top)

    assert summary["excluidas"]["GEDI L2A/L4A"] == "vedada_como_feature"
    assert summary["excluidas"]["carbono organico do solo"] == "experimental_nao_habilitada"
    permitted = catalog[
        (catalog["prioridade"] > 1) & (catalog["status_adr"] == "permitida")
    ].iloc[0]["feature"]
    assert summary["excluidas"][permitted] == "fora_do_filtro"

    experimental_with_filter = summarize(
        catalog,
        select_features(catalog, max_priority=1, include_experimental=True),
        include_experimental=True,
    )
    assert experimental_with_filter["excluidas"]["carbono organico do solo"] == "fora_do_filtro"


def test_invalid_status_and_duplicates_raise(tmp_path):
    bad_status = _write_catalog(
        tmp_path / "bad_status.csv",
        [_row("a", status="proibida")],
    )
    with pytest.raises(ValueError, match="status_adr invalido"):
        load_catalog(bad_status)

    duplicated = _write_catalog(
        tmp_path / "duplicated.csv",
        [_row("a"), _row("a")],
    )
    with pytest.raises(ValueError, match="features duplicadas"):
        load_catalog(duplicated)

    bad_priority = _write_catalog(
        tmp_path / "bad_priority.csv",
        [_row("gedi", status=FORBIDDEN_STATUS, prioridade=1)],
    )
    with pytest.raises(ValueError, match="prioridade 0"):
        load_catalog(bad_priority)
