import numpy as np
import pandas as pd
from shapely.geometry import Point

from biomass_model.inventory.adapters import (
    load_ifn_panel,
    load_ornl_site,
    load_plos2018,
)
from biomass_model.inventory.schema import (
    normalize_observations,
    read_observations,
    validate_observations,
    write_observations,
)


def _row(**extra):
    base = {
        "observation_id": "test:1",
        "source": "test",
        "source_version": "1",
        "observation_type": "field",
        "reference_date": "2020-01-01",
        "geometry_wkt": Point(-50, -10).wkt,
        "crs": "EPSG:4326",
        "lon": -50,
        "lat": -10,
        "location_accuracy_m": 10,
        "support_area_ha": 1.0,
        "biome": "Cerrado",
        "fitofisionomia": "Cerrado sensu stricto",
        "fitofisionomia_group": "savanna",
        "mapbiomas_class": 4,
        "agb_mg_ha": 20.0,
        "agb_uncertainty_mg_ha": 2.0,
        "uncertainty_type": "se",
        "method": "field",
        "allometric_equation": "Chave2005",
        "quality_flags": "",
        "license": "CC BY",
        "citation": "test",
        "model_status": "validation",
        "notes": "",
    }
    base.update(extra)
    return base


def test_schema_validate_and_roundtrip(tmp_path):
    df = normalize_observations(pd.DataFrame([_row()]))
    report = validate_observations(df)
    assert not report["errors"]
    out = write_observations(df, tmp_path / "obs.csv")
    back = read_observations(out)
    assert len(back) == 1
    assert back.loc[0, "agb_mg_ha"] == 20.0
    assert back.loc[0, "geometry_wkt"].startswith("POINT")


def test_schema_flags_duplicates_and_negative_agb():
    df = normalize_observations(pd.DataFrame([_row(), _row(agb_mg_ha=-1)]))
    report = validate_observations(df)
    assert any("duplicados" in e for e in report["errors"])
    assert any("negativa" in e for e in report["errors"])


def test_plos_adapter(tmp_path):
    columns = [
        "Site Number", "Location name", "State", "Ecoregion",
        "Longitude (decimal)", "Latitude (decimal)", "Tree  Density (ind ha-1)",
        "Basal_area (m2 ha-1)", "Biomass (ton ha-1)",
        "BiomassInferior  95% CIL (ton ha-1)",
        "BiomassSuperior 95% CIL (ton ha-1)", "Inventory date", "Reference",
    ]
    values = [1, "Local", "GO", "PLANALTO CENTRAL", -47.6, -15.2, 100, 2.0,
              10.0, 8.0, 12.0, "2012-09-01", "ref"]
    df = pd.DataFrame([values], columns=columns)
    path = tmp_path / "s003.xlsx"
    df.to_excel(path, index=False)
    out = load_plos2018(path)
    assert len(out) == 1
    row = out.iloc[0]
    assert row["observation_type"] == "field"
    assert np.isclose(row["agb_mg_ha"], 10.0)
    assert np.isclose(row["agb_uncertainty_mg_ha"], 2.0)
    assert row["geometry_wkt"].startswith("POINT")


def test_ifn_adapter_chooses_equation_and_converts_units(tmp_path):
    path = tmp_path / "biomassa.csv"
    text = (
        "bioma;uf;lon_pc;lat_pc;ua;n_subunidades;sanidade;classe_uso_da_terra;"
        "tipologia_da_vegetacao;equacoes;area_ha;agb_media_kg_por_ha;agb_variancia_por_ua\n"
        "Cerrado;Goiás;-50,4;-15,84;GO_1;2;Vivas;Savana;Savana;AGB_Chave;0,1;25950,56064;100\n"
        "Cerrado;Goiás;-50,4;-15,84;GO_1;2;Vivas;Savana;Savana;Eq.183;0,1;28173,67284;100\n"
    )
    path.write_text(text, encoding="utf-8")
    out = load_ifn_panel(path)
    assert len(out) == 1
    row = out.iloc[0]
    assert row["allometric_equation"] == "AGB_Chave"
    assert np.isclose(row["agb_mg_ha"], 25.95056064)
    assert np.isclose(row["agb_uncertainty_mg_ha"], np.sqrt(100 / 2) / 1000)
    assert np.isclose(row["location_accuracy_m"], 11000)


def test_ornl_adapter_tree_measurements(tmp_path):
    path = tmp_path / "TST_A01_2009_Inventory.csv"
    pd.DataFrame({
        "area": ["TST_A01", "TST_A01", "TST_A01"],
        "transect": ["T1", "T1", "T2"],
        "DBH_09": [20, 10, 30],
        "Htot_09": [10, 8, 20],
        "WSD_09": [0.6, 0.5, 0.7],
        "dead_09": ["A", "D", "A"],
        "type": ["O", "O", "O"],
    }).to_csv(path, index=False)
    out = load_ornl_site(path)
    assert len(out) == 1
    row = out.iloc[0]
    assert row["source"] == "ORNL_SLB"
    assert row["agb_mg_ha"] > 0
    assert np.isfinite(row["agb_uncertainty_mg_ha"])
    assert "ornl_ddls" in row["quality_flags"]
