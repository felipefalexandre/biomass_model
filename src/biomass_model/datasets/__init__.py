"""Aquisicao de dados do projeto.

Cada modulo expoe uma funcao `fetch_*` que baixa/recorta o dado, grava o
manifesto de proveniencia e devolve um resumo. O CLI (`biomass_model.cli`)
e o ponto de entrada recomendado.
"""

from __future__ import annotations

__all__ = ["s1", "s2", "landsat", "dem", "era5", "gedi", "sites"]
