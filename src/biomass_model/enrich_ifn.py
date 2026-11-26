"""Enriquecimento do IFN/SFB com evidência IBGE/MapBiomas (docs/60).

Princípios (pedido de escopo; ADRs 0027/0029/0032):

- A unidade de saída é a **unidade de treino** do adaptador `load_ifn_panel`
  (1 linha por Unidade Amostral/conglomerado), preservando a AGB e sua origem.
- A classe IBGE vem de **correspondência temática** entre a categoria publicada
  do IFN e a legenda oficial do IBGE (nunca de localização em polígono).
- O IFN público não divulga a posição exata da parcela. O suporte espacial padrão
  é a **pegada documentada do conglomerado (Cruz de Malta) centrada no ponto
  publicado**: 4 subunidades de 20×50 m (20×100 m na Amazônia), 10 m de vão, com
  `n_subunidades` braços medidos. Os pontos empilhados são as linhas (UAs ×
  classes × equações) que compartilham a mesma coordenada. A composição é
  calculada nessa pegada (IBGE + MapBiomas do ano), jamais no centro como se
  fosse a parcela. O município continua disponível como suporte alternativo
  (`--spatial-support municipio`), mas é unidade administrativa mais grossa que
  a granularidade oficial de publicação (estadual).
- Proporções territoriais são atributos compartilhados da unidade: não
  identificam a classe da parcela e não substituem prova de pixel 3/4.
- Campos sem evidência suficiente permanecem vazios.

Referências metodológicas do SFB (registradas no relatório): desenho em dois
estágios (Cochran 1977; Queiroz 2012), teste de equivalência TOST ±25%
(Robinson & Froese 2004), tipologias conforme IBGE (2012) e REFLORA (2023),
fator de expansão AGB→BGB (`valor_r`).
"""
from __future__ import annotations

import csv
import json
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .inventory.adapters import load_ifn_panel
from .stratification import normalize_name

TIPOLOGIA = "tipologia_da_vegetacao"
USO = "classe_uso_da_terra"
ORIGEM_TEMATICA = "correspondencia_tematica"
MOTIVO_SEM_PIXEL = "sem_observacao_direta_no_ponto"
MOTIVO_DOMINIO = (
    "IFN publico nao divulga a posicao exata da parcela; composicao "
    "territorial nao comprova classe 3/4 no pixel"
)
ANTHROPIC_MB = {"15", "18", "19", "20", "21", "24", "25", "30", "39", "40",
                "41", "46", "47", "48"}
# Desenho amostral documentado (Metodologia IFN/SFB; ver data/reference/
# ifn_desenho_amostral.csv): conglomerado em Cruz de Malta, 4 subunidades
# 20 x 50 m (20 x 100 m no bioma Amazônia), 10 m de vão a partir do centro.
IFN_SUBUNIT_WIDTH_M = 20.0
IFN_SUBUNIT_GAP_M = 10.0
IFN_SUBUNIT_LENGTH_AMAZON_M = 100.0
IFN_SUBUNIT_LENGTH_DEFAULT_M = 50.0

MAPBIOMAS_CLASSES = {
    3: "Formacao Florestal",
    4: "Formacao Savanica",
    5: "Mangue",
    6: "Floresta Alagavel",
    11: "Campo Alagado e Area Pantanosa",
    12: "Formacao Campestre",
    15: "Pastagem",
    18: "Agricultura",
    19: "Lavoura Temporaria",
    20: "Cana",
    21: "Mosaico de Usos",
    24: "Area Urbanizada",
    25: "Outras Areas Nao Vegetadas",
    30: "Mineracao",
    33: "Rio, Lago e Oceano",
    39: "Soja",
    40: "Arroz",
    41: "Outras Lavouras Temporarias",
    46: "Cafe",
    47: "Citrus",
    48: "Outras Lavouras Perenes",
}


# ------------------------------------------------------------------ utilidades
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_csv(records: list[dict], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        path.write_text("", encoding="utf-8")
        return path
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    return path


def _join(values: Any) -> str:
    if isinstance(values, str):
        values = [values]
    return "|".join(sorted({str(v).strip() for v in values if str(v).strip()}))


# ------------------------------------------------------- tabela de correspondência
def load_correspondence(path: str | Path) -> pd.DataFrame:
    """Carrega e valida a tabela de correspondência IFN × IBGE."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    required = {"campo_ifn", "valor_ifn", "classe_ibge_legenda1", "vinculo",
                "nivel_detalhe", "origem", "fonte_documental",
                "prefixos_normalizados"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"correspondência sem colunas: {sorted(missing)}")
    valid = {"univoco", "parcial", "ambiguo", "sem_correspondencia"}
    bad = set(df["vinculo"]) - valid
    if bad:
        raise ValueError(f"vínculo inválido: {sorted(bad)}")
    return df


def compile_correspondence(df: pd.DataFrame) -> dict[str, dict]:
    """Índice por campo: exato + prefixos (prefixo mais longo vence)."""
    index: dict[str, dict] = {}
    for campo, sub in df.groupby("campo_ifn"):
        exact: dict[str, dict] = {}
        prefixes: list[tuple[str, dict]] = []
        for _, row in sub.iterrows():
            record = row.to_dict()
            exact.setdefault(normalize_name(record["valor_ifn"]), record)
            for pref in str(record.get("prefixos_normalizados", "")).split(";"):
                pref = normalize_name(pref)
                if pref:
                    prefixes.append((pref, record))
        prefixes.sort(key=lambda item: (-len(item[0]), item[0]))
        index[str(campo)] = {"exact": exact, "prefixes": prefixes}
    return index


def match_category(name: Any, campo: str, index: dict[str, dict]) -> dict:
    """Classifica uma categoria publicada; ausência de regra fica explícita."""
    entry = index.get(campo, {"exact": {}, "prefixes": []})
    query = normalize_name(name)
    empty = {
        "classe_ibge": "", "vinculo": "sem_correspondencia",
        "nivel_detalhe": "", "fonte": "", "regra": "nenhuma",
        "candidatas": "", "observacao": "",
    }
    if not query:
        return empty
    row = entry["exact"].get(query)
    regra = "exato"
    if row is None:
        for pref, candidate in entry["prefixes"]:
            if query.startswith(pref):
                row, regra = candidate, f"prefixo:{pref}"
                break
    if row is None:
        return empty
    return {
        "classe_ibge": str(row.get("classe_ibge_legenda1", "")).strip(),
        "vinculo": str(row.get("vinculo", "")).strip(),
        "nivel_detalhe": str(row.get("nivel_detalhe", "")).strip(),
        "fonte": str(row.get("fonte_documental", "")).strip(),
        "regra": regra,
        "candidatas": str(row.get("classes_ibge_legenda2_candidatas", "")).strip(),
        "observacao": str(row.get("observacao", "")).strip(),
    }


def _classify_set(values: list[str], campo: str, index: dict) -> dict:
    """Classifica o conjunto de categorias de uma UA (pode haver >1)."""
    targets: list[str] = []
    candidatas: list[str] = []
    vinculos: list[str] = []
    regras: list[str] = []
    fontes: list[str] = []
    detalhes: list[str] = []
    for value in sorted({str(v).strip() for v in values if str(v).strip()}):
        match = match_category(value, campo, index)
        vinculos.append(match["vinculo"])
        regras.append(f"{value}={match['regra']}")
        if match["fonte"]:
            fontes.append(match["fonte"])
        if match["nivel_detalhe"]:
            detalhes.append(match["nivel_detalhe"])
        if match["classe_ibge"]:
            targets.append(match["classe_ibge"])
        for cand in match["candidatas"].split("|"):
            if cand:
                candidatas.append(cand)

    # precedência do pior caso: sem > ambíguo > múltiplo > parcial > unívoco
    if "sem_correspondencia" in vinculos:
        status = "sem_correspondencia"
    elif "ambiguo" in vinculos:
        status = "ambiguo"
    elif len(set(targets)) > 1:
        status = "multiplo"
    elif "parcial" in vinculos:
        status = "parcial"
    elif targets:
        status = "univoco"
    else:
        status = "sem_correspondencia"

    unico = targets[0] if status == "univoco" and targets else ""
    return {
        "fitofisionomia_ibge": unico,
        "fitofisionomia_candidatas": _join(targets + candidatas),
        "status_correspondencia": status,
        "regra_correspondencia": "; ".join(regras),
        "nivel_detalhe": _join(detalhes),
        "fonte_correspondencia": " | ".join(sorted(set(fontes))),
    }


# ------------------------------------- correspondência IBGE legenda_1 -> MapBiomas
def load_mapbiomas_correspondence(path: str | Path) -> pd.DataFrame:
    """Tabela documentada IBGE legenda_1 -> MapBiomas (por bioma)."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    required = {"classe_ibge_legenda1", "bioma", "mapbiomas_codigos",
                "mapbiomas_classes", "evidencia_legenda", "fonte_documental"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"correspondência IBGE->MapBiomas sem colunas: "
                         f"{sorted(missing)}")
    return df


