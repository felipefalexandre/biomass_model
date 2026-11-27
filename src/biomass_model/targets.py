"""Consolidacao do target observado por unidade amostral (UA).

Le as camadas de candidatos confirmados (pixel de 30 m e celula de ~1,1 km) do
GeoPackage gerado por ``tools/ifn_spatial_candidates.py`` e produz **uma unica
linha por UA**, com os tres valores de AGB (min, mediana, max), o suporte de
grade e as flags de confianca.

Regras cientificas (docs/61, docs/62):

- 1 target por UA; **Tier A (pixel) tem precedencia** sobre Tier B (celula);
- os pixels de uma mesma UA sao representacoes espaciais do mesmo valor:
  entram como ``n_repeticoes``, nunca como amostras independentes;
- ``agb_mg_ha`` e a **mediana entre equacoes** (estimador do alvo); min/max
  formam a faixa de incerteza de equacao;
- nenhuma feature derivada de AGB, GEDI ou LiDAR entra na tabela;
- plausibilidade: mediana entre 0 e 500 Mg/ha (limite configuravel).

O resultado e a tabela canonica de target para treino/validacao e a base do
mapa-alvo; nao substitui a validacao independente descrita em docs/62.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

TIER_LAYERS: tuple[tuple[str, str, str], ...] = (
    ("pixels_confirmados", "A", "pixel_30m"),
    ("celulas_confirmadas", "B", "celula_1km"),
)

#: Area de um pixel de 30 m em hectares (0,3 km x 0,3 km na grade oficial).
PIXEL_AREA_HA = 30.0 * 30.0 / 10_000.0

UF_CODES = {
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS",
    "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC",
    "SE", "SP", "TO",
}

TARGET_COLUMNS = [
    "ua", "tier", "suporte", "source", "source_version", "ano", "bioma", "uf",
    "municipio", "fitofisionomia", "tipologia", "classe_mapbiomas",
    "classe_mapbiomas_nome", "agb_min_mg_ha", "agb_mg_ha",
    "agb_mediana_mg_ha", "agb_max_mg_ha", "n_equacoes", "spread_razao",
    "precisao_decimais", "area_pegada_ha", "area_celula_ha", "n_repeticoes",
    "fracao_coberta_media", "mb_share_compativel", "ibge_share_compativel",
    "plausivel", "target_estimator", "lon", "lat",
]

FORBIDDEN_TARGET_COLUMNS = ("gedi", "lidar", "icesat", "agbd_gedi")


def sha256_file(path: str | Path, chunk: int = 1 << 20) -> str:
    """SHA-256 de um arquivo, lido em blocos (sem carregar tudo em memoria)."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_columns(frame: pd.DataFrame, columns: list[str], layer: str) -> None:
    missing = [c for c in columns if c not in frame.columns]
    if missing:
        raise ValueError(f"camada '{layer}' sem colunas obrigatorias: {missing}")


def _uf_from_ua(ua: str) -> str | None:
    prefix = str(ua).split("_", 1)[0].upper()
    return prefix if prefix in UF_CODES else None


def _normalize_text(value: Any) -> str:
    """Normaliza texto para comparacao (sem acento, minusculo)."""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.casefold().split())


def _add_lonlat(frame) -> Any:
    """Adiciona lon/lat do ponto representativo de cada geometria (EPSG:4326)."""
    geometry = frame.geometry.to_crs(6933).representative_point().to_crs(4326)
    frame = frame.copy()
    frame["lon"] = geometry.x.to_numpy()
    frame["lat"] = geometry.y.to_numpy()
    return frame


def _check_interval_consistency(frame: pd.DataFrame, layer: str) -> None:
    """Garante min <= mediana <= max (erro de intervalo e bug de origem)."""
    tol = 1e-6
    bad = frame[
        (frame["agb_min_mg_ha"] > frame["agb_mediana_mg_ha"] + tol)
        | (frame["agb_mediana_mg_ha"] > frame["agb_max_mg_ha"] + tol)
    ]
    if len(bad):
        sample = bad[["ua", "agb_min_mg_ha", "agb_mediana_mg_ha", "agb_max_mg_ha"]]
        raise ValueError(
            f"intervalo de AGB inconsistente em {len(bad)} linha(s) da camada "
            f"'{layer}': {sample.head(5).to_dict(orient='records')}"
        )


