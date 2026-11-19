import numpy as np
import pandas as pd

from biomass_model.datasets.ornl import density_from_agb_area, density_from_measurements


def test_density_from_agb_area_mean_of_transects():
    df = pd.DataFrame({
        "transect": ["t1", "t1", "t2", "t2"],
        "AGB": [1.0, 1.0, 2.0, 2.0],
        "area_sampled": [0.5, 0.5, 0.5, 0.5],
    })
    r = density_from_agb_area(df)
    assert np.isclose(r["per_transect"][0], 4.0)
    assert np.isclose(r["per_transect"][1], 8.0)
    assert np.isclose(r["density_mg_ha"], 6.0)
    assert r["n_transects"] == 2


def test_density_from_measurements_chave_units():
    df = pd.DataFrame({
        "transect": ["t1"],
        "type": ["O"],
        "DBH_09": [10.0],
        "Htot_09": [10.0],
        "WSD_09": [0.5],
        "dead_09": ["A"],
    })
    r = density_from_measurements(df, "09")
    # AGB = 0.0509*0.5*100*10/1000 = 0.02545 Mg; area = 2*500*1/10000 = 0.1 ha
    assert np.isclose(r["density_mg_ha"], 0.2545, atol=1e-4)
    assert r["n_trees"] == 1
