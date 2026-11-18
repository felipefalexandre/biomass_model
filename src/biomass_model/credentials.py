"""Leitura de credenciais fora do repositorio.

Nenhuma funcao imprime o valor de tokens ou senhas. Os caminhos seguem a
politica de `docs/19`: credenciais ficam no perfil do usuario, nunca no repo.
"""

from __future__ import annotations

import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "biomass_model"
EARTHDATA_TOKEN_FILE = CONFIG_DIR / "earthdata_token"
CDSAPIRC = Path.home() / ".cdsapirc"


def earthdata_token() -> str | None:
    """Token Earthdata de EARTHDATA_TOKEN ou do arquivo local (sem expor)."""
    token = os.getenv("EARTHDATA_TOKEN")
    if token:
        return token.strip()
    if EARTHDATA_TOKEN_FILE.exists():
        return EARTHDATA_TOKEN_FILE.read_text(encoding="ascii").strip()
    return None


def require_earthdata() -> str:
    token = earthdata_token()
    if not token:
        raise RuntimeError(
            "Credencial Earthdata ausente. Defina EARTHDATA_TOKEN ou crie "
            f"{EARTHDATA_TOKEN_FILE} (ver docs/32)."
        )
    os.environ["EARTHDATA_TOKEN"] = token
    return token


def has_cds() -> bool:
    return CDSAPIRC.exists()


def status() -> dict[str, dict[str, object]]:
    """Estado das credenciais, sem valores sensiveis."""
    return {
        "earthdata": {
            "configured": earthdata_token() is not None,
            "source": "env" if os.getenv("EARTHDATA_TOKEN") else (
                "file" if EARTHDATA_TOKEN_FILE.exists() else None
            ),
            "path": str(EARTHDATA_TOKEN_FILE),
        },
        "cds": {
            "configured": has_cds(),
            "path": str(CDSAPIRC),
        },
    }
