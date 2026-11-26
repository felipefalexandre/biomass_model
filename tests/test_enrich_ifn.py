"""Testes do enriquecimento IFN (correspondência + território + elegibilidade)."""
from __future__ import annotations

import json

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import Point, box

from biomass_model.enrich_ifn import (
    build_ifn_enrichment,
    mapbiomas_compatible_classes,
    validate_correspondence,
)

CORRESPONDENCIA = (
    "campo_ifn,valor_ifn,classe_ibge_legenda1,classes_ibge_legenda2_candidatas,"
    "vinculo,nivel_detalhe,origem,fonte_documental,prefixos_normalizados,"
    "observacao\n"
    "tipologia_da_vegetacao,Savana,Savana,Savana Arborizada,univoco,legenda_1,"
    "correspondencia_tematica,teste,savana,\n"
    "tipologia_da_vegetacao,Floresta Ombrófila Densa,Floresta Ombrófila Densa,"
    "Densa Submontana,univoco,legenda_1,correspondencia_tematica,teste,"
    "floresta ombrofila densa,\n"
    "classe_uso_da_terra,Floresta Natural,(ampla),varias,parcial,legenda_1,"
    "correspondencia_tematica,teste,floresta natural,\n"
    "classe_uso_da_terra,Savana,Savana,Savana Arborizada,univoco,legenda_1,"
    "correspondencia_tematica,teste,savana,\n"
)

MB_CORRESPONDENCIA = (
    "classe_ibge_legenda1,bioma,mapbiomas_codigos,mapbiomas_classes,"
    "evidencia_legenda,fonte_documental,observacao\n"
    "Savana,Cerrado,4,Formação Savânica,teste,teste,\n"
    "Floresta Ombrófila Densa,Cerrado,3,Formação Florestal,teste,teste,\n"
)


def _panel(tmp_path):
    rows = [
        # ua, bioma, uf, classe_uso, tipologia, n_sub, area, agb
        ("UA1", "Cerrado", "GO", "Savana", "Savana", 1, 0.4, 20000.0),
        ("UA2", "Cerrado", "GO", "Floresta Natural",
         "Floresta Ombrófila Densa", 2, 0.2, 30000.0),
        ("UA2", "Cerrado", "GO", "Savana", "Savana", 2, 0.2, 10000.0),
        ("UA3", "Cerrado", "GO", "Floresta Natural",
         "Vegetação Secundária", 1, 0.4, 15000.0),
    ]
    df = pd.DataFrame(rows, columns=[
        "ua", "bioma", "uf", "classe_uso_da_terra", "tipologia_da_vegetacao",
        "n_subunidades", "area_ha", "agb_media_kg_por_ha"])
    df["lon_pc"] = -47.1
    df["lat_pc"] = -15.1
    df["sanidade"] = "Vivas"
    df["equacoes"] = "AGB_Chave"
    df["agb_variancia_por_ua"] = 0.0
    path = tmp_path / "painel.csv"
    df.to_csv(path, sep=";", index=False, encoding="utf-8")
    return path


def _uf_dir(tmp_path):
    d = tmp_path / "uf"
    d.mkdir()
    pd.DataFrame({
        "ua": ["UA1", "UA2", "UA3"],
        "mun": ["Municipio A", "Municipio A", "Municipio A"],
        "uf": ["GO", "GO", "GO"],
        "data": ["2018/10/19 00:00:00"] * 3,
    }).to_csv(d / "ua_go.csv", index=False, encoding="utf-8-sig")
    return d


def _municipalities(tmp_path):
    gdf = gpd.GeoDataFrame(
        {"CD_MUN": ["5200010"], "NM_MUN": ["Municipio A"],
         "SIGLA_UF": ["GO"]},
        geometry=[box(-47.2, -15.2, -46.8, -15.0)], crs="EPSG:4326")
    path = tmp_path / "munis.gpkg"
    gdf.to_file(path, driver="GPKG")
    return path


