# 64 — Global Canopy Atlas (GCA): avaliação para target e features (2026-11-27)

**Status:** avaliado; **não entra como target nem como feature**. Registrado como
referência secundária/validação estrutural (INV12). Complementa `ADR/0022`, `ADR/0027`,
`docs/61` e `docs/62`.

## 1. O que é

- Artigo: Fischer et al. (2026), *A global atlas of 3D woody ecosystem structure*,
  Nature Ecology & Evolution, DOI `10.1038/s41559-026-03218-8` (open access).
- Produto: **3.458 aquisições de LiDAR aerotransportado (ALS)**, 56.554 km², convertidas
  em CHM/DTM/DSM padronizados de **1 m**, com metadados de aquisição (sensor, densidade
  de pulsos, data, classificação de solo, licença).
- Cobertura: todos os biomas/reinos; 19% da área com aquisições repetidas; 87% dos
  produtos abertos (95% da área).
- Acesso: plataforma `https://globalcanopyatlas.org` (links/filtros); produtos abertos
  no MAAP/ESA; código e materiais em Zenodo `10.5281/zenodo.22177606` (o DOI citado no
  artigo, `16987210`, resolve para esse registro).

## 2. Por que **não** serve como target

1. **Não contém AGB.** Entrega altura de dossel, elevação e estrutura 3D; biomassa exige
   alometria e densidade da madeira, que não estão no produto.
2. Converter altura em AGB exigiria **calibrar ALS com parcelas de campo** — ou seja, o
   target continuaria sendo o campo; o ALS seria referência secundária, não target.
3. A cobertura é amostral (56.554 km² no mundo; 9.181 km² no Brasil), não wall-to-wall;
   não há como usá-la como mapa-alvo contínuo.

## 3. Por que **não** serve como feature

1. É **LiDAR aerotransportado**. O `ADR-0022` e o `ADR-0027` vedam GEDI/LiDAR como
   variável de inferência; o GCA é exatamente essa classe de dado.
2. Não existe na inferência wall-to-wall: usá-lo como feature criaria um modelo que
   depende de dado esparso e caro, impossível de aplicar no mapa operacional.
3. Risco de **vazamento/circularidade**: altura ALS é altamente preditiva de AGB e foi
   calibrada com campo/LiDAR em alguns produtos; o ganho em validação não seria honesto.
4. O próprio artigo mostra que mapas globais de altura derivados de satélite têm erro
   grande em resolução nativa (R² 0,28–0,38; RMSE relativo 95–189%). Isso reforça não
   usar produtos globais de altura como atalho para AGB.

## 4. Onde o GCA é útil

| Uso | Como | Estado |
|---|---|---|
| **Validação estrutural independente** | comparar altura/estrutura prevista com CHM ALS onde há sobreposição; detectar viés grosseiro do mapa | viável, mas amostra pequena |
| **Referência secundária calibrada** | em sítios com parcela de campo **e** ALS, calibrar AGB com métricas de dossel; documentar suporte, erro e origem (ADR-0027) | exige sobreposição campo–ALS |
| **Benchmark/teto de altura** | testar se features S2/S1 capturam gradientes de estrutura; comparar modelos globais de altura | útil conceitualmente |
| **Metodologia** | usar o pipeline e as camadas de qualidade (densidade de pulsos, classificação de solo, angulação) como referência para o LiDAR da Embrapa e para o nosso protocolo de validação | útil |
| **Estratificação de validação** | estratificar por estrutura/altura onde o GCA cobre, sem entrar como preditor | útil e permitido |

## 5. Sobreposição com o nosso alvo (medida)

Índice extraído do ZIP remoto do Zenodo (somente shapefiles, ~5 MB, sem baixar os 2,6 GB):

- GCA global: 3.458 aquisições;
- no *bounding box* do Brasil: **1.240** aquisições, **9.181 km²**, 1.154 abertas e 86
  fechadas; datas 2008–2023; densidade mediana de pulsos 4,84 m⁻²;
- licenças no Brasil: CC BY 4.0 (880), EOSDIS (237), não pública (120), GPLv3 (2),
  CC BY-NC (1).

Sobreposição com as UAs (ponto representativo dentro da pegada ALS):

| Conjunto | UAs com sobreposição | Detalhe |
|---|---:|---|
| Target Amazônia+Cerrado (824 UAs) | **4** | todas na Amazônia, 2016, CC BY 4.0; 1,83 ha de pegadas cobertas; 1 UA com ≥90% |
| IFN completo (7.466 UAs) | **6** | Amazônia, 2016–2017 |

**Conclusão:** a sobreposição é insuficiente para calibrar ou validar estatisticamente o
target atual. O GCA não deve bloquear o cubo de features nem o E3. Ele fica disponível
para (a) validação pontual de estrutura nos 4–6 sítios, (b) uso futuro em campanhas com
parcelas coincidentes e (c) referência metodológica.

## 6. Registro e reprodutibilidade

- Fonte registrada como **INV12** em `data/reference/inventarios_abertos.md/.csv`.
- Índice local (fora do Git): `data/raw/gca/GCA_extended_public.{shp,dbf,shx,prj,cpg}`.
- SHA-256 do índice: `GCA_extended_public.shp` =
  `b998c9449d6df68b7022805fa7c91afba950486408e80833e33038d4d9a40799`;
  `.dbf` = `76b3a5f46343ceca3a5ec0465ac81021bb124561cdf3bef634aa6be1d5e73dfd`.
- Sobreposição: `data/processed/gca/gca_sobreposicao_uas.csv` e resumo em
  `data/processed/gca/gca_sobreposicao_resumo.json`.
- Extrator usado: `tools/gca_index_overlap.py` (requisições HTTP *range* sobre o ZIP do
  Zenodo para listar/extrair só os membros do GCA; não foi necessário baixar o pacote
  completo de 2,6 GB).

## 7. Limitações

1. O índice é só metadado/pegada; **nenhum CHM de 1 m foi baixado** (3,2 TB no total).
   Qualquer validação estrutural exigirá baixar tiles específicos no MAAP.
2. Licença varia por aquisição; 120 aquisições no Brasil não são públicas. Uso comercial
   exigirá checagem caso a caso.
3. A posição da pegada IFN é incerta (2–3 casas decimais); a sobreposição ponto-dentro-de-
   polígono é uma aproximação, não uma coincidência exata de parcela.
4. O GCA não substitui validação independente de AGB; ele valida **estrutura**, não
   biomassa.