def compile_mapbiomas_correspondence(
    df: pd.DataFrame,
) -> dict[tuple[str, str], set[int]]:
    """Índice (classe IBGE normalizada, bioma normalizado) -> códigos MapBiomas."""
    index: dict[tuple[str, str], set[int]] = {}
    for _, row in df.iterrows():
        cls = normalize_name(row["classe_ibge_legenda1"])
        bio = normalize_name(row["bioma"])  # "*" normaliza para ""
        codes = {int(c) for c in str(row["mapbiomas_codigos"]).replace(
            ";", ",").split(",") if c.strip().isdigit()}
        index.setdefault((cls, bio), set()).update(codes)
    return index


def mapbiomas_compatible_classes(
    index: dict[tuple[str, str], set[int]],
    classe_ibge: str,
    bioma: str,
) -> list[int]:
    """Códigos MapBiomas documentados para uma classe IBGE e bioma.

    Ordem: (classe, bioma) -> (classe, "*") -> união de biomas.
    """
    cls = normalize_name(classe_ibge)
    if not cls:
        return []
    codes = index.get((cls, normalize_name(bioma)), set())
    if not codes:
        codes = index.get((cls, ""), set())
    if not codes:
        for (other_cls, _bio), value in index.items():
            if other_cls == cls:
                codes |= value
    return sorted(codes)


# ------------------------------------------------------------- suporte espacial
def _decimals(value: float) -> int:
    text = repr(float(value))
    if "." not in text:
        return 0
    return len(text.split(".")[1].rstrip("0"))


def ifn_footprint(
    lon: float,
    lat: float,
    bioma: str = "",
    n_subunidades: int | None = None,
    *,
    width_m: float = IFN_SUBUNIT_WIDTH_M,
    gap_m: float = IFN_SUBUNIT_GAP_M,
) -> dict:
    """Pegada do conglomerado IFN (Cruz de Malta) centrada no ponto publicado.

    Metodologia IFN/SFB: 4 subunidades de 20 x 50 m (20 x 100 m no bioma
    Amazônia), perpendiculares ao ponto central, orientadas N/E/S/W, com 10 m
    entre o centro e o início de cada subunidade. `n_subunidades` (1–4,
    atributo do painel) limita quantos braços foram medidos.
    """
    from shapely import affinity
    from shapely.geometry import box
    from shapely.ops import unary_union

    is_amazon = normalize_name(bioma).startswith("amazonia")
    length = (IFN_SUBUNIT_LENGTH_AMAZON_M if is_amazon
              else IFN_SUBUNIT_LENGTH_DEFAULT_M)
    n = 4 if not n_subunidades else max(1, min(4, int(n_subunidades)))
    lat_deg_per_m = 1.0 / 110_574.0
    lon_deg_per_m = 1.0 / (111_320.0 * max(np.cos(np.radians(lat)), 1e-6))
    half_w_lon = (width_m / 2.0) * lon_deg_per_m
    half_w_lat = (width_m / 2.0) * lat_deg_per_m
    g_lat = gap_m * lat_deg_per_m
    g_lon = gap_m * lon_deg_per_m
    len_lat = length * lat_deg_per_m
    len_lon = length * lon_deg_per_m
    arms = [
        box(-half_w_lon, g_lat, half_w_lon, g_lat + len_lat),        # N (1)
        box(g_lon, -half_w_lat, g_lon + len_lon, half_w_lat),        # E (2)
        box(-half_w_lon, -(g_lat + len_lat), half_w_lon, -g_lat),    # S (3)
        box(-(g_lon + len_lon), -half_w_lat, -g_lon, half_w_lat),    # W (4)
    ]
    poly = unary_union([affinity.translate(a, lon, lat) for a in arms])
    radius = float(np.hypot(gap_m + length, width_m / 2.0))
    footprint_ha = 4.0 * width_m * length / 10_000.0
    measured_ha = n * width_m * length / 10_000.0
    precision = min(_decimals(lon), _decimals(lat))
    return {
        # o suporte é a coordenada publicada (pontos empilhados compartilham)
        "suporte_id": f"{lon:.6f}|{lat:.6f}|{bioma}",
        "geometry": poly,
        "area_ha": float(footprint_ha),
        "area_medida_ha": float(measured_ha),
        "raio_m": radius,
        "comprimento_subunidade_m": float(length),
        "largura_subunidade_m": float(width_m),
        "n_subunidades": int(n),
        "precisao_decimais": int(precision),
        "incerteza_max_m": float(0.5 * 10.0 ** -precision * 111_320.0),
    }


# ------------------------------------------------------- composição territorial
def _pixel_area_rows(transform, rows: np.ndarray) -> np.ndarray:
    lats = transform.f + (rows + 0.5) * transform.e
    dx_km = abs(transform.a) * 111.320 * np.cos(np.radians(lats))
    dy_km = abs(transform.e) * 110.574
    return dx_km * dy_km


def _iter_blocks(height: int, block_rows: int = 256):
    for row0 in range(0, height, block_rows):
        yield row0, min(block_rows, height - row0)