def _ibge(tmp_path):
    gdf = gpd.GeoDataFrame(
        {"legenda_1": ["Savana", "Floresta Ombrófila Densa",
                       "Savana"],
         "leg_sup": ["Vegetação Natural Dominante",
                     "Vegetação Natural Dominante",
                     "Área Antrópica Dominante"]},
        geometry=[box(-47.2, -15.2, -47.0, -15.0),
                  box(-47.0, -15.2, -46.8, -15.0),
                  box(-47.2, -15.0, -47.1, -14.9)], crs="EPSG:4326")
    path = tmp_path / "vege.gpkg"
    gdf.to_file(path, driver="GPKG")
    return path


def _mapbiomas(tmp_path):
    # raster fino (~11 m): cobre a pegada de 60 m no entorno do ponto
    fine = np.full((200, 200), 4, dtype="uint8")
    fine[0, 0] = 3  # fora da pegada
    fine_path = tmp_path / "mapbiomas_fine_2018.tif"
    with rasterio.open(
        fine_path, "w", driver="GTiff", height=200, width=200, count=1,
        dtype="uint8", crs="EPSG:4326",
        transform=from_origin(-47.11, -15.09, 0.0001, 0.0001), nodata=0,
    ) as dst:
        dst.write(fine, 1)
    # raster grosso (~4,4 km): metade oeste = 4, leste = 3 (município)
    coarse = np.full((10, 10), 4, dtype="uint8")
    coarse[:, 5:] = 3
    coarse[0, 0] = 15
    coarse_path = tmp_path / "mapbiomas_coarse_2018.tif"
    with rasterio.open(
        coarse_path, "w", driver="GTiff", height=10, width=10, count=1,
        dtype="uint8", crs="EPSG:4326",
        transform=from_origin(-47.2, -15.0, 0.04, 0.02), nodata=0,
    ) as dst:
        dst.write(coarse, 1)
    return str(tmp_path / "mapbiomas_fine_{year}.tif"), \
        str(tmp_path / "mapbiomas_coarse_{year}.tif")


@pytest.fixture()
def insumos(tmp_path):
    corr = tmp_path / "correspondencia.csv"
    corr.write_text(CORRESPONDENCIA, encoding="utf-8")
    mb_corr = tmp_path / "mapbiomas_correspondencia.csv"
    mb_corr.write_text(MB_CORRESPONDENCIA, encoding="utf-8")
    mb_fine, mb_coarse = _mapbiomas(tmp_path)
    return {
        "panel": _panel(tmp_path),
        "uf_dir": _uf_dir(tmp_path),
        "corr": corr,
        "mb_corr": mb_corr,
        "munis": _municipalities(tmp_path),
        "ibge": _ibge(tmp_path),
        "mb_fine": mb_fine,
        "mb_coarse": mb_coarse,
    }


def test_enriquecimento_sem_mapas(insumos):
    """Campos territoriais permanecem ausentes sem insumos de mapa."""
    report = build_ifn_enrichment(
        insumos["panel"], insumos["uf_dir"], insumos["corr"],
        insumos["panel"].parent / "out_sem_mapa",
        mapbiomas_correspondence_path=insumos["mb_corr"],
    )
    assert report["contagens"]["registros"] == 3
    assert report["verificacoes"]["sem_duplicacao"] is True
    out = pd.read_csv(insumos["panel"].parent / "out_sem_mapa"
                      / "ifn_enriquecido.csv")
    assert out["ter_status"].eq("sem_insumos_mapas").all()
    assert out["ter_prop_mapbiomas_3"].isna().all()
    assert out["classe_pixel_mapbiomas_parcela"].isna().all()


