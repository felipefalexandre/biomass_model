import numpy as np

from biomass_model.allometry import chave2005, palm_agb, tree_agb
from biomass_model.stratification import (
    classify_fitofisionomia,
    load_crosswalk,
    normalize_name,
    sample_fitofisionomia_vector,
)


def test_chave2005_known_value():
    assert np.isclose(chave2005(20, 10, 0.6), 0.0509 * 0.6 * 400 * 10 / 1000)


def test_tree_agb_life_forms():
    assert np.isclose(tree_agb(20, 10, 0.6), chave2005(20, 10, 0.6))
    assert np.isclose(tree_agb(20, life_form="P"), palm_agb(20))
    assert np.isfinite(tree_agb(10, life_form="L"))


def test_normalize_name_removes_accents_and_punctuation():
    assert normalize_name("Floresta Ombrófila Densa") == "floresta ombrofila densa"
    assert normalize_name("Cerrado Típico (sensu stricto)") == "cerrado tipico sensu stricto"


def test_crosswalk_maps_ibge_to_mapbiomas():
    table = load_crosswalk()
    assert len(table) >= 20
    forest = classify_fitofisionomia("Floresta Ombrófila Densa", biome="Amazônia", crosswalk=table)
    assert forest["mapbiomas_class"] == 3
    assert forest["fitofisionomia_group"] == "forest"
    savanna = classify_fitofisionomia("Cerrado Típico (sensu stricto)", biome="Cerrado",
                                      crosswalk=table)
    assert savanna["mapbiomas_class"] == 4
    assert savanna["fitofisionomia_group"] == "savanna"
    campestre = classify_fitofisionomia("Campo Sujo", biome="Cerrado", crosswalk=table)
    assert campestre["mapbiomas_class"] == 2
    assert campestre["fitofisionomia_group"] == "campestre"


def test_sample_fitofisionomia_vector(tmp_path):
    import geopandas as gpd
    from shapely.geometry import Point, box

    vector = tmp_path / "fit.geojson"
    gpd.GeoDataFrame(
        {"legenda_2": ["Savana Arborizada", "Floresta Ombrófila Densa"]},
        geometry=[box(-51, -16, -50, -15), box(-49, -16, -48, -15)],
        crs="EPSG:4326",
    ).to_file(vector)
    out = sample_fitofisionomia_vector(
        vector, np.array([-50.5, -48.5, -47.0]), np.array([-15.5, -15.5, -15.5]),
        attribute="legenda_2",
    )
    assert out.loc[0, "ibge_group"] == "savanna"
    assert out.loc[1, "ibge_group"] == "forest"
    assert out.loc[2, "ibge_fitofisionomia"] == ""