def compute_territorial_units(
    units,
    ibge_vegetation_path: str | Path,
    mapbiomas_pattern: str,
    *,
    ibge_version: str = "2025-01-01",
    max_units: int | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Composição IBGE (vegetação natural) e MapBiomas por unidade espacial.

    `units` é um GeoDataFrame (EPSG:4326) com colunas:
    `unidade_tipo`, `unidade_id`, `unidade_label`, `uf`, `ano`,
    `resolucao_graus`, `n_uas`, `area_unidade_km2`, `geometry`.
    Uma linha por (unidade, ano).
    """
    import geopandas as gpd
    import rasterio
    from rasterio import features
    from rasterio.windows import Window, from_bounds
    from shapely.geometry import box as shape_box

    units = units.copy()
    if max_units:
        units = units.head(max_units)
    if units.crs is None:
        units = units.set_crs("EPSG:4326")
    elif str(units.crs).upper() != "EPSG:4326":
        units = units.to_crs("EPSG:4326")

    ibge = gpd.read_file(
        ibge_vegetation_path,
        columns=["legenda_1", "legenda_2", "leg_sup"])
    if ibge.crs is None:
        ibge = ibge.set_crs("EPSG:4674")
    ibge = ibge.to_crs("EPSG:4326")
    sup = ibge["leg_sup"].astype(str)
    natural = sup.str.startswith("Vegetação Natural")
    ibge = ibge[natural & ibge["legenda_1"].notna()].copy()
    ibge["legenda_1"] = ibge["legenda_1"].astype(str).str.strip()
    legenda1 = sorted(ibge["legenda_1"].unique())
    legenda1_code = {name: i + 1 for i, name in enumerate(legenda1)}
    if len(legenda1) > 15:  # pragma: no cover - proteção do canal de 4 bits
        raise ValueError(f"legenda_1 com {len(legenda1)} classes; "
                         "ajustar dimensão do cruzamento")
    ibge["_code"] = ibge["legenda_1"].map(legenda1_code).astype("uint8")
    ibge_sindex = ibge.sindex

    records: list[dict] = []
    # cache de composição IBGE por unidade (tempo-invariante; a grade é comum)
    cache: dict[str, tuple[np.ndarray, list]] = {}
    years_by_unit: dict[str, list[int]] = {}
    for _, row in units.iterrows():
        years_by_unit.setdefault(str(row["unidade_id"]), []).append(
            int(row["ano"]))

    for _, unit in units.iterrows():
        uid = str(unit["unidade_id"])
        year = int(unit["ano"])
        geom = unit.geometry
        if geom is None or geom.is_empty:
            continue
        label = unit.get("unidade_label", "")
        uf = unit.get("uf", "")
        tipo = unit.get("unidade_tipo", "grid_cell")
        resol = unit.get("resolucao_graus", "")
        n_uas = unit.get("n_uas", "")
        area_unit = unit.get("area_unidade_km2", "")
        if uid not in cache:
            idx = ibge_sindex.query(geom, predicate="intersects")
            sub = ibge.iloc[list(idx)]
            shapes = [(g, int(c)) for g, c in
                      zip(sub.geometry, sub["_code"])
                      if g is not None and not g.is_empty]
            cache[uid] = (np.zeros(len(legenda1) + 1, dtype="float64"), shapes)
        l1_area, shapes = cache[uid]
        first_year = year == min(years_by_unit[uid])
        with ExitStack() as stack:
            raster_path = Path(str(mapbiomas_pattern).format(year=year))
            if not raster_path.exists():
                continue
            src = stack.enter_context(rasterio.open(raster_path))
            win = from_bounds(*geom.bounds, transform=src.transform)
            row0 = max(0, int(np.floor(win.row_off)))
            col0 = max(0, int(np.floor(win.col_off)))
            row1 = min(src.height, int(np.ceil(win.row_off + win.height)))
            col1 = min(src.width, int(np.ceil(win.col_off + win.width)))
            height, width = row1 - row0, col1 - col0
            if height <= 0 or width <= 0:
                continue
            mb_area = np.zeros(256, dtype="float64")
            pair_area = np.zeros(16 * 256, dtype="float64")
            valid_area = 0.0
            for off, nrows in _iter_blocks(height):
                window = Window(col0, row0 + off, width, nrows)
                arr = src.read(1, window=window)
                if arr.size == 0:
                    continue
                block_transform = src.window_transform(window)
                mask = features.geometry_mask(
                    [geom], out_shape=arr.shape, transform=block_transform,
                    all_touched=True, invert=True)
                if not mask.any():
                    continue
                rows = np.arange(nrows, dtype="float64") + off
                area_row = _pixel_area_rows(block_transform, rows)
                rr, cc = np.nonzero(mask)
                base_pixel_area = abs(block_transform.a * block_transform.e)
                frac = np.zeros(len(rr), dtype="float64")
                for k in range(len(rr)):
                    left = block_transform.c + cc[k] * block_transform.a
                    top = block_transform.f + rr[k] * block_transform.e
                    px = shape_box(left, top + block_transform.e,
                                   left + block_transform.a, top)
                    inter = px.intersection(geom)
                    frac[k] = (inter.area / base_pixel_area
                               if not inter.is_empty else 0.0)
                keep_frac = frac > 0
                if not keep_frac.any():
                    continue
                rr, cc, frac = rr[keep_frac], cc[keep_frac], frac[keep_frac]
                cls = arr[rr, cc].astype("int64")
                w = area_row[rr] * frac
                valid = cls > 0
                if not valid.any():
                    continue
                mb_area += np.bincount(cls[valid], weights=w[valid],
                                       minlength=256)
                valid_area += float(w[valid].sum())
                shapes_arr = features.rasterize(
                    shapes, out_shape=arr.shape, transform=block_transform,
                    fill=0, dtype="uint8")
                ic = shapes_arr[rr, cc].astype("int64")
                keep = valid & (ic > 0)
                if keep.any():
                    if first_year:
                        l1_area += np.bincount(ic[keep], weights=w[keep],
                                               minlength=len(legenda1) + 1)
                    pair_area += np.bincount(
                        ic[keep] * 256 + cls[keep], weights=w[keep],
                        minlength=16 * 256)
            base = {
                "unidade_tipo": tipo, "unidade_id": uid,
                "unidade_label": label, "uf": uf,
                "ano_mapbiomas": year, "area_unidade_km2": area_unit,
                "resolucao_graus": resol, "n_uas": n_uas,
            }
            records.append({**base, "colecao": "MapBiomas Col.11",
                            "fonte_mapa": "MapBiomas_col11",
                            "classe": "__resumo__", "area_km2": "",
                            "proporcao": "",
                            "denominador_km2": round(valid_area, 6),
                            "cobertura_valida_km2": round(valid_area, 6),
                            "tipo": "resumo", "status": "ok"})
            for cls in range(1, 256):
                if mb_area[cls] <= 0:
                    continue
                records.append({
                    **base, "colecao": "MapBiomas Col.11",
                    "fonte_mapa": "MapBiomas_col11",
                    "classe": f"{cls} {MAPBIOMAS_CLASSES.get(cls, '')}".strip(),
                    "area_km2": round(float(mb_area[cls]), 6),
                    "proporcao": round(float(mb_area[cls]) / valid_area, 6)
                    if valid_area else "",
                    "denominador_km2": round(valid_area, 6),
                    "cobertura_valida_km2": round(valid_area, 6),
                    "tipo": "mapbiomas_nivel2", "status": "ok",
                })
            total_l1 = float(l1_area.sum())
            if first_year and total_l1:
                for name, c in legenda1_code.items():
                    area = float(l1_area[c])
                    if area <= 0:
                        continue
                    records.append({
                        **base, "ano_mapbiomas": "",
                        "colecao": f"IBGE {ibge_version}",
                        "fonte_mapa": "IBGE_vegetacao_250k",
                        "classe": name, "area_km2": round(area, 6),
                        "proporcao": round(area / total_l1, 6),
                        "denominador_km2": round(total_l1, 6),
                        "cobertura_valida_km2": round(total_l1, 6),
                        "tipo": "ibge_legenda1",
                        "status": "sem_dimensao_temporal",
                    })
            total_px = float(pair_area.sum())
            mean_px = (valid_area / total_px) if total_px else 0.0
            mat = pair_area.reshape(16, 256)
            for icode, name in ((c, n) for n, c in legenda1_code.items()):
                if icode >= 16:
                    continue
                for cls in range(1, 256):
                    area = float(mat[icode, cls]) * mean_px
                    if area <= 0:
                        continue
                    records.append({
                        **base, "colecao": "MapBiomas Col.11 + IBGE",
                        "fonte_mapa": "cruzamento_ibge_x_mapbiomas",
                        "classe": (f"{name} | "
                                   f"{cls} {MAPBIOMAS_CLASSES.get(cls, '')}"
                                   ).strip(),
                        "area_km2": round(area, 6),
                        "proporcao": round(area / valid_area, 6)
                        if valid_area else "",
                        "denominador_km2": round(valid_area, 6),
                        "cobertura_valida_km2": round(valid_area, 6),
                        "tipo": "cruzamento_ibge_x_mapbiomas", "status": "ok",
                    })
    out = pd.DataFrame(records)
    meta = {"unidades_calculadas": int(out["unidade_id"].nunique())
            if len(out) else 0,
            "legenda1_classes": legenda1}
    return out, meta


# ------------------------------------------------------------------ enriquecimento
def _territorial_summary(territorio: pd.DataFrame) -> pd.DataFrame:
    """Resumo por (unidade, ano) para anexar indicadores aos registros."""
    if territorio is None or territorio.empty:
        return pd.DataFrame()
    mb = territorio[(territorio["tipo"] == "mapbiomas_nivel2")
                    & (territorio["ano_mapbiomas"] != "")].copy()
    mb["area_num"] = pd.to_numeric(mb["area_km2"], errors="coerce")
    mb["classe_num"] = mb["classe"].astype(str).str.split(" ").str[0]
    ibge = territorio[territorio["tipo"] == "ibge_legenda1"].copy()
    ibge["area_num"] = pd.to_numeric(ibge["area_km2"], errors="coerce")
    resumo = territorio[territorio["tipo"] == "resumo"].copy()
    area_unit = {}
    for _, row in resumo.iterrows():
        area_unit[(row["unidade_id"], row["ano_mapbiomas"])] = (
            row["area_unidade_km2"])

    rows = []
    for (uid, year), sub in mb.groupby(["unidade_id", "ano_mapbiomas"]):
        total = float(pd.to_numeric(sub["denominador_km2"],
                                    errors="coerce").iloc[0] or 0.0)
        area = sub.groupby("classe_num")["area_num"].sum()

        def prop(cls: str) -> float | None:
            value = float(area.get(cls, 0.0))
            return round(value / total, 6) if total else None

        cross = territorio[(territorio["tipo"] == "cruzamento_ibge_x_mapbiomas")
                           & (territorio["unidade_id"] == uid)
                           & (territorio["ano_mapbiomas"] == year)].copy()
        ibge_unit = ibge[ibge["unidade_id"] == uid]
        natural_area = float(ibge_unit["area_num"].sum()) \
            if len(ibge_unit) else 0.0

        def _mb_code(label: str) -> str:
            parts = str(label).split("|")
            return parts[1].strip().split(" ")[0] if len(parts) > 1 else ""

        frac = None
        if natural_area and len(cross):
            cross["_mb"] = cross["classe"].map(_mb_code)
            ant = float(pd.to_numeric(
                cross[cross["_mb"].isin(ANTHROPIC_MB)]["area_km2"],
                errors="coerce").sum())
            frac = round(ant / natural_area, 6)
        dominant = ""
        if len(ibge_unit):
            dominant = str(ibge_unit.sort_values(
                "area_num", ascending=False)["classe"].iloc[0])
        unit_area = area_unit.get((uid, year), "")
        rows.append({
            "unidade_id": uid,
            "ano_mapbiomas": year,
            "ter_prop_mapbiomas_3": prop("3"),
            "ter_prop_mapbiomas_4": prop("4"),
            "ter_prop_mapbiomas_5": prop("5"),
            "ter_prop_mapbiomas_6": prop("6"),
            "ter_prop_mapbiomas_11": prop("11"),
            "ter_prop_mapbiomas_12": prop("12"),
            "ter_prop_mapbiomas_3_4": (round((prop("3") or 0) + (prop("4") or 0), 6)
                                       if total else None),
            "ter_prop_ibge_vegetacao_natural": (
                round(natural_area / float(unit_area), 6)
                if unit_area not in ("", None) and float(unit_area) > 0
                else None),
            "ter_classe_ibge_dominante": dominant,
            "ter_frac_ibge_natural_antropico_mapbiomas": frac,
            "ter_denominador_km2": round(total, 6) if total else None,
        })
    return pd.DataFrame(rows)


# ------------------------------------------------------------- leitura de insumos
def load_panel_sets(path: str | Path) -> pd.DataFrame:
    """Categorias publicadas por UA (todas as linhas; não deduplica AGB)."""
    p = Path(path)
    if p.suffix.lower() == ".gpkg":
        import sqlite3

        with sqlite3.connect(p) as con:
            df = pd.read_sql_query(
                "SELECT ua, classe_uso_da_terra, tipologia_da_vegetacao "
                "FROM pontos_sfb", con)
    else:
        df = pd.read_csv(
            p, sep=";", encoding="utf-8-sig", encoding_errors="replace",
            usecols=["ua", USO, TIPOLOGIA, "n_subunidades"],
            low_memory=False)
    df = df.fillna("")
    for col in ("ua", USO, TIPOLOGIA):
        df[col] = df[col].astype(str).str.strip()
    df["n_subunidades"] = pd.to_numeric(df.get("n_subunidades"),
                                        errors="coerce")
    grouped = df.groupby("ua").agg({
        USO: lambda s: _join(s.tolist()),
        TIPOLOGIA: lambda s: _join(s.tolist()),
        "n_subunidades": "max",
    })
    counts = df.groupby("ua").size().rename("n_linhas_painel")
    return grouped.join(counts).reset_index()


def load_uf_aux(uf_dir: str | Path) -> pd.DataFrame:
    """Município, UF e data de campo por UA (arquivos oficiais por UF)."""
    rows = []
    for path in sorted(Path(uf_dir).glob("ua_*.csv")):
        df = pd.read_csv(path, encoding="utf-8-sig", encoding_errors="replace",
                         usecols=lambda c: c in {"ua", "mun", "uf", "data"})
        if "ua" in df.columns:
            rows.append(df)
    if not rows:
        raise FileNotFoundError(f"nenhum ua_*.csv em {uf_dir}")
    aux = pd.concat(rows, ignore_index=True).fillna("")
    for col in ("ua", "mun", "uf", "data"):
        if col in aux:
            aux[col] = aux[col].astype(str).str.strip()
    aux = aux.drop_duplicates("ua", keep="first")
    aux["ano"] = pd.to_numeric(
        aux.get("data", "").astype(str).str.extract(r"(\d{4})")[0],
        errors="coerce")
    return aux[["ua", "mun", "uf", "data", "ano"]].rename(
        columns={"data": "data_campo"})


def load_municipalities(path: str | Path):
    """Malha municipal IBGE; localiza colunas de código/nome/UF."""
    import geopandas as gpd

    gdf = gpd.read_file(path)
    cols = {c.lower(): c for c in gdf.columns}
    code = next((cols[k] for k in ("cd_mun", "cd_geocmu", "geocodigo")
                 if k in cols), None)
    name = next((cols[k] for k in ("nm_mun", "nome", "nm_municipio")
                 if k in cols), None)
    uf = next((cols[k] for k in ("sigla_uf", "uf", "sigla") if k in cols), None)
    if not code or not name:
        raise ValueError(f"malha municipal sem código/nome: {list(gdf.columns)}")
    keep = [code, name] + ([uf] if uf else []) + [gdf.geometry.name]
    out = gdf[keep].copy()
    rename = {code: "municipio_codigo", name: "municipio"}
    if uf:
        rename[uf] = "uf"
    out = out.rename(columns=rename)
    out["municipio_codigo"] = out["municipio_codigo"].astype(str)
    if "uf" not in out:
        out["uf"] = ""
    out["_chave"] = (out["uf"].map(normalize_name) + "|"
                     + out["municipio"].map(normalize_name))
    return out


def build_ifn_enrichment(
    panel_path: str | Path,
    uf_dir: str | Path,
    correspondence_path: str | Path,
    out_dir: str | Path,
    *,
    equation: str = "AGB_Chave",
    usage: str = "validation",
    spatial_support: str = "footprint",
    municipalities_path: str | Path | None = None,
    ibge_vegetation_path: str | Path | None = None,
    mapbiomas_pattern: str | None = None,
    mapbiomas_correspondence_path: str | Path | None = None,
    ibge_version: str = "2025-01-01",
    max_units: int | None = None,
) -> dict[str, Any]:
    """Executa o enriquecimento, grava as tabelas e devolve o relatório."""
    if spatial_support not in ("footprint", "municipio"):
        raise ValueError("spatial_support deve ser 'footprint' ou 'municipio'")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    corr = load_correspondence(correspondence_path)
    index = compile_correspondence(corr)

    base = load_ifn_panel(panel_path, equation=equation, usage=usage)
    base["ua"] = base["site"].astype(str)
    sets = load_panel_sets(panel_path)
    uf_aux = load_uf_aux(uf_dir)
    df = base.merge(sets, on="ua", how="left").merge(uf_aux, on="ua", how="left")
    df["municipio"] = df.get("mun", "").fillna("").astype(str)
    df["uf"] = df.get("uf", "").fillna("").astype(str)

    # código municipal a partir da malha (chave uf|nome), quando fornecida
    munis_ref = None
    if municipalities_path:
        munis_ref = load_municipalities(municipalities_path)
        key_map = dict(zip(munis_ref["_chave"], munis_ref["municipio_codigo"]))
        chave = (df["uf"].map(normalize_name) + "|"
                 + df["municipio"].map(normalize_name))
        df["municipio_codigo"] = chave.map(key_map).fillna("")
    else:
        df["municipio_codigo"] = ""

    tipologia_cols = []
    uso_cols = []
    evidencias = []
    for _, row in df.iterrows():
        tipologias = [t for t in str(row.get(TIPOLOGIA, "")).split("|") if t]
        usos = [u for u in str(row.get(USO, "")).split("|") if u]
        tipologia_cols.append(_classify_set(tipologias, TIPOLOGIA, index))
        uso_cols.append(_classify_set(usos, USO, index))
        for value in sorted(set(tipologias)):
            match = match_category(value, TIPOLOGIA, index)
            evidencias.append({
                "observation_id": row["observation_id"], "ua": row["ua"],
                "campo_ifn": TIPOLOGIA, "valor_ifn": value,
                "classe_ibge_alvo": match["classe_ibge"],
                "vinculo": match["vinculo"],
                "nivel_detalhe": match["nivel_detalhe"],
                "regra_aplicada": match["regra"],
                "origem": ORIGEM_TEMATICA,
                "fonte_documental": match["fonte"],
                "observacao": match["observacao"],
            })
        for value in sorted(set(usos)):
            match = match_category(value, USO, index)
            evidencias.append({
                "observation_id": row["observation_id"], "ua": row["ua"],
                "campo_ifn": USO, "valor_ifn": value,
                "classe_ibge_alvo": match["classe_ibge"],
                "vinculo": match["vinculo"],
                "nivel_detalhe": match["nivel_detalhe"],
                "regra_aplicada": match["regra"],
                "origem": "definicao_de_campo",
                "fonte_documental": match["fonte"],
                "observacao": match["observacao"],
            })

    tip_df = pd.DataFrame(tipologia_cols, index=df.index)
    uso_df = pd.DataFrame(uso_cols, index=df.index)
    df = pd.concat([df, tip_df.add_prefix("tip_"), uso_df.add_prefix("uso_")],
                   axis=1)

    # classes MapBiomas documentadas para a fitofisionomia IBGE (por bioma)
    mb_index: dict = {}
    if mapbiomas_correspondence_path:
        mb_table = load_mapbiomas_correspondence(mapbiomas_correspondence_path)
        mb_index = compile_mapbiomas_correspondence(mb_table)
    bioma_col = df["biome"] if "biome" in df.columns else pd.Series(
        "", index=df.index)
    df["tip_mapbiomas_compativeis"] = [
        "|".join(str(c) for c in mapbiomas_compatible_classes(
            mb_index, row["tip_fitofisionomia_ibge"], bioma))
        for (_, row), bioma in zip(df.iterrows(), bioma_col)
    ]

    # pegada documentada do conglomerado (Cruz de Malta) centrada no ponto
    n_rows = len(df)
    lon_vals = (df["lon"].tolist() if "lon" in df.columns
                else [np.nan] * n_rows)
    lat_vals = (df["lat"].tolist() if "lat" in df.columns
                else [np.nan] * n_rows)
    bioma_vals = (df["biome"].tolist() if "biome" in df.columns
                  else [""] * n_rows)
    nsub_vals = (df["n_subunidades"].tolist()
                 if "n_subunidades" in df.columns else [np.nan] * n_rows)
    footprints = []
    for lon, lat, bioma, n_sub in zip(lon_vals, lat_vals, bioma_vals,
                                      nsub_vals):
        try:
            footprints.append(ifn_footprint(
                float(lon), float(lat), str(bioma),
                int(n_sub) if pd.notna(n_sub) else None))
        except (TypeError, ValueError):
            footprints.append(None)
    df["suporte_id"] = [f["suporte_id"] if f else "" for f in footprints]
    df["suporte_area_ha"] = [f["area_ha"] if f else np.nan for f in footprints]
    df["suporte_area_medida_ha"] = [f["area_medida_ha"] if f else np.nan
                                    for f in footprints]
    df["suporte_raio_m"] = [f["raio_m"] if f else np.nan for f in footprints]
    df["suporte_comprimento_m"] = [f["comprimento_subunidade_m"] if f else np.nan
                                   for f in footprints]
    df["suporte_precisao_decimais"] = [f["precisao_decimais"] if f else np.nan
                                       for f in footprints]
    df["suporte_incerteza_max_m"] = [f["incerteza_max_m"] if f else np.nan
                                     for f in footprints]
    # empilhamento: quantas linhas/UAs compartilham a mesma coordenada
    n_obs = df.groupby("suporte_id")["observation_id"].nunique().to_dict()
    n_uas = df.groupby("suporte_id")["ua"].nunique().to_dict()
    df["suporte_n_obs_empilhadas"] = df["suporte_id"].map(n_obs)
    df["suporte_n_uas_empilhadas"] = df["suporte_id"].map(n_uas)
    # linhas do painel por UA (classes x equacoes) - o empilhamento de registros
    linhas_por_ua = (sets.set_index("ua")["n_linhas_painel"].to_dict()
                     if "n_linhas_painel" in sets.columns else {})
    df["suporte_n_linhas_painel"] = df["ua"].map(linhas_por_ua)

    # ---------------- composição territorial (opcional) ----------------
    territorial = pd.DataFrame()
    ter_meta: dict[str, Any] = {}
    ter_status = "sem_insumos_mapas"
    if ibge_vegetation_path and mapbiomas_pattern:
        if spatial_support == "footprint":
            units = []
            seen = set()
            for _, row in df.iterrows():
                key = (row["suporte_id"], row["ano"])
                if not row["suporte_id"] or pd.isna(row["ano"]) or key in seen:
                    continue
                seen.add(key)
                fp = next((f for f in footprints
                           if f and f["suporte_id"] == row["suporte_id"]), None)
                if fp is None:
                    continue
                units.append({
                    "unidade_tipo": "pegada_conglomerado",
                    "unidade_id": row["suporte_id"],
                    "unidade_label": "pegada " + row["suporte_id"],
                    "uf": row["uf"], "ano": int(row["ano"]),
                    "resolucao_graus": "",
                    "n_uas": row["suporte_n_uas_empilhadas"],
                    "area_unidade_km2": round(fp["area_ha"] / 100.0, 6),
                    "geometry": fp["geometry"],
                })
            if units:
                import geopandas as gpd

                units_gdf = gpd.GeoDataFrame(units, crs="EPSG:4326")
                territorial, ter_meta = compute_territorial_units(
                    units_gdf, ibge_vegetation_path, mapbiomas_pattern,
                    ibge_version=ibge_version, max_units=max_units)
                ter_status = "ok" if not territorial.empty else "sem_dados"
            else:
                ter_status = "sem_unidades"
        else:
            if not municipalities_path:
                ter_status = "municipio_sem_malha"
            else:
                import geopandas as gpd

                pairs = df[["municipio_codigo", "municipio", "uf", "ano"]].copy()
                pairs["ano"] = pd.to_numeric(pairs["ano"], errors="coerce")
                pairs = pairs.dropna(subset=["ano"])
                pairs = pairs[pairs["municipio_codigo"].astype(str).str.len() > 0]
                requested = pairs.drop_duplicates(
                    ["municipio_codigo", "ano"])
                if requested.empty:
                    ter_status = "municipio_sem_malha"
                else:
                    munis = (munis_ref if munis_ref is not None
                             else load_municipalities(municipalities_path))
                    wanted = set(requested["municipio_codigo"])
                    munis = munis[munis["municipio_codigo"].isin(wanted)].copy()
                    munis_area = munis.to_crs("EPSG:5880")
                    area_km2 = {row["municipio_codigo"]:
                                float(row.geometry.area / 1e6)
                                for _, row in munis_area.iterrows()}
                    units = []
                    for _, row in requested.iterrows():
                        geom = munis.loc[munis["municipio_codigo"] ==
                                         row["municipio_codigo"], "geometry"]
                        if not len(geom):
                            continue
                        units.append({
                            "unidade_tipo": "municipio",
                            "unidade_id": row["municipio_codigo"],
                            "unidade_label": row["municipio"],
                            "uf": row["uf"], "ano": int(row["ano"]),
                            "resolucao_graus": "",
                            "n_uas": "",
                            "area_unidade_km2": round(
                                area_km2.get(row["municipio_codigo"], np.nan), 6),
                            "geometry": geom.iloc[0],
                        })
                    if units:
                        units_gdf = gpd.GeoDataFrame(units, crs=munis.crs)
                        territorial, ter_meta = compute_territorial_units(
                            units_gdf, ibge_vegetation_path,
                            mapbiomas_pattern, ibge_version=ibge_version,
                            max_units=max_units)
                        ter_status = "ok" if not territorial.empty else "sem_dados"

    summary = _territorial_summary(territorial)
    join_key = ("suporte_id" if spatial_support == "footprint"
                else "municipio_codigo")
    if len(summary):
        df = df.merge(
            summary.rename(columns={"unidade_id": "ter_unidade_id",
                                    "ano_mapbiomas": "ter_ano_mapbiomas"}),
            left_on=[join_key, "ano"],
            right_on=["ter_unidade_id", "ter_ano_mapbiomas"], how="left")
        df["ter_status"] = np.where(df["ter_ano_mapbiomas"].notna(), "ok",
                                    "ano_sem_mapa")
    else:
        for col in ("ter_unidade_id", "ter_ano_mapbiomas",
                    "ter_prop_mapbiomas_3", "ter_prop_mapbiomas_4",
                    "ter_prop_mapbiomas_5", "ter_prop_mapbiomas_6",
                    "ter_prop_mapbiomas_11", "ter_prop_mapbiomas_12",
                    "ter_prop_mapbiomas_3_4", "ter_prop_ibge_vegetacao_natural",
                    "ter_classe_ibge_dominante",
                    "ter_frac_ibge_natural_antropico_mapbiomas",
                    "ter_denominador_km2"):
            df[col] = ""
        df["ter_status"] = ter_status
    df["ter_suporte"] = spatial_support
    df["ter_colecao"] = "MapBiomas Col.11"

    def _compat_prop(row: pd.Series) -> Any:
        codes = [c for c in str(row.get("tip_mapbiomas_compativeis", "")
                                ).split("|") if c.isdigit()]
        if not codes or str(row.get("ter_status", "")) != "ok":
            return ""
        total, found = 0.0, False
        for code in codes:
            col = f"ter_prop_mapbiomas_{code}"
            value = row.get(col, "")
            if value not in ("", None) and pd.notna(value):
                total += float(value)
                found = True
        return round(total, 6) if found else ""

    df["ter_prop_mapbiomas_compativeis"] = df.apply(_compat_prop, axis=1)

    # ---------------- elegibilidade ----------------
    agb_ok = pd.to_numeric(df["agb_mg_ha"], errors="coerce").notna()
    ano_ok = pd.to_numeric(df.get("ano", pd.Series(dtype=float)),
                           errors="coerce").notna()
    univoco = df["tip_status_correspondencia"].eq("univoco")
    motivo, elegivel, elegivel_anual = [], [], []
    for i in range(len(df)):
        if not univoco.iloc[i]:
            elegivel.append(False)
            elegivel_anual.append(False)
            motivo.append(
                f"correspondencia_{df['tip_status_correspondencia'].iloc[i]}")
        elif not agb_ok.iloc[i]:
            elegivel.append(False)
            elegivel_anual.append(False)
            motivo.append("agb_ausente_ou_invalida")
        else:
            elegivel.append(True)
            if ano_ok.iloc[i]:
                elegivel_anual.append(True)
                motivo.append("")
            else:
                elegivel_anual.append(False)
                motivo.append("sem_ano_de_campo")
    df["elegivel_treino_fitofisionomia"] = elegivel
    df["elegivel_treino_anual"] = elegivel_anual
    df["motivo_exclusao"] = motivo
    df["elegivel_dominio_3_4_prova_pixel"] = False
    df["motivo_dominio"] = MOTIVO_DOMINIO
    df["classe_pixel_mapbiomas_parcela"] = ""
    df["motivo_ausencia_classe_pixel"] = MOTIVO_SEM_PIXEL
    df["origem_fitofisionomia"] = np.where(
        df["tip_fitofisionomia_ibge"].astype(str).str.len() > 0,
        ORIGEM_TEMATICA, "")
    df["grupo_conglomerado"] = df["ua"]
    df["grupo_suporte"] = df["suporte_id"]
    df["grupo_territorial"] = df.apply(
        lambda r: str(r["municipio_codigo"]) if str(r["municipio_codigo"]) else
        f"{r['uf']}|{r['municipio']}", axis=1)
    df["modalidade_agb"] = "calculada_pelo_sfb_a_partir_de_medicoes_de_campo"
    df["tipologias_ifn"] = df.get(TIPOLOGIA, "")

    rename = {"biome": "bioma", "support_area_ha": "area_amostral_ha",
              "agb_uncertainty_mg_ha": "agb_se_mg_ha",
              "allometric_equation": "agb_equacao"}
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    cols = ["observation_id", "ua", "bioma", "uf", "municipio",
            "municipio_codigo", "data_campo", "ano", "tipologias_ifn",
            USO, "tip_fitofisionomia_ibge", "tip_fitofisionomia_candidatas",
            "tip_status_correspondencia", "tip_regra_correspondencia",
            "tip_nivel_detalhe", "tip_fonte_correspondencia",
            "tip_mapbiomas_compativeis",
            "origem_fitofisionomia", "uso_fitofisionomia_ibge",
            "uso_status_correspondencia", "classe_pixel_mapbiomas_parcela",
            "motivo_ausencia_classe_pixel", "agb_mg_ha", "agb_se_mg_ha",
            "agb_equacao", "modalidade_agb", "area_amostral_ha",
            "ter_suporte", "ter_status", "ter_unidade_id", "ter_ano_mapbiomas",
            "ter_colecao", "ter_denominador_km2", "suporte_id",
            "suporte_area_ha", "suporte_area_medida_ha",
            "suporte_raio_m", "suporte_comprimento_m",
            "suporte_precisao_decimais", "suporte_incerteza_max_m",
            "suporte_n_obs_empilhadas", "suporte_n_uas_empilhadas",
            "suporte_n_linhas_painel",
            "ter_prop_mapbiomas_3", "ter_prop_mapbiomas_4",
            "ter_prop_mapbiomas_5", "ter_prop_mapbiomas_6",
            "ter_prop_mapbiomas_11", "ter_prop_mapbiomas_12",
            "ter_prop_mapbiomas_3_4", "ter_prop_mapbiomas_compativeis",
            "ter_prop_ibge_vegetacao_natural", "ter_classe_ibge_dominante",
            "ter_frac_ibge_natural_antropico_mapbiomas",
            "elegivel_treino_fitofisionomia", "motivo_exclusao",
            "elegivel_treino_anual", "elegivel_dominio_3_4_prova_pixel",
            "motivo_dominio", "grupo_conglomerado", "grupo_suporte",
            "grupo_territorial", "quality_flags"]
    out_df = df[[c for c in cols if c in df.columns]].copy()
    out_df = out_df.rename(columns={USO: "uso_campo_ifn"})
    out_df = out_df.sort_values("observation_id").reset_index(drop=True)
    _write_csv(out_df.to_dict(orient="records"), out / "ifn_enriquecido.csv")
    _write_csv(evidencias, out / "ifn_evidencias_associacao.csv")
    if not territorial.empty:
        _write_csv(territorial.to_dict(orient="records"),
                   out / "ifn_territorio_unidades.csv")

    # ---------------- verificações e relatório ----------------
    checks = {
        "linhas_saida": int(len(out_df)),
        "observation_id_unicos": int(out_df["observation_id"].nunique()),
        "sem_duplicacao": bool(out_df["observation_id"].nunique() == len(out_df)),
        "fitofisionomia_somente_univoca": bool(
            (out_df.loc[out_df["tip_status_correspondencia"] != "univoco",
                        "tip_fitofisionomia_ibge"].astype(str) == "").all()),
        "classe_pixel_sempre_ausente": bool(
            (out_df["classe_pixel_mapbiomas_parcela"].astype(str) == "").all()),
        "territorio_ok": ter_status == "ok",
    }
    if not territorial.empty:
        mb = territorial[territorial["tipo"] == "mapbiomas_nivel2"].copy()
        mb["proporcao"] = pd.to_numeric(mb["proporcao"], errors="coerce")
        sums = mb.groupby(["unidade_id", "ano_mapbiomas"])["proporcao"].sum()
        checks["prop_mapbiomas_soma_1"] = bool(((sums - 1).abs() <= 1e-3).all())
        ib = territorial[territorial["tipo"] == "ibge_legenda1"].copy()
        ib["proporcao"] = pd.to_numeric(ib["proporcao"], errors="coerce")
        sums_i = ib.groupby("unidade_id")["proporcao"].sum()
        checks["prop_ibge_soma_1"] = bool(((sums_i - 1).abs() <= 1e-3).all())

    elegiveis = out_df[out_df["elegivel_treino_fitofisionomia"]]
    report = {
        "gerado_em": _now(),
        "insumos": {
            "painel": str(panel_path), "uf_dir": str(uf_dir),
            "correspondencia": str(correspondence_path),
            "suporte_espacial": spatial_support,
            "malha_municipal": str(municipalities_path or ""),
            "ibge_vegetacao": str(ibge_vegetation_path or ""),
            "mapbiomas": str(mapbiomas_pattern or ""),
            "mapbiomas_correspondencia": str(
                mapbiomas_correspondence_path or ""),
            "ibge_version": ibge_version, "equacao": equation,
        },
        "contagens": {
            "registros": int(len(out_df)),
            "uas_unicas": int(out_df["ua"].nunique()),
            "com_municipio": int((out_df["municipio"].astype(str) != "").sum()),
            "com_ano": int(pd.to_numeric(out_df["ano"],
                                         errors="coerce").notna().sum()),
            "com_suporte": int((out_df["suporte_id"].astype(str) != "").sum()),
            "suportes_distintos": int(out_df["suporte_id"].nunique()),
            "suportes_com_mais_de_1_ua": int(
                (out_df.groupby("suporte_id")["ua"].nunique() > 1).sum()),
        },
        "suporte_espacial": {
            "pegada_area_ha": out_df["suporte_area_ha"]
            .describe().round(4).to_dict(),
            "area_medida_ha": out_df["suporte_area_medida_ha"]
            .describe().round(4).to_dict(),
            "raio_m": out_df["suporte_raio_m"].describe().round(1).to_dict(),
            "comprimento_subunidade_m": out_df["suporte_comprimento_m"]
            .describe().round(1).to_dict(),
            "precisao_decimais": out_df["suporte_precisao_decimais"]
            .describe().round(2).to_dict(),
            "incerteza_max_m": out_df["suporte_incerteza_max_m"]
            .describe().round(1).to_dict(),
            "linhas_painel_por_ua": out_df["suporte_n_linhas_painel"]
            .describe().round(1).to_dict(),
        },
        "status_correspondencia": out_df["tip_status_correspondencia"]
        .value_counts().to_dict(),
        "mapbiomas_compatibilidade": {
            "registros_com_classes_compativeis": int(
                (out_df["tip_mapbiomas_compativeis"].astype(str) != "").sum()),
            "distribuicao_n_classes": (
                out_df.loc[out_df["tip_mapbiomas_compativeis"].astype(str) != "",
                           "tip_mapbiomas_compativeis"]
                .astype(str).str.count(r"\|").add(1)
                .value_counts().sort_index().to_dict()),
        },
        "elegiveis_treino_fitofisionomia": int(len(elegiveis)),
        "elegiveis_por_fitofisionomia": (
            elegiveis.groupby("tip_fitofisionomia_ibge").size()
            .sort_values(ascending=False).to_dict()),
        "elegiveis_por_ano": {
            str(int(k)): int(v) for k, v in
            elegiveis.assign(ano=pd.to_numeric(elegiveis["ano"], errors="coerce")
                             ).dropna(subset=["ano"]).groupby("ano").size().items()},
        "exclusoes_por_motivo": (
            out_df[~out_df["elegivel_treino_fitofisionomia"]]["motivo_exclusao"]
            .value_counts().to_dict()),
        "territorio": {
            "status": ter_status,
            "linhas": int(len(territorial)),
            "unidades_calculadas": ter_meta.get("unidades_calculadas", 0),
            "legenda1_classes": ter_meta.get("legenda1_classes", []),
        },
        "verificacoes": checks,
        "limitacoes": [
            "IFN publico nao divulga a posicao exata da parcela: o suporte e a "
            "pegada documentada do conglomerado (Cruz de Malta) centrada no "
            "ponto publicado; a coordenada publicada pode ser arredondada "
            "(suporte_precisao_decimais / suporte_incerteza_max_m)",
            "a pegada documentada representa a area amostral medida (4 "
            "subunidades 20x50 m ou 20x100 m na Amazonia, 10 m de vao), nao a "
            "posicao de cada arvore",
            "fitofisionomia vem de correspondencia tematica (categoria "
            "publicada), nao de localizacao em poligono IBGE",
            "composicao na pegada e atributo da unidade amostral; nao "
            "substitui prova de pixel 3/4 para a parcela",
            "IBGE 1:250k nao tem dimensao temporal; verificar defasagem com "
            "MapBiomas (ter_frac_ibge_natural_antropico_mapbiomas)",
            "pesos de desenho do IFN nao sao publicados por linha; area_ha e "
            "a area amostral da tipologia na subunidade",
        ],
    }
    (out / "relatorio_enriquecimento.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


# --------------------------------------------------------------------- validação
def validate_correspondence(
    points_path: str | Path,
    ibge_vegetation_path: str | Path,
    correspondence_path: str | Path,
    out_dir: str | Path,
    *,
    tipologia_col: str = "tipologia",
    source_col: str = "fonte",
) -> dict[str, Any]:
    """Valida a regra temática contra a vegetação IBGE no ponto (base externa).

    A regra usa **apenas o atributo** (tipologia do ponto); a coordenada serve
    somente para obter a referência no polígono IBGE, conforme o desenho de
    validação com simulação de ausência de coordenada.
    """
    import geopandas as gpd

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    corr = load_correspondence(correspondence_path)
    index = compile_correspondence(corr)

    pts = gpd.read_file(points_path)
    if tipologia_col not in pts.columns:
        raise KeyError(f"coluna {tipologia_col} ausente em {points_path}")
    if pts.crs is None:
        pts = pts.set_crs("EPSG:4674")
    pts = pts.to_crs("EPSG:4326").reset_index(drop=True)
    pts["_pid"] = np.arange(len(pts))

    pred = [match_category(v, TIPOLOGIA, index)
            for v in pts[tipologia_col].astype(str)]
    pts["classe_predita"] = [p["classe_ibge"] for p in pred]
    pts["vinculo"] = [p["vinculo"] for p in pred]

    ibge = gpd.read_file(ibge_vegetation_path,
                         columns=["legenda_1", "leg_sup"])
    if ibge.crs is None:
        ibge = ibge.set_crs("EPSG:4674")
    ibge = ibge.to_crs("EPSG:4326")
    ibge["_natural"] = ibge["leg_sup"].astype(str).str.startswith(
        "Vegetação Natural")
    joined = gpd.sjoin(pts[["_pid", "classe_predita", "vinculo",
                            source_col, "geometry"]],
                       ibge[["legenda_1", "_natural", "geometry"]],
                       how="left", predicate="within")
    joined = joined.sort_values(["_pid", "_natural"],
                                ascending=[True, False]).drop_duplicates("_pid")
    joined["classe_referencia"] = np.where(
        joined["_natural"].fillna(False), joined["legenda_1"].fillna(""), "")

    valid = joined[(joined["classe_predita"] != "")
                   & (joined["classe_referencia"] != "")]
    concordantes = (valid["classe_predita"] == valid["classe_referencia"])
    crosstab = pd.crosstab(valid["classe_predita"],
                           valid["classe_referencia"]).reset_index()
    por_classe = []
    for classe, sub in valid.groupby("classe_predita"):
        ok = (sub["classe_predita"] == sub["classe_referencia"]).sum()
        por_classe.append({"classe_predita": classe, "n": int(len(sub)),
                           "concordantes": int(ok),
                           "concordancia": round(float(ok) / len(sub), 4)})
    by_source = []
    if source_col in valid.columns:
        for source, sub in valid.groupby(source_col):
            ok = (sub["classe_predita"] == sub["classe_referencia"]).sum()
            by_source.append({"fonte": str(source), "n": int(len(sub)),
                              "concordancia": round(float(ok) / len(sub), 4)})
    resid = (valid[valid["classe_predita"] != valid["classe_referencia"]]
             .groupby(["classe_predita", "classe_referencia"]).size()
             .sort_values(ascending=False).head(15).reset_index(name="n")
             .to_dict(orient="records"))

    _write_csv(crosstab.to_dict(orient="records"),
               out / "validacao_crosstab.csv")
    _write_csv(por_classe, out / "validacao_por_classe.csv")
    _write_csv(by_source, out / "validacao_por_fonte.csv")
    _write_csv(resid, out / "validacao_residuais.csv")

    report = {
        "gerado_em": _now(), "base": str(points_path),
        "referencia": str(ibge_vegetation_path),
        "pontos": int(len(pts)),
        "com_classe_predita": int((pts["classe_predita"] != "").sum()),
        "sem_correspondencia_no_atributo": int(
            (pts["classe_predita"] == "").sum()),
        "com_referencia_natural": int((joined["classe_referencia"] != "").sum()),
        "comparaveis": int(len(valid)),
        "concordancia_geral": round(float(concordantes.sum()) / len(valid), 4)
        if len(valid) else None,
        "por_classe": por_classe, "por_fonte": by_source,
        "residuais_top": resid,
    }
    (out / "relatorio_validacao.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