def test_correspondencia_e_elegibilidade(insumos):
    out_dir = insumos["panel"].parent / "out"
    report = build_ifn_enrichment(
        insumos["panel"], insumos["uf_dir"], insumos["corr"], out_dir,
        municipalities_path=insumos["munis"],
        ibge_vegetation_path=insumos["ibge"],
        mapbiomas_pattern=insumos["mb_coarse"],
        mapbiomas_correspondence_path=insumos["mb_corr"],
    )
    out = pd.read_csv(out_dir / "ifn_enriquecido.csv").set_index("ua")
    assert report["verificacoes"]["sem_duplicacao"] is True

    # UA1: Savana unívoca
    assert out.loc["UA1", "tip_fitofisionomia_ibge"] == "Savana"
    assert out.loc["UA1", "tip_status_correspondencia"] == "univoco"
    assert str(out.loc["UA1", "tip_mapbiomas_compativeis"]) in ("4", "4.0")
    assert bool(out.loc["UA1", "elegivel_treino_fitofisionomia"]) is True

    # UA2: duas tipologias com alvos diferentes -> múltiplo, sem classe única
    assert out.loc["UA2", "tip_status_correspondencia"] == "multiplo"
    assert str(out.loc["UA2", "tip_fitofisionomia_ibge"]) in ("", "nan")
    assert "Savana" in str(out.loc["UA2", "tip_fitofisionomia_candidatas"])
    assert "Floresta Ombrófila Densa" in str(
        out.loc["UA2", "tip_fitofisionomia_candidatas"])
    assert bool(out.loc["UA2", "elegivel_treino_fitofisionomia"]) is False

    # UA3: categoria sem correspondência documentada
    assert out.loc["UA3", "tip_status_correspondencia"] == "sem_correspondencia"
    assert out.loc["UA3", "motivo_exclusao"] == (
        "correspondencia_sem_correspondencia")
    # AGB não é duplicada mesmo quando há múltiplas tipologias
    assert len(out) == 3

    # Domínio 3/4 nunca comprovado sem posição exata
    assert out["elegivel_dominio_3_4_prova_pixel"].eq(False).all()

    # grupos de divisão
    assert out.loc["UA1", "grupo_conglomerado"] == "UA1"
    assert str(out.loc["UA1", "grupo_territorial"]) == "5200010"
    # empilhamento de registros do painel por UA (classes x equacoes)
    assert int(out.loc["UA2", "suporte_n_linhas_painel"]) == 2


def test_suporte_pegada_denominadores(insumos):
    out_dir = insumos["panel"].parent / "out_terr"
    report = build_ifn_enrichment(
        insumos["panel"], insumos["uf_dir"], insumos["corr"], out_dir,
        municipalities_path=insumos["munis"],
        ibge_vegetation_path=insumos["ibge"],
        mapbiomas_pattern=insumos["mb_fine"],
        mapbiomas_correspondence_path=insumos["mb_corr"],
    )
    assert report["insumos"]["suporte_espacial"] == "footprint"
    assert report["verificacoes"]["territorio_ok"] is True
    assert report["verificacoes"]["prop_mapbiomas_soma_1"] is True
    assert report["verificacoes"]["prop_ibge_soma_1"] is True

    terr = pd.read_csv(out_dir / "ifn_territorio_unidades.csv")
    assert set(terr["unidade_tipo"]) == {"pegada_conglomerado"}
    mb = terr[terr["tipo"] == "mapbiomas_nivel2"]
    assert mb["proporcao"].sum() == pytest.approx(1.0, abs=1e-3)
    # a pegada (~60 m) cai inteira no pixel de Formação Savânica do teste
    classes = set(mb["classe"].str.split(" ").str[0])
    assert classes == {"4"}
    # IBGE só com vegetação natural (o polígono antrópico é excluído)
    ib = terr[terr["tipo"] == "ibge_legenda1"]
    assert ib["proporcao"].sum() == pytest.approx(1.0, abs=1e-3)
    assert set(ib["classe"]) == {"Savana"}

    out = pd.read_csv(out_dir / "ifn_enriquecido.csv").set_index("ua")
    assert float(out.loc["UA1", "ter_prop_mapbiomas_4"]) == pytest.approx(1.0)
    assert float(out.loc["UA1", "ter_prop_mapbiomas_compativeis"]) == (
        pytest.approx(1.0))
    # pegada documentada: 0,4 ha (4 subunidades de 20 x 50 m fora da Amazônia)
    assert float(out.loc["UA1", "suporte_area_ha"]) == pytest.approx(0.4)
    # três UAs na mesma coordenada -> empilhamento registrado
    assert int(out.loc["UA1", "suporte_n_uas_empilhadas"]) == 3


