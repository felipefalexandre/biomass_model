"""Armazenamento canônico idempotente de observações (ADR-0032)."""

from __future__ import annotations

import hashlib
import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .schema import normalize_observations, read_observations, write_observations

MANIFEST = "manifest.json"
TABLE = "observations.csv"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_signature(path: str | Path) -> str:
    p = Path(path)
    if p.is_file():
        return _sha256_file(p)
    if p.is_dir():
        digest = hashlib.sha256()
        for item in sorted(x for x in p.rglob("*") if x.is_file()):
            stat = item.stat()
            digest.update(f"{item.relative_to(p)}|{stat.st_size}|{stat.st_mtime_ns}".encode())
        return digest.hexdigest()
    raise FileNotFoundError(path)


@contextmanager
def _write_lock(path: Path, timeout: float = 60.0):
    lock = path.with_suffix(".lock")
    deadline = time.monotonic() + timeout
    fd = None
    while fd is None:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if time.monotonic() > deadline:
                raise TimeoutError(f"lock de escrita ocupado: {lock}")
            time.sleep(0.05)
    os.close(fd)
    try:
        yield
    finally:
        try:
            lock.unlink()
        except FileNotFoundError:
            pass


class ObservationStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.table_path = self.root / TABLE
        self.manifest_path = self.root / MANIFEST

    def read_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            return {"version": 1, "sources": {}, "updated_at": None}
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def read(self) -> pd.DataFrame:
        if not self.table_path.exists():
            return normalize_observations(pd.DataFrame())
        return read_observations(self.table_path)

    def ingest(
        self,
        observations: pd.DataFrame,
        *,
        source_path: str | Path,
        license: str,
        notes: str = "",
        force: bool = False,
    ) -> dict[str, Any]:
        with _write_lock(self.manifest_path):
            return self._ingest(
                observations, source_path=source_path, license=license,
                notes=notes, force=force,
            )

    def _ingest(
        self,
        observations: pd.DataFrame,
        *,
        source_path: str | Path,
        license: str,
        notes: str = "",
        force: bool = False,
    ) -> dict[str, Any]:
        frame = normalize_observations(observations)
        if frame.empty:
            raise ValueError("nenhuma observação para ingerir")
        source = str(frame["source"].iloc[0]).strip()
        version = str(frame["source_version"].iloc[0]).strip()
        signature = _source_signature(source_path)
        manifest = self.read_manifest()
        key = f"{source}:{version}"
        previous = manifest["sources"].get(key)
        if previous and previous.get("sha256") == signature and not force:
            return {
                "status": "skipped",
                "source": source,
                "version": version,
                "rows_in": int(len(frame)),
                "rows_total": int(len(self.read())),
                "reason": "mesma assinatura de fonte",
            }

        existing = self.read()
        if len(existing):
            existing = existing[~existing["observation_id"].isin(frame["observation_id"])]
        combined = normalize_observations(pd.concat([existing, frame], ignore_index=True))
        combined = combined.drop_duplicates(subset=["observation_id"], keep="last")
        write_observations(combined, self.table_path)

        manifest["sources"][key] = {
            "source": source,
            "version": version,
            "path": str(Path(source_path).resolve()),
            "sha256": signature,
            "rows": int(len(frame)),
            "license": license,
            "notes": notes,
            "ingested_at": _now(),
        }
        manifest["updated_at"] = _now()
        manifest["rows_total"] = int(len(combined))
        manifest["table_sha256"] = _sha256_file(self.table_path)
        self.manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return {
            "status": "ingested",
            "source": source,
            "version": version,
            "rows_in": int(len(frame)),
            "rows_total": int(len(combined)),
            "replaced": int(len(existing)),
            "table": str(self.table_path),
        }

    def summary(self) -> dict[str, Any]:
        table = self.read()
        if table.empty:
            return {"rows": 0, "by_source": {}, "by_biome": {}}
        return {
            "rows": int(len(table)),
            "by_source": table["source"].value_counts().to_dict(),
            "by_biome": table["biome"].value_counts().to_dict(),
            "manifest": str(self.manifest_path),
            "table": str(self.table_path),
        }
