"""Registro JSON de modelos candidatos e champions."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

REGISTRY_FILE = "registry.json"
VALID_STATUS = {"challenger", "champion", "retired"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_registry(registry_dir: str | Path) -> dict[str, Any]:
    path = Path(registry_dir) / REGISTRY_FILE
    if not path.exists():
        return {"version": 1, "models": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if "models" not in data:
        data["models"] = []
    return data


def _save_registry(registry_dir: str | Path, data: dict[str, Any]) -> Path:
    root = Path(registry_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / REGISTRY_FILE
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    tmp.replace(path)
    return path


def _metrics_summary(metrics: dict[str, Any]) -> dict[str, Any]:
    overall = metrics.get("overall", {})
    keys = ("n", "r2", "rmse", "mae", "medae", "bias", "rmse_relative", "mae_relative")
    return {key: overall.get(key) for key in keys if key in overall}


def register_model(
    metrics_path: str | Path,
    registry_dir: str | Path,
    *,
    model_id: str | None = None,
    family: str = "field_first",
    status: str = "challenger",
    notes: str = "",
) -> dict[str, Any]:
    if status not in VALID_STATUS:
        raise ValueError(f"status inválido: {status}")
    metrics_file = Path(metrics_path)
    metrics = json.loads(metrics_file.read_text(encoding="utf-8"))
    model_id = model_id or metrics_file.stem.replace(".metrics", "")
    metrics_hash = _sha256(metrics_file)
    if metrics_file.name.endswith(".metrics.json"):
        base = metrics_file.with_name(metrics_file.name[:-len(".metrics.json")])
    else:
        base = metrics_file.with_suffix("")
    model_path = base.with_suffix(".joblib")
    predictions_path = base.parent / f"{base.name}.predictions.csv"

    registry = load_registry(registry_dir)
    existing = next((m for m in registry["models"] if m["model_id"] == model_id), None)
    record = {
        "model_id": model_id,
        "family": family,
        "status": status,
        "created_at": _now(),
        "metrics_path": str(metrics_file.resolve()),
        "metrics_sha256": metrics_hash,
        "model_path": str(model_path.resolve()) if model_path.exists() else None,
        "predictions_path": str(predictions_path.resolve()) if predictions_path.exists() else None,
        "target": metrics.get("target", "agb_mg_ha"),
        "n": metrics.get("n"),
        "n_features": metrics.get("n_features") or len(metrics.get("features", [])),
        "cv_mode": metrics.get("cv_mode"),
        "metrics": _metrics_summary(metrics),
        "notes": notes,
    }
    if existing:
        record["created_at"] = existing.get("created_at", record["created_at"])
        record["history"] = existing.get("history", []) + [{
            "event": "re-registered", "at": _now(), "status": status,
            "metrics_sha256": metrics_hash,
        }]
        record["status"] = existing.get("status", status) if status == "challenger" else status
        registry["models"] = [record if m["model_id"] == model_id else m for m in registry["models"]]
    else:
        record["history"] = [{"event": "registered", "at": _now(), "status": status}]
        registry["models"].append(record)
    registry["updated_at"] = _now()
    path = _save_registry(registry_dir, registry)
    return {"registry": str(path), "model": record}


def list_models(registry_dir: str | Path, *, family: str | None = None) -> pd.DataFrame:
    registry = load_registry(registry_dir)
    rows = []
    for model in registry["models"]:
        if family and model.get("family") != family:
            continue
        row = {
            "model_id": model.get("model_id"),
            "family": model.get("family"),
            "status": model.get("status"),
            "target": model.get("target"),
            "n": model.get("n"),
            "n_features": model.get("n_features"),
            "cv_mode": model.get("cv_mode"),
            "created_at": model.get("created_at"),
        }
        row.update(model.get("metrics", {}))
        rows.append(row)
    return pd.DataFrame(rows)


def compare_models(
    registry_dir: str | Path,
    *,
    metric: str = "rmse",
    family: str | None = None,
    ascending: bool = True,
) -> pd.DataFrame:
    table = list_models(registry_dir, family=family)
    if table.empty or metric not in table.columns:
        return table
    return table.sort_values(metric, ascending=ascending).reset_index(drop=True)


def promote_model(
    registry_dir: str | Path,
    model_id: str,
    *,
    reason: str = "",
) -> dict[str, Any]:
    registry = load_registry(registry_dir)
    target = next((m for m in registry["models"] if m["model_id"] == model_id), None)
    if target is None:
        raise KeyError(f"modelo {model_id!r} não registrado")
    family = target.get("family")
    demoted = []
    for model in registry["models"]:
        if model.get("family") != family or model is target:
            continue
        if model.get("status") == "champion":
            model["status"] = "retired"
            model.setdefault("history", []).append({
                "event": "demoted", "at": _now(), "by": model_id, "reason": reason,
            })
            demoted.append(model["model_id"])
    target["status"] = "champion"
    target.setdefault("history", []).append({
        "event": "promoted", "at": _now(), "reason": reason, "demoted": demoted,
    })
    registry["updated_at"] = _now()
    path = _save_registry(registry_dir, registry)
    return {"registry": str(path), "promoted": model_id, "demoted": demoted}
