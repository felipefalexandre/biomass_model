import pandas as pd
from shapely.geometry import Point

from biomass_model.inventory.schema import normalize_observations
from biomass_model.inventory.store import ObservationStore


def _frame(ids, agb=20.0, source="TEST", version="1"):
    rows = []
    for obs_id in ids:
        rows.append({
            "observation_id": obs_id,
            "site": obs_id,
            "source": source,
            "source_version": version,
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
            "agb_mg_ha": agb,
            "agb_uncertainty_mg_ha": 2.0,
            "uncertainty_type": "se",
            "method": "field",
            "allometric_equation": "",
            "quality_flags": "",
            "license": "CC BY",
            "citation": "test",
            "model_status": "validation",
            "notes": "",
        })
    return normalize_observations(pd.DataFrame(rows))


def test_store_is_idempotent_and_replaces_source(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text("a,b\n1,2\n", encoding="utf-8")
    store = ObservationStore(tmp_path / "store")

    first = store.ingest(_frame(["a", "b"]), source_path=source, license="CC BY")
    assert first["status"] == "ingested"
    assert first["rows_total"] == 2

    second = store.ingest(_frame(["a", "b"]), source_path=source, license="CC BY")
    assert second["status"] == "skipped"
    assert second["rows_total"] == 2

    source.write_text("a,b\n1,3\n", encoding="utf-8")
    third = store.ingest(_frame(["a", "b"], agb=30.0), source_path=source, license="CC BY")
    assert third["status"] == "ingested"
    table = store.read()
    assert len(table) == 2
    assert set(table["agb_mg_ha"]) == {30.0}
    summary = store.summary()
    assert summary["rows"] == 2
