"""Manifestos de aquisicao de dados.

Cada download grava um JSON pequeno em `data/manifests/` com parametros,
URLs, hashes e licenca. Nao inclui credenciais.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

DEFAULT_MANIFEST_DIR = Path(__file__).resolve().parents[2] / "data" / "manifests"


def sha256_file(path: str | Path, chunk: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def file_entry(path: str | Path, with_hash: bool = True) -> dict[str, Any]:
    p = Path(path)
    entry: dict[str, Any] = {
        "path": str(p),
        "bytes": p.stat().st_size,
    }
    if with_hash:
        entry["sha256"] = sha256_file(p)
    return entry


def git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[2],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return out.stdout.strip() or None
    except Exception:
        return None


def build_manifest(
    dataset: str,
    params: dict[str, Any],
    outputs: Iterable[str | Path],
    *,
    license: str | None = None,
    account: str | None = None,
    source: str | None = None,
    notes: str | None = None,
    inputs: Iterable[str | Path] = (),
    hash_outputs: bool = True,
) -> dict[str, Any]:
    return {
        "dataset": dataset,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "python": platform.python_version(),
        "argv": sys.argv,
        "params": params,
        "license": license,
        "account": account,
        "source": source,
        "notes": notes,
        "inputs": [file_entry(p) for p in inputs],
        "outputs": [file_entry(p, with_hash=hash_outputs) for p in outputs],
    }


def write_manifest(manifest: dict[str, Any], out_dir: str | Path = DEFAULT_MANIFEST_DIR) -> Path:
    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = manifest["dataset"].replace("/", "_").replace(" ", "_")
    path = directory / f"{slug}_{stamp}.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