def _check_constant_per_ua(frame: pd.DataFrame, column: str, layer: str) -> None:
    """Um valor de AGB por UA: pixels-irmaos nao podem divergir."""
    counts = frame.groupby("ua")[column].nunique(dropna=False)
    divergent = counts[counts > 1]
    if len(divergent):
        raise ValueError(
            f"coluna '{column}' varia dentro da UA em {len(divergent)} caso(s) "
            f"da camada '{layer}': {divergent.head(5).to_dict()}"
        )


def _aggregate_layer(gdf, layer: str, tier: str, support: str) -> pd.DataFrame:
    """Consolida os registros de uma camada em uma linha por UA."""
    _require_columns(
        gdf,
        ["ua", "ano", "fitofisionomia", "tipologia", "classe_mapbiomas",
         "classe_mapbiomas_nome", "agb_min_mg_ha", "agb_mediana_mg_ha",
         "agb_max_mg_ha", "n_equacoes", "spread_razao"],
        layer,
    )
    for column in ("agb_min_mg_ha", "agb_mediana_mg_ha", "agb_max_mg_ha"):
        _check_constant_per_ua(gdf, column, layer)
    _check_interval_consistency(gdf, layer)

    aggregations: dict[str, tuple[str, str]] = {
        "ano": ("ano", "first"),
        "fitofisionomia": ("fitofisionomia", "first"),
        "tipologia": ("tipologia", "first"),
        "classe_mapbiomas": ("classe_mapbiomas", "first"),
        "classe_mapbiomas_nome": ("classe_mapbiomas_nome", "first"),
        "agb_min_mg_ha": ("agb_min_mg_ha", "first"),
        "agb_mediana_mg_ha": ("agb_mediana_mg_ha", "first"),
        "agb_max_mg_ha": ("agb_max_mg_ha", "first"),
        "n_equacoes": ("n_equacoes", "first"),
        "spread_razao": ("spread_razao", "first"),
        "n_repeticoes": ("ua", "size"),
    }
    optional = {
        "precisao_decimais": ("precisao_decimais", "first"),
        "mb_share_compativel": ("mb_share_compativel", "first"),
        "ibge_share_compativel": ("ibge_share_compativel", "first"),
    }
    for name, spec in optional.items():
        if name in gdf.columns:
            aggregations[name] = spec
    if "fracao_coberta" in gdf.columns:
        aggregations["fracao_coberta_media"] = ("fracao_coberta", "mean")

    grouped = gdf.groupby("ua", sort=True).agg(**aggregations).reset_index()
    grouped["tier"] = tier
    grouped["suporte"] = support
    # Area da celula de GRADE (0,09 ha no pixel; area da celula de ~1,1 km no
    # Tier B). Nao confundir com ``area_pegada_ha``, o suporte da medicao.
    if support == "pixel_30m":
        grouped["area_celula_ha"] = PIXEL_AREA_HA
    elif "area_celula_km2" in gdf.columns:
        grouped["area_celula_ha"] = (
            gdf.groupby("ua", sort=True)["area_celula_km2"].first().to_numpy()
            * 100.0
        )
    else:
        grouped["area_celula_ha"] = float("nan")
    if "fracao_coberta_media" not in grouped.columns:
        grouped["fracao_coberta_media"] = float("nan")
    return grouped


def _merge_metadata(target: pd.DataFrame, gpkg: str | Path) -> pd.DataFrame:
    """Traz bioma, UF, municipio e area da pegada da camada de avaliacao."""
    import geopandas as gpd
    from pyogrio.errors import DataSourceError

    try:
        meta = gpd.read_file(gpkg, layer="cruz_avaliada")
    except DataSourceError:  # camada opcional em fixtures minimas
        return target
    keep = [c for c in ("ua", "bioma", "uf", "municipio", "area_pegada_ha",
                        "precisao_decimais")
            if c in meta.columns]
    if not keep:
        return target
    meta = meta[keep].drop_duplicates("ua")
    merged = target.merge(
        meta, on="ua", how="left", validate="one_to_one",
        suffixes=("", "_meta"),
    )
    if "precisao_decimais_meta" in merged.columns:
        fallback = merged.pop("precisao_decimais_meta")
        if "precisao_decimais" in merged.columns:
            merged["precisao_decimais"] = merged["precisao_decimais"].where(
                merged["precisao_decimais"].notna(), fallback
            )
        else:
            merged["precisao_decimais"] = fallback
    if "uf" not in merged.columns:
        merged["uf"] = pd.NA
    merged["uf"] = merged["uf"].where(
        merged["uf"].notna(), merged["ua"].map(_uf_from_ua)
    )
    return merged


