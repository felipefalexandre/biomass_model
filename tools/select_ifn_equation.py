"""Seleção de equação alométrica no Painel de Biomassa e Carbono (IFN/SFB).

Reduz a matriz UA x classe x equação (439.970 linhas) para:
  - 1 linha por (UA, tipologia) com a equação escolhida;
  - 1 linha por UA com AGB agregado por área entre tipologias.

Regra de seleção por grupo (bioma, tipologia), em ordem (determinística):
  1. maior nº de pares "Equivalente" no teste oficial de equivalência (TOST);
  2. equação coberta pelo teste do grupo;
  3. bioma do catálogo igual ao bioma do grupo;
  4. fito do catálogo igual à tipologia do grupo;
  5. peso "Seco" sobre "Fresco";
  6. maior r2 (normalizado; ausente = -1);
  7. menor syx (ausente = +inf);
  8. id crescente.

Se a equação escolhida não existe em uma UA do grupo, desce a lista ranqueada
(`equation_fallback_rank_N`). Valores em kg/ha são convertidos para Mg/ha (÷1000).

Insumos oficiais (CC BY, dados.florestal.gov.br): CSV de biomassa (ou GeoPackage),
`equacoes_oficial.csv` e `teste_equacoes.csv`. Somente leitura nos insumos.
Somente stdlib (sqlite3, csv, json) — não requer pandas/geopandas.

Uso:
  python tools/select_ifn_equation.py \
    --gpkg <pontos_sfb.gpkg> \
    --equacoes data/raw/inventarios/sfb/equacoes_oficial.csv \
    --teste data/raw/inventarios/sfb/teste_equacoes.csv \
    --out-dir data/processed/ifn_selection
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

CITATION = "SFB/IFN — Painel de Biomassa e Carbono (CC BY)"


# ----------------------------------------------------------------- utilitarios
def _fixkey(key: str) -> str:
    """Remove BOM/sujeira do cabeçalho (ex.: '\\ufeffbioma', 'bioma' com acento)."""
    return re.sub(r"^[^A-Za-z_]+", "", key)


def _parse_num(text: str | None) -> float | None:
    """Extrai número de valores como '0,95', '47,9(%)', '43 kg', '-1'."""
    if text is None:
        return None
    s = str(text).strip()
    s = re.sub(r"\(.*?\)", "", s)
    s = s.replace("%", "").replace(",", ".").strip()
    if s in ("", "-", "NA", "na", "NaN"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _norm_r2(value: float | None) -> float | None:
    """Normaliza r2 para fração (algumas linhas vêm em percentual: 98.7)."""
    if value is None:
        return None
    return value / 100.0 if value > 1.5 else value


def _load_catalog(path: Path) -> dict[str, dict]:
    # CSVs oficiais do portal sao UTF-8 com BOM (verificado nos bytes)
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = [{_fixkey(k): v for k, v in row.items()}
                for row in csv.DictReader(fh, delimiter=";")]
    cat: dict[str, dict] = {}
    for row in rows:
        eq_id = str(row.get("id", "")).strip()
        if not eq_id:
            continue
        cat[eq_id] = {
            "bioma": str(row.get("bioma", "")).strip(),
            "fito": str(row.get("fito", "")).strip(),
            "peso": str(row.get("peso", "")).strip(),
            "d_min": _parse_num(row.get("d.min")),
            "d_max": _parse_num(row.get("d.max")),
            "r2": _norm_r2(_parse_num(row.get("r2/r2aj"))),
            "syx": _parse_num(row.get("syx")),
            "autor": str(row.get("autor", "")).strip(),
        }
    return cat


def _load_equivalence(path: Path):
    """Retorna (arestas_equivalentes por grupo, pares por grupo)."""
    edges: dict[tuple[str, str], Counter] = defaultdict(Counter)
    totals: dict[tuple[str, str], Counter] = defaultdict(Counter)
    pairs: dict[tuple[str, str, str, str], str] = {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh, delimiter=";"):
            row = {_fixkey(k): v for k, v in row.items()}
            key = (row["bioma"].strip(), row["tipologia"].strip())
            e1 = row["equacao_1"].strip()
            e2 = row["equacao_2"].strip()
            totals[key][e1] += 1
            totals[key][e2] += 1
            if row["equivalente"].strip() == "Equivalente":
                edges[key][e1] += 1
                edges[key][e2] += 1
            pairs[(key[0], key[1], e1, e2)] = row["equivalente"].strip()
    return edges, totals, pairs


def _pair_status(pairs, bioma: str, tipologia: str, a: str, b: str):
    """Status do par (a,b) no teste; tenta as duas ordens."""
    for pair in ((a, b), (b, a)):
        status = pairs.get((bioma, tipologia, pair[0], pair[1]))
        if status is not None:
            return status
    return None


# ----------------------------------------------------------------- selecao
def _rank_group(group_eqs: set[str], key: tuple[str, str],
                cat: dict[str, dict], edges, totals) -> list[str]:
    """Ordena as equações candidatas do grupo pela regra documentada."""

    def sort_key(eq_id: str):
        meta = cat.get(eq_id, {})
        r2 = meta.get("r2")
        syx = meta.get("syx")
        return (
            -edges.get(key, {}).get(eq_id, 0),          # 1. consenso TOST
            -int(totals.get(key, {}).get(eq_id, 0) > 0),  # 2. coberto pelo teste
            -int(meta.get("bioma", "") == key[0]),       # 3. bioma específico
            -int(meta.get("fito", "") == key[1]),        # 4. fito específico
            -int(meta.get("peso", "") == "Seco"),        # 5. peso seco
            -(r2 if r2 is not None else -1.0),           # 6. maior r2
            (syx if syx is not None else math.inf),      # 7. menor syx
            eq_id,                                       # 8. determinismo
        )

    return sorted(group_eqs, key=sort_key)


def _decimals(value: float) -> int:
    text = repr(float(value))
    if "." not in text:
        return 0
    return len(text.split(".")[1].rstrip("0"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gpkg", required=True, help="pontos_sfb.gpkg (ou use --csv)")
    ap.add_argument("--csv", default=None, help="CSV oficial do painel (alternativa ao gpkg)")
    ap.add_argument("--equacoes", required=True, help="equacoes_oficial.csv")
    ap.add_argument("--teste", required=True, help="teste_equacoes.csv")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cat = _load_catalog(Path(args.equacoes))
    edges, totals, pairs = _load_equivalence(Path(args.teste))

    # --- leitura das linhas do painel ---
    if args.gpkg:
        con = sqlite3.connect(args.gpkg)
        cur = con.cursor()
        query = (
            "SELECT ua, bioma, uf, lon_pc, lat_pc, n_subunidades, "
            "classe_uso_da_terra, tipologia_da_vegetacao, equacoes, area_ha, "
            "agb_media_kg_por_ha, agb_variancia_por_ua, valor_r "
            "FROM pontos_sfb ORDER BY ua, tipologia_da_vegetacao, equacoes"
        )
        raw = cur.execute(query).fetchall()
        con.close()
    else:
        with open(args.csv, encoding="utf-8", encoding_errors="replace",
                  newline="") as fh:
            raw = [
                (r["ua"], r["bioma"], r["uf"], r["lon_pc"], r["lat_pc"],
                 r["n_subunidades"], r["classe_uso_da_terra"],
                 r["tipologia_da_vegetacao"], r["equacoes"], r["area_ha"],
                 r["agb_media_kg_por_ha"], r["agb_variancia_por_ua"],
                 r.get("valor_r", ""))
                for r in csv.DictReader(fh, delimiter=";")
            ]

    cols = ["ua", "bioma", "uf", "lon_pc", "lat_pc", "n_subunidades",
            "classe_uso_da_terra", "tipologia", "equacao", "area_ha",
            "agb_kg_ha", "agb_var", "valor_r"]
    rows = []
    for rec in raw:
        row = dict(zip(cols, rec))
        for name in ("lon_pc", "lat_pc", "n_subunidades", "area_ha",
                     "agb_kg_ha", "agb_var", "valor_r"):
            row[name] = _parse_num(row[name])
        for name in ("ua", "bioma", "uf", "classe_uso_da_terra",
                     "tipologia", "equacao"):
            row[name] = str(row[name]).strip()
        rows.append(row)

    # --- agrupamento (bioma, tipologia) -> equacoes; e (ua, tipologia) -> linhas ---
    group_eqs: dict[tuple[str, str], set] = defaultdict(set)
    ua_tip: dict[tuple[str, str], list[dict]] = defaultdict(list)
    ua_meta: dict[str, dict] = {}
    for row in rows:
        gkey = (row["bioma"], row["tipologia"])
        group_eqs[gkey].add(row["equacao"])
        ua_tip[(row["ua"], row["tipologia"])].append(row)
        ua_meta.setdefault(row["ua"], {
            "bioma": row["bioma"], "uf": row["uf"], "lon": row["lon_pc"],
            "lat": row["lat_pc"], "n_sub": row["n_subunidades"],
        })

    ranking = {gkey: _rank_group(eqs, gkey, cat, edges, totals)
               for gkey, eqs in group_eqs.items()}

    # --- selecao por (ua, tipologia) ---
    detail = []
    rank_hist: Counter = Counter()
    flag_hist: Counter = Counter()
    for (ua, tipologia), line_rows in sorted(ua_tip.items()):
        by_eq: dict[str, list[dict]] = defaultdict(list)
        for r in line_rows:
            by_eq[r["equacao"]].append(r)
        gkey = (line_rows[0]["bioma"], tipologia)
        chosen, rank = None, 0
        for i, eq_id in enumerate(ranking[gkey], start=1):
            if eq_id in by_eq:
                chosen, rank = eq_id, i
                break
        if chosen is None:  # pragma: no cover - grupo deriva das proprias linhas
            continue
        # mesma equacao em >1 classe da mesma tipologia: media simples
        # (areas por classe sao desconhecidas; area_ha e da tipologia)
        eq_rows = by_eq[chosen]
        row = dict(eq_rows[0])
        agbs = [r["agb_kg_ha"] for r in eq_rows
                if r["agb_kg_ha"] is not None]
        row["agb_kg_ha"] = sum(agbs) / len(agbs) if agbs else None
        meta = cat.get(chosen, {})
        flags = ["ifn_panel", "reference_date_unknown",
                 "multiple_equations", "coarse_coordinates"]
        if len(eq_rows) > 1:
            flags.append("multi_class_same_tipologia")
        rank_hist[rank] += 1
        if rank > 1:
            flags.append(f"equation_fallback_rank_{rank}")
        if gkey not in totals:
            flags.append("sem_cobertura_teste")
        status = _pair_status(pairs, gkey[0], gkey[1], chosen, "AGB_Chave")
        if status == "Não Equivalente":
            flags.append("nao_equivalente_vs_agb_chave")
        tested = totals.get(gkey, {})
        if tested.get(chosen):
            frac = 1.0 - edges.get(gkey, {}).get(chosen, 0) / tested[chosen]
        else:
            frac = None
        if meta.get("peso") and meta["peso"] != "Seco":
            flags.append("peso_fresco")
        if row["lon_pc"] is not None and _decimals(row["lon_pc"]) < 2:
            flags.append("coord_precision_gt_001deg")
        agb_mg = (row["agb_kg_ha"] or 0.0) / 1000.0
        if agb_mg > 1000:
            flags.append("agb_gt_1000_mg_ha")
        if agb_mg < 1:
            flags.append("agb_lt_1_mg_ha")
        variance = row["agb_var"]
        n_sub = row["n_subunidades"]
        se_kg = (math.sqrt(variance / n_sub)
                 if (variance and variance > 0 and n_sub and n_sub > 1)
                 else None)
        for flag in flags:
            flag_hist[flag] += 1
        detail.append({
            "ua": ua,
            "bioma": gkey[0],
            "uf": line_rows[0]["uf"],
            "tipologia": tipologia,
            "classes_uso": "|".join(sorted({r["classe_uso_da_terra"]
                                            for r in line_rows})),
            "equacao_escolhida": chosen,
            "equacao_rank": rank,
            "n_equacoes_grupo": len(group_eqs[gkey]),
            "n_equacoes_ua": len(by_eq),
            "frac_pares_nao_equivalentes": (round(frac, 4)
                                            if frac is not None else ""),
            "area_ha": row["area_ha"],
            "agb_mg_ha": round(agb_mg, 4),
            "agb_se_mg_ha": (round(se_kg / 1000.0, 4)
                             if se_kg is not None else ""),
            "agb_variancia_orig": row["agb_var"],
            "valor_r_bgb": row["valor_r"] if row["valor_r"] is not None else "",
            "autor_equacao": meta.get("autor", ""),
            "flags": ";".join(flags),
        })

    # --- agregacao por UA (media ponderada por area entre tipologias) ---
    ua_rows: dict[str, list[dict]] = defaultdict(list)
    for row in detail:
        ua_rows[row["ua"]].append(row)

    ua_out = []
    for ua, parts in sorted(ua_rows.items()):
        meta = ua_meta[ua]
        weighted = [p for p in parts if p["area_ha"] and p["area_ha"] > 0]
        total_area = sum(p["area_ha"] for p in weighted)
        if weighted and total_area > 0:
            agb = sum(p["agb_mg_ha"] * p["area_ha"] for p in weighted) / total_area
            # variancia entre tipologias com pesos (componentes: subunit + heterogeneidade)
            se = math.sqrt(sum(
                (p["agb_se_mg_ha"] ** 2) * (p["area_ha"] / total_area) ** 2
                for p in weighted if p["agb_se_mg_ha"] != ""
            )) if any(p["agb_se_mg_ha"] != "" for p in weighted) else None
        else:
            agb, se, total_area = None, None, 0.0
        flags: list[str] = []
        eqs_used = sorted({p["equacao_escolhida"] for p in parts})
        if len(eqs_used) > 1:
            flags.append("multi_equation_by_tipologia")
        if any("equation_fallback_rank" in p["flags"] for p in parts):
            flags.append("equation_fallback")
        if any("nao_equivalente_vs_agb_chave" in p["flags"] for p in parts):
            flags.append("nao_equivalente_vs_agb_chave")
        if any("agb_gt_1000_mg_ha" in p["flags"] for p in parts):
            flags.append("agb_gt_1000_mg_ha")
        if any("agb_lt_1_mg_ha" in p["flags"] for p in parts):
            flags.append("agb_lt_1_mg_ha")
        if any("coord_precision_gt_001deg" in p["flags"] for p in parts):
            flags.append("coord_precision_gt_001deg")
        if any("peso_fresco" in p["flags"] for p in parts):
            flags.append("peso_fresco")
        valor_r = sorted({str(p["valor_r_bgb"]) for p in parts
                          if p["valor_r_bgb"] != ""})
        ua_out.append({
            "ua": ua,
            "bioma": meta["bioma"],
            "uf": meta["uf"],
            "lon_pc": meta["lon"],
            "lat_pc": meta["lat"],
            "n_subunidades": meta["n_sub"],
            "n_tipologias": len(parts),
            "area_ha_total": round(total_area, 4),
            "agb_mg_ha": round(agb, 4) if agb is not None else "",
            "agb_se_mg_ha": (round(se, 4) if se is not None else ""),
            "se_components": "subunit_variance_only" if se is not None else "",
            "equacoes_usadas": "|".join(eqs_used),
            "valor_r_bgb": "|".join(valor_r),
            "flags": ";".join(flags),
        })

    # --- comparacao com o default atual (AGB_Chave; ver load_ifn_panel) ---
    chave_rows = {}
    for row in rows:
        if row["equacao"] == "AGB_Chave" and row["ua"] not in chave_rows:
            chave_rows[row["ua"]] = row
    diffs = []
    for u in ua_out:
        base = chave_rows.get(u["ua"])
        if base and u["agb_mg_ha"] != "" and base["agb_kg_ha"] is not None:
            default_mg = base["agb_kg_ha"] / 1000.0
            if default_mg > 0:
                diffs.append((u["agb_mg_ha"] / default_mg, default_mg,
                              u["agb_mg_ha"]))
    diffs.sort()

    def _pct(values, p):
        if not values:
            return None
        return values[min(int(p * (len(values) - 1)), len(values) - 1)]

    sel = sorted(u["agb_mg_ha"] for u in ua_out if u["agb_mg_ha"] != "")
    default = sorted(d[1] for d in diffs)
    ratios = sorted(d[0] for d in diffs)

    report = {
        "fonte": CITATION,
        "regra": ("por (bioma,tipologia): consenso TOST > cobertura teste > "
                  "bioma > fito > peso seco > r2 > syx > id; fallback "
                  "descendente por rank; agregacao UA = media ponderada "
                  "por area_ha entre tipologias"),
        "inputs": {"gpkg": args.gpkg or args.csv, "equacoes": args.equacoes,
                   "teste": args.teste},
        "contagens": {
            "linhas_entrada": len(rows),
            "uas": len(ua_out),
            "grupos_bioma_tipologia": len(group_eqs),
            "grupos_sem_cobertura_teste": sorted(
                f"{b}|{t}" for (b, t) in group_eqs if (b, t) not in totals),
            "detalhes_ua_tipologia": len(detail),
        },
        "rank_fallback_histogram": {str(k): v
                                    for k, v in sorted(rank_hist.items())},
        "flags_histogram": dict(sorted(flag_hist.items())),
        "equacao_escolhida_por_grupo": {
            f"{b}|{t}": detail_eq
            for (b, t), detail_eq in sorted(
                ((g, next((d["equacao_escolhida"] for d in detail
                           if (d["bioma"], d["tipologia"]) == g), ""))
                 for g in group_eqs))
        },
        "agb_mg_ha_selecionado": {
            "n": len(sel), "min": sel[0] if sel else None,
            "p05": _pct(sel, 0.05), "p50": _pct(sel, 0.50),
            "p95": _pct(sel, 0.95), "max": sel[-1] if sel else None,
            "gt_1000": sum(1 for v in sel if v > 1000),
            "lt_1": sum(1 for v in sel if v < 1),
        },
        "comparacao_default_agb_chave": {
            "n": len(default),
            "p50_default": _pct(default, 0.50),
            "p50_selecionado": _pct(sel, 0.50),
            "razao_selecionado_default_p50": _pct(ratios, 0.50),
            "razao_p05": _pct(ratios, 0.05),
            "razao_p95": _pct(ratios, 0.95),
            "uas_razao_gt2": sum(1 for r in ratios if r > 2),
            "uas_razao_lt0p5": sum(1 for r in ratios if r < 0.5),
        },
        "limitacoes": [
            "se apenas de variancia entre subunidades (nao inclui erro de "
            "equacao, alometria ou coordenada)",
            "ano de medicao ausente no painel (reference_date_unknown)",
            "tipologia classificada por informacao secundaria (SFB)",
            "coordenadas com precisao heterogenea (flag coord_precision)",
            "regra candidata: limiares nao validados por sensibilidade",
        ],
    }

    # --- escrita (UTF-8, deterministica) ---
    def write_csv(path: Path, records: list[dict]) -> None:
        if not records:
            return
        with open(path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)

    write_csv(out_dir / "ifn_tipologia_selected.csv", detail)
    write_csv(out_dir / "ifn_ua_selected.csv", ua_out)
    with open(out_dir / "relatorio_selecao.json", "w",
              encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    # resumo ASCII no console
    print("selecao ifn: OK")
    print(f"  linhas entrada : {len(rows)}")
    print(f"  detalhes       : {len(detail)} (ua x tipologia)")
    print(f"  uas            : {len(ua_out)}")
    print(f"  saidas         : {out_dir}")
    print(f"  p50 agb (selecionado) : "
          f"{report['agb_mg_ha_selecionado']['p50']}")
    print(f"  p50 agb (AGB_Chave)   : "
          f"{report['comparacao_default_agb_chave']['p50_default']}")
    print(f"  flags           : {dict(sorted(flag_hist.items()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