def test_suporte_municipio_alternativo(insumos):
    out_dir = insumos["panel"].parent / "out_mun"
    report = build_ifn_enrichment(
        insumos["panel"], insumos["uf_dir"], insumos["corr"], out_dir,
        spatial_support="municipio",
        municipalities_path=insumos["munis"],
        ibge_vegetation_path=insumos["ibge"],
        mapbiomas_pattern=insumos["mb_coarse"],
        mapbiomas_correspondence_path=insumos["mb_corr"],
    )
    assert report["insumos"]["suporte_espacial"] == "municipio"
    terr = pd.read_csv(out_dir / "ifn_territorio_unidades.csv")
    assert set(terr["unidade_tipo"]) == {"municipio"}
    mb = terr[terr["tipo"] == "mapbiomas_nivel2"]
    assert mb["proporcao"].sum() == pytest.approx(1.0, abs=1e-3)
    assert {"3", "4"}.issubset(
        set(mb["classe"].str.split(" ").str[0]))


def test_validacao_tematica(insumos):
    pts = gpd.GeoDataFrame(
        {"tipologia": ["Savana", "Floresta Ombrófila Densa",
                       "Vegetação Secundária"],
         "fonte": ["RADAM-BR", "RADAM-BR", "RADAM-BR"]},
        geometry=[Point(-47.1, -15.1), Point(-46.9, -15.1),
                  Point(-47.1, -15.1)],
        crs="EPSG:4326")
    path = insumos["panel"].parent / "pontos.gpkg"
    pts.to_file(path, driver="GPKG")
    out_dir = insumos["panel"].parent / "out_val"
    report = validate_correspondence(
        path, insumos["ibge"], insumos["corr"], out_dir)
    assert report["pontos"] == 3
    assert report["sem_correspondencia_no_atributo"] == 1
    assert report["comparaveis"] == 2
    assert report["concordancia_geral"] == 1.0
    assert (out_dir / "validacao_por_classe.csv").exists()


def test_pegada_documentada():
    """Dimensões da Cruz de Malta conforme a metodologia do IFN/SFB."""
    from biomass_model.enrich_ifn import ifn_footprint

    fp = ifn_footprint(-47.1, -15.1, "Cerrado", 4)
    assert fp["area_ha"] == pytest.approx(0.4)
    assert fp["comprimento_subunidade_m"] == 50
    assert fp["raio_m"] == pytest.approx(60.83, abs=0.05)
    assert fp["n_subunidades"] == 4
    minx, miny, maxx, maxy = fp["geometry"].bounds
    assert (maxx - minx) < 0.01 and (maxy - miny) < 0.01

    amazon = ifn_footprint(-60.0, -3.0, "Amazônia", 4)
    assert amazon["area_ha"] == pytest.approx(0.8)
    assert amazon["comprimento_subunidade_m"] == 100
    assert amazon["raio_m"] == pytest.approx(110.45, abs=0.05)

    partial = ifn_footprint(-47.1, -15.1, "Cerrado", 2)
    assert partial["area_ha"] == pytest.approx(0.4)
    assert partial["area_medida_ha"] == pytest.approx(0.2)


def test_mapbiomas_compat_por_bioma(insumos):
    from biomass_model.enrich_ifn import (
        compile_mapbiomas_correspondence,
        load_mapbiomas_correspondence,
    )

    index = compile_mapbiomas_correspondence(
        load_mapbiomas_correspondence(insumos["mb_corr"]))
    assert mapbiomas_compatible_classes(index, "Savana", "Cerrado") == [4]
    assert mapbiomas_compatible_classes(
        index, "Floresta Ombrófila Densa", "Cerrado") == [3]
    # bioma sem linha cai no curinga/união, sem inventar código
    assert mapbiomas_compatible_classes(index, "Savana", "Pampa") == [4]
    assert mapbiomas_compatible_classes(index, "", "Cerrado") == []