def build_target(
    gpkg: str | Path,
    *,
    source: str = "IFN/SFB",
    source_version: str = "painel_biomassa_carbono_2025",
    plausibility_max: float = 500.0,
    biomes: Sequence[str] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Constroi a tabela de target (1 linha por UA) a partir do GeoPackage.

    Retorna ``(GeoDataFrame, relatorio)``. Nao escreve arquivos: use
    :func:`export_target` ou :func:`consolidate_target`.
    """
    import geopandas as gpd
    from pyogrio import list_layers

    path = Path(gpkg)
    if not path.exists():
        raise FileNotFoundError(path)
    layers = {name for name, _ in list_layers(path)}
    available = [(layer, tier, support) for layer, tier, support in TIER_LAYERS
                 if layer in layers]
    if not available:
        raise ValueError(
            f"{path} nao contem nenhuma camada de candidatos confirmados "
            f"({[l for l, _, _ in TIER_LAYERS]}); camadas: {sorted(layers)}"
        )

    parts: list[pd.DataFrame] = []
    layer_counts: dict[str, int] = {}
    support_geometry: dict[str, Any] = {}
    for layer, tier, support in available:
        gdf = _add_lonlat(gpd.read_file(path, layer=layer))
        layer_counts[layer] = int(len(gdf))
        parts.append(_aggregate_layer(gdf, layer, tier, support))
        union = gdf.groupby("ua")["geometry"].apply(lambda s: s.union_all())
        support_geometry.update(union.to_dict())

    target = pd.concat(parts, ignore_index=True)

    # Precedencia Tier A: pixels confirmados representam melhor o suporte.
    target["_tier_order"] = target["tier"].map({"A": 0, "B": 1})
    target = target.sort_values(["_tier_order", "ua"]).reset_index(drop=True)
    duplicated = target["ua"].duplicated(keep="first")
    conflicts = target.loc[duplicated, "ua"].tolist()
    target = target.loc[~duplicated].drop(columns="_tier_order")

    target = _merge_metadata(target, path)

    n_before_biome = int(len(target))
    available_biomes = sorted(target["bioma"].dropna().unique().tolist())
    if biomes:
        allowed = {_normalize_text(b) for b in biomes}
        mask = target["bioma"].map(
            lambda value: _normalize_text(value) in allowed if pd.notna(value) else False
        )
        target = target.loc[mask].copy()
        if not len(target):
            raise ValueError(
                f"filtro de bioma {list(biomes)} nao deixou nenhuma UA; "
                f"biomas disponiveis: {available_biomes}"
            )

    target["source"] = source
    target["source_version"] = source_version
    target["agb_mg_ha"] = target["agb_mediana_mg_ha"]
    target["target_estimator"] = "mediana_entre_equacoes"

    median = pd.to_numeric(target["agb_mediana_mg_ha"], errors="coerce")
    plausible = median.gt(0) & median.le(float(plausibility_max))
    rejected = target.loc[~plausible, ["ua", "agb_mediana_mg_ha"]].copy()
    rejected["motivo"] = "agb_fora_da_faixa_plausivel"
    target = target.loc[plausible].copy()
    target["plausivel"] = True

    for column in ("ano", "classe_mapbiomas", "n_equacoes", "precisao_decimais"):
        if column in target.columns:
            target[column] = pd.to_numeric(
                target[column], errors="coerce"
            ).astype("Int64")
    target["n_repeticoes"] = target["n_repeticoes"].astype("int64")

    # Ponto representativo do suporte no mapa-alvo (nao e feature).
    support_geom = gpd.GeoSeries(
        [support_geometry[ua] for ua in target["ua"]], crs="EPSG:4326"
    )
    points = support_geom.to_crs(6933).representative_point().to_crs(4326)

    target = target[[c for c in TARGET_COLUMNS if c in target.columns]]
    target["lon"] = points.x.to_numpy()
    target["lat"] = points.y.to_numpy()
    result = gpd.GeoDataFrame(target, geometry=points.to_numpy(), crs="EPSG:4326")

    forbidden = [
        c for c in result.columns
        if any(token in c.lower() for token in FORBIDDEN_TARGET_COLUMNS)
    ]
    if forbidden:
        raise AssertionError(f"target nao pode conter features vedadas: {forbidden}")

    agb = result["agb_mg_ha"].astype(float)
    report: dict[str, Any] = {
        "n_uas": int(len(result)),
        "n_uas_unicas": int(result["ua"].nunique()),
        "n_antes_filtro_bioma": n_before_biome,
        "filtro_bioma": list(biomes) if biomes else None,
        "biomas_disponiveis": available_biomes,
        "tiers": {k: int(v) for k, v in result["tier"].value_counts().items()},
        "suportes": {k: int(v) for k, v in result["suporte"].value_counts().items()},
        "camadas": layer_counts,
        "pixels_consolidados": layer_counts.get("pixels_confirmados", 0),
        "conflitos_tier_resolvidos": len(conflicts),
        "conflitos_tier_uas": conflicts,
        "implausiveis_removidos": rejected.to_dict(orient="records"),
        "agb_mg_ha": {
            "min": float(agb.min()),
            "p25": float(agb.quantile(0.25)),
            "p50": float(agb.median()),
            "p75": float(agb.quantile(0.75)),
            "max": float(agb.max()),
            "media": float(agb.mean()),
        },
        "por_bioma": {
            str(name): int(len(group))
            for name, group in result.groupby("bioma")
        },
        "por_fitofisionomia": {
            str(name): {
                "n": int(len(group)),
                "agb_p50": float(group["agb_mg_ha"].median()),
            }
            for name, group in result.groupby("fitofisionomia")
        },
    }
    return result, report


def export_target(
    target,
    csv_path: str | Path,
    *,
    gpkg_path: str | Path | None = None,
    manifest_path: str | Path | None = None,
    report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Escreve CSV (tabela) e, opcionalmente, GeoPackage (pontos) e manifesto."""
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(target.drop(columns="geometry"))
    table.to_csv(csv_path, index=False, encoding="utf-8", float_format="%.6f")

    outputs: dict[str, Any] = {
        "csv": str(csv_path),
        "sha256_csv": sha256_file(csv_path),
        "rows": int(len(table)),
    }
    if gpkg_path is not None:
        gpkg_path = Path(gpkg_path)
        gpkg_path.parent.mkdir(parents=True, exist_ok=True)
        if gpkg_path.exists():
            gpkg_path.unlink()
        target.to_file(gpkg_path, layer="target_uas", driver="GPKG")
        outputs["gpkg"] = str(gpkg_path)
        outputs["sha256_gpkg"] = sha256_file(gpkg_path)

    result = dict(report or {})
    result["outputs"] = outputs
    if manifest_path is not None:
        manifest_path = Path(manifest_path)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "target_version": "target_uas_v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            **result,
        }
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        result["manifest"] = str(manifest_path)
    return result


def consolidate_target(
    gpkg: str | Path,
    csv_path: str | Path,
    *,
    gpkg_path: str | Path | None = None,
    manifest_path: str | Path | None = None,
    source: str = "IFN/SFB",
    source_version: str = "painel_biomassa_carbono_2025",
    plausibility_max: float = 500.0,
    biomes: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Constroi e exporta o target consolidado; devolve o relatorio."""
    target, report = build_target(
        gpkg,
        source=source,
        source_version=source_version,
        plausibility_max=plausibility_max,
        biomes=biomes,
    )
    report["inputs"] = {"gpkg": str(Path(gpkg)), "sha256_gpkg": sha256_file(gpkg)}
    report["params"] = {
        "source": source,
        "source_version": source_version,
        "plausibility_max_mg_ha": float(plausibility_max),
        "biomes": list(biomes) if biomes else None,
        "one_row_per_ua": True,
        "tier_precedence": "A>B",
    }
    return export_target(
        target, csv_path, gpkg_path=gpkg_path, manifest_path=manifest_path,
        report=report,
    )
