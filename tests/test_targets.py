"""Testes da consolidacao do target observado por UA (docs/61, docs/62)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import Point, box

from biomass_model.targets import (
    FORBIDDEN_TARGET_COLUMNS,
    build_target,
    consolidate_target,
)


def _meta(ua: str, *, bioma: str = "Amazônia", uf: str | None = "AC",
          municipio: str | None = "Rio Branco", area: float = 0.4,
          precisao: int = 3) -> dict:
    return {
        "ua": ua, "ano": 2020, "bioma": bioma, "uf": uf,
        "municipio": municipio, "area_pegada_ha": area,
        "precisao_decimais": precisao,
    }


def _pixel(ua: str, lon: float, agb: tuple[float, float, float]) -> dict:
    return {
        "ua": ua, "ano": 2020, "fitofisionomia": "Floresta Ombrófila Densa",
        "tipologia": "Floresta Ombrófila Densa", "classe_mapbiomas": 3,
        "classe_mapbiomas_nome": "Formacao Florestal",
        "agb_min_mg_ha": agb[0], "agb_mediana_mg_ha": agb[1],
        "agb_max_mg_ha": agb[2], "n_equacoes": 10, "precisao_decimais": 3,
        "fracao_coberta": 0.8, "spread_razao": 3.0,
        "mb_share_compativel": 1.0, "ibge_share_compativel": 1.0,
        "geometry": box(lon, -10, lon + 0.0003, -10 + 0.0003),
    }


def _cell(ua: str, lon: float, agb: tuple[float, float, float],
          area_km2: float = 1.21) -> dict:
    return {
        "ua": ua, "ano": 2020, "fitofisionomia": "Savana",
        "tipologia": "Savana", "classe_mapbiomas": 4,
        "classe_mapbiomas_nome": "Formacao Savanica",
        "agb_min_mg_ha": agb[0], "agb_mediana_mg_ha": agb[1],
        "agb_max_mg_ha": agb[2], "n_equacoes": 8, "area_celula_km2": area_km2,
        "spread_razao": 2.0, "mb_share_compativel": 1.0,
        "ibge_share_compativel": 0.9,
        "geometry": box(lon, -10, lon + 0.011, -10 + 0.011),
    }


def _write_fixture(path: Path, *, inconsistent: bool = False) -> Path:
    meta = gpd.GeoDataFrame(
        [_meta("AC_1"), _meta("AC_2"), _meta("AC_3"),
         _meta("AC_4", uf=None, municipio=None, precisao=2,
               bioma="Cerrado"),
         _meta("AC_5")],
        geometry=[Point(-60 + i, -10) for i in range(5)], crs="EPSG:4326",
    )
    agb_ac3 = (1.0, 2.0, 3.0)
    if inconsistent:
        agb_ac3 = (9.0, 2.0, 3.0)
    pixels = gpd.GeoDataFrame(
        [
            _pixel("AC_1", -60.0, (10.0, 20.0, 30.0)),
            _pixel("AC_1", -60.001, (10.0, 20.0, 30.0)),
            _pixel("AC_2", -60.002, (5.0, 15.0, 40.0)),
            _pixel("AC_3", -60.003, agb_ac3),
        ],
        crs="EPSG:4326",
    )
    cells = gpd.GeoDataFrame(
        [
            _cell("AC_3", -60.01, (7.0, 8.0, 9.0)),
            _cell("AC_4", -60.02, (100.0, 200.0, 300.0)),
            _cell("AC_5", -60.03, (600.0, 700.0, 800.0)),
        ],
        crs="EPSG:4326",
    )
    for layer, frame in (
        ("cruz_avaliada", meta), ("pixels_confirmados", pixels),
        ("celulas_confirmadas", cells),
    ):
        frame.to_file(path, layer=layer, driver="GPKG")
    return path


def test_one_row_per_ua_and_tier_precedence(tmp_path):
    gpkg = _write_fixture(tmp_path / "candidates.gpkg")
    target, report = build_target(gpkg)

    assert report["tiers"] == {"A": 3, "B": 1}
    assert report["n_uas"] == len(target) == target["ua"].nunique() == 4
    assert report["conflitos_tier_resolvidos"] == 1
    assert report["conflitos_tier_uas"] == ["AC_3"]
    assert report["pixels_consolidados"] == 4
    assert report["implausiveis_removidos"][0]["ua"] == "AC_5"
    assert sum(report["por_bioma"].values()) == report["n_uas"]
    assert sum(v["n"] for v in report["por_fitofisionomia"].values()) == report["n_uas"]

    tier_a = target.set_index("ua").loc["AC_1"]
    assert tier_a["tier"] == "A"
    assert tier_a["suporte"] == "pixel_30m"
    assert tier_a["n_repeticoes"] == 2
    assert tier_a["area_celula_ha"] == pytest.approx(0.09)

    # Tier A vence o conflito com a celula de AC_3.
    ac3 = target.set_index("ua").loc["AC_3"]
    assert ac3["tier"] == "A"
    assert ac3["agb_mg_ha"] == pytest.approx(2.0)

    ac4 = target.set_index("ua").loc["AC_4"]
    assert ac4["tier"] == "B"
    assert ac4["area_celula_ha"] == pytest.approx(121.0)
    assert ac4["uf"] == "AC"  # fallback a partir do prefixo da UA
    assert ac4["precisao_decimais"] == 2


def test_target_columns_are_leak_free(tmp_path):
    gpkg = _write_fixture(tmp_path / "candidates.gpkg")
    target, _ = build_target(gpkg)

    lower = [c.lower() for c in target.columns]
    for token in FORBIDDEN_TARGET_COLUMNS:
        assert not any(token in column for column in lower)
    assert {"lon", "lat"}.issubset(target.columns)
    assert (target["agb_mg_ha"] == target["agb_mediana_mg_ha"]).all()
    assert (target["agb_min_mg_ha"] <= target["agb_mg_ha"] + 1e-9).all()
    assert (target["agb_mg_ha"] <= target["agb_max_mg_ha"] + 1e-9).all()
    assert str(target.crs) == "EPSG:4326"


def test_biome_filter_and_report(tmp_path):
    gpkg = _write_fixture(tmp_path / "candidates.gpkg")
    amazon, report = build_target(gpkg, biomes=["Amazonia"])
    assert report["n_uas"] == 3
    assert set(amazon["bioma"]) == {"Amazônia"}

    cerrado, report_c = build_target(gpkg, biomes=["cerrado"])
    assert report_c["n_uas"] == 1
    assert set(cerrado["bioma"]) == {"Cerrado"}

    with pytest.raises(ValueError, match="nao deixou nenhuma UA"):
        build_target(gpkg, biomes=["Pampa"])


def test_inconsistent_interval_raises(tmp_path):
    gpkg = _write_fixture(tmp_path / "bad.gpkg", inconsistent=True)
    with pytest.raises(ValueError, match="intervalo de AGB inconsistente"):
        build_target(gpkg)


def test_export_writes_csv_gpkg_manifest_and_is_reproducible(tmp_path):
    gpkg = _write_fixture(tmp_path / "candidates.gpkg")
    csv_path = tmp_path / "target" / "target_uas.csv"
    gpkg_out = tmp_path / "target" / "target_uas.gpkg"
    manifest = tmp_path / "target" / "target_manifest.json"

    first = consolidate_target(
        gpkg, csv_path, gpkg_path=gpkg_out, manifest_path=manifest,
        biomes=["Amazonia"],
    )
    assert csv_path.exists() and gpkg_out.exists() and manifest.exists()
    assert first["outputs"]["rows"] == 3

    written = gpd.read_file(gpkg_out, layer="target_uas")
    assert len(written) == 3
    assert str(written.crs) == "EPSG:4326"

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["params"]["one_row_per_ua"] is True
    assert payload["params"]["tier_precedence"] == "A>B"
    assert payload["outputs"]["sha256_csv"] == first["outputs"]["sha256_csv"]

    digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    assert digest == first["outputs"]["sha256_csv"]

    second = consolidate_target(
        gpkg, csv_path, gpkg_path=gpkg_out, manifest_path=manifest,
        biomes=["Amazonia"],
    )
    assert second["outputs"]["sha256_csv"] == first["outputs"]["sha256_csv"]
