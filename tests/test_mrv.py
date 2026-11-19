import pandas as pd

from biomass_model.mrv import check_predictions


def test_mrv_checks_pass(tmp_path):
    df = pd.DataFrame({
        "pixel_row": [0, 0, 1, 1], "pixel_col": [0, 1, 0, 1], "year": [2020] * 4,
        "pred": [10.0, 12.0, 14.0, 16.0], "agbd": [11.0, 13.0, 15.0, 17.0],
        "lo": [5.0] * 4, "hi": [20.0] * 4, "mapbiomas_class": [3, 3, 4, 4],
        "aoa_inside": [True] * 4,
    })
    csv = tmp_path / "p.csv"
    df.to_csv(csv, index=False)
    res = check_predictions(csv)
    assert res["status"] in ("pass", "warn")
    gates = {c["gate"]: c for c in res["checks"]}
    assert gates["G6"]["status"] == "pass"


def test_mrv_flags_duplicates_and_range(tmp_path):
    df = pd.DataFrame({
        "pixel_row": [0, 0], "pixel_col": [0, 0], "pred": [-1.0, 999.0],
        "mapbiomas_class": [3, 4],
    })
    csv = tmp_path / "p.csv"
    df.to_csv(csv, index=False)
    res = check_predictions(csv)
    assert res["status"] == "fail"
    names = {c["check"]: c["status"] for c in res["checks"]}
    assert names["duplicatas espaciais/temporais"] == "fail"
