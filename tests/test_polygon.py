import numpy as np
import pandas as pd

from biomass_model.polygon import polygon_stats


def test_polygon_stats_basic(tmp_path):
    rows = []
    for r in range(10):
        for c in range(10):
            rows.append({
                "pixel_row": r, "pixel_col": c,
                "pred": 10.0 if c < 5 else 20.0,
                "mapbiomas_class": 3 if c < 5 else 4,
            })
    csv = tmp_path / "pred.csv"
    pd.DataFrame(rows).to_csv(csv, index=False)
    res = polygon_stats(csv, value_col="pred", n_boot=50)
    assert res["n_cells"] == 100
    assert np.isclose(res["mean_agbd"], 15.0)
    assert np.isclose(res["total_mg"], 15.0 * 100 * 100)
    lo, hi = res["ci90_total_mg"]
    assert lo <= res["total_mg"] <= hi
    classes = {c["class"]: c for c in res["by_class"]}
    assert classes[3]["n_cells"] == 50
    assert np.isclose(classes[4]["mean_agbd"], 20.0)


def test_polygon_stats_filter(tmp_path):
    df = pd.DataFrame({
        "pixel_row": [0, 0, 1, 1], "pixel_col": [0, 1, 0, 1],
        "pred": [5.0, 5.0, 15.0, 15.0], "box": ["a", "a", "b", "b"],
        "mapbiomas_class": [3, 3, 3, 3],
    })
    csv = tmp_path / "p.csv"
    df.to_csv(csv, index=False)
    res = polygon_stats(csv, filter_col="box", filter_value="a", n_boot=20)
    assert res["n_cells"] == 2
    assert np.isclose(res["mean_agbd"], 5.0)
