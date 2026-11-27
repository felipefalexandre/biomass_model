"""Testes da ponte target -> observacoes canonicas e da amostragem."""

from __future__ import annotations

import json

import pandas as pd

from biomass_model.target_observations import (
    sample_target,
    target_to_observations,
    write_observations,
)


def _target(n: int = 12) -> pd.DataFrame:
    rows = []
    for i in range(n):
        tier = "A" if i < 2 else "B"
        biome = "Amazônia" if i % 2 == 0 else "Cerrado"
        fito = "Floresta Ombrófila Densa" if biome == "Amazônia" else "Savana"
        classe = 3 if biome == "Amazônia" else 4
        rows.append({
            "ua": f"UA_{i:02d}", "tier": tier,
            "suporte": "pixel_30m" if tier == "A" else "celula_1km",
            "source": "IFN/SFB", "source_version": "teste",
            "ano": 2018, "bioma": biome, "uf": "AM", "municipio": "X",
            "fitofisionomia": fito, "tipologia": fito,
            "classe_mapbiomas": classe,
            "classe_mapbiomas_nome": "Formacao",
            "agb_min_mg_ha": 10.0, "agb_mg_ha": 20.0,
            "agb_mediana_mg_ha": 20.0, "agb_max_mg_ha": 30.0,
            "n_equacoes": 5, "spread_razao": 2.0,
            "precisao_decimais": 3 if tier == "A" else 2,
            "area_pegada_ha": 0.4, "area_celula_ha": 0.09,
            "n_repeticoes": 1, "fracao_coberta_media": 0.5,
            "mb_share_compativel": 1.0, "ibge_share_compativel": 1.0,
            "plausivel": True, "target_estimator": "mediana_entre_equacoes",
            "lon": -60.0 + i * 0.01, "lat": -10.0,
        })
    return pd.DataFrame(rows)


def test_target_to_observations_maps_schema_and_status():
    obs = target_to_observations(_target(4))
    assert len(obs) == 4
    assert {"observation_id", "geometry_wkt", "agb_mg_ha", "license",
            "model_status", "fitofisionomia_group"}.issubset(obs.columns)
    first = obs[obs["observation_id"] == "target:UA_00"].iloc[0]
    third = obs[obs["observation_id"] == "target:UA_03"].iloc[0]
    assert first["observation_id"] == "target:UA_00"
    assert first["model_status"] == "validation"  # Tier A
    assert third["model_status"] == "training"    # Tier B
    assert first["location_accuracy_m"] == 55.66
    assert third["location_accuracy_m"] == 556.6
    assert first["agb_uncertainty_mg_ha"] == 10.0
    assert first["reference_date"] == "2018-01-01"
    assert "reference_date_year_only" in first["quality_flags"]
    assert first["fitofisionomia_group"] == "forest"
    assert third["fitofisionomia_group"] == "savanna"


def test_sample_is_stratified_and_reproducible():
    target = _target(12)
    first = sample_target(target, 8, tier="B", seed=7)
    second = sample_target(target, 8, tier="B", seed=7)

    assert len(first) == 8
    assert set(first["tier"]) == {"B"}
    assert list(first["ua"]) == list(second["ua"])
    assert first.groupby(["bioma", "fitofisionomia_group"]).size().min() >= 1

    all_rows = sample_target(target, 100, seed=1)
    assert len(all_rows) == len(target)


def test_write_observations_manifest(tmp_path):
    obs = target_to_observations(_target(4))
    out = tmp_path / "obs.csv"
    manifest = tmp_path / "obs.json"
    report = write_observations(obs, out, report_path=manifest,
                                params={"sample": 4})
    assert out.exists() and manifest.exists()
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["rows"] == 4
    assert payload["by_tier"] == {"B": 2, "A": 2}
    assert report["sha256"] == payload["sha256"]
