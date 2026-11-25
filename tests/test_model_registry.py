import json

from biomass_model.model_registry import (
    compare_models,
    list_models,
    load_registry,
    promote_model,
    register_model,
)


def _metrics(path, rmse):
    data = {
        "target": "agb_mg_ha",
        "n": 10,
        "n_features": 3,
        "cv_mode": "spatial_block_buffer",
        "overall": {"n": 10, "r2": 0.1, "rmse": rmse, "mae": 1.0, "bias": 0.0},
        "features": ["a", "b", "c"],
    }
    path.write_text(json.dumps(data), encoding="utf-8")


def test_registry_register_compare_promote(tmp_path):
    registry = tmp_path / "registry"
    a = tmp_path / "model_a.metrics.json"
    b = tmp_path / "model_b.metrics.json"
    _metrics(a, 10.0)
    _metrics(b, 8.0)

    register_model(a, registry, family="field_first")
    register_model(b, registry, family="field_first")
    table = list_models(registry)
    assert set(table["model_id"]) == {"model_a", "model_b"}

    ranked = compare_models(registry, metric="rmse")
    assert ranked.iloc[0]["model_id"] == "model_b"

    result = promote_model(registry, "model_b", reason="melhor RMSE")
    assert result["promoted"] == "model_b"
    reg = load_registry(registry)
    status = {m["model_id"]: m["status"] for m in reg["models"]}
    assert status["model_b"] == "champion"
    assert status["model_a"] == "challenger"
    history = next(m for m in reg["models"] if m["model_id"] == "model_b")["history"]
    assert any(h["event"] == "promoted" for h in history)
