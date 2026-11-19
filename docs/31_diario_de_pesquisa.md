# 31 — Diário de pesquisa

Registro cronológico do que foi feito, decidido e descoberto. Complementa os ADRs (decisões) e
`docs/30` (pendências).

## 2026-11-17 — Sessão 1

### Decisões recebidas do usuário

1. Piloto: um tile pequeno por bioma, escolhido por nós, desde que tenha biomassa real.
2. Anos: intervalo de anos, preferencialmente recentes, para comparar com inventários, bases
   abertas e artigos.
3. Começar por AGB; BGB como modelo separado, focado em solo, acoplado (não derivado).
4. Dados e intermediários em `E:\Mapbiomas\biomass`.
5. Domínio: classes 3 e 4 do MapBiomas, Amazônia e Cerrado; estratificação por vegetação é
   desejável.
6. Referência obrigatória: legenda MapBiomas Coleção 11 e códigos IBGE de vegetação.
7. Inventários: buscar dados abertos e armazenar em pasta de referência.
8. Dúvidas não respondidas: seguir o padrão dos docs/ADRs.

### O que foi feito

- Download da legenda oficial Coleção 11 (PDF + texto extraído).
- Download do Painel de Biomassa e Carbono do SFB (IFN): `biomassa.csv` (53 MB, 439.970
  registros), `equacoes.csv`, `metadados.pdf`.
- Download dos suplementos S3–S5 do artigo de Cerrado (PLOS ONE 2018, DOI
  10.1371/journal.pone.0196742).
- Criação de `data/reference/inventarios_abertos.md` e `.csv` (10 fontes catalogadas).
- Ferramenta `tools/suggest_pilots_from_ifn.py`: cruza adensamento do IFN com fração de classes
  3/4 do MapBiomas.
- Seleção dos pilotos:
  - Amazônia: lon −60,45, lat −6,90; 512 px; 93,3% classe 3; 511 UAs do IFN na célula.
  - Cerrado: lon −47,70, lat −13,95; 512 px; 79,1% classes 3+4 (25,6% + 53,6%); 605 UAs.
- Scaffolding: `pyproject.toml`, `src/biomass_model/grid.py`, `tests/test_grid.py` (5 testes
  passando), `tools/select_pilots.py`.

### Achados

- O painel do SFB é aberto e tem coordenadas (~0,1°) e AGB por unidade amostral — serve para
  validação regional, não para pareamento pixel a pixel.
- Estatísticas calculadas por nós no CSV do SFB: Amazônia 151,6 Mg ha⁻¹ (média) / 112,0
  (mediana); Cerrado 33,9 / 19,4. A diferença média–mediana mostra distribuição assimétrica;
  não usar a média como "valor do bioma".
- O cluster do IFN em −60,45/−6,90 tem alta fração de floresta e muitas UAs; é melhor piloto
  amazônico do que Belterra, que não tinha UA do IFN em 50 km.
- A legenda confirma 3 = Formação Florestal e 4 = Formação Savânica; a distribuição empírica
  confirma (3 domina a Amazônia; 4 domina o Cerrado).

### Pendências geradas

- Baixar (ou obter via login gratuito) os inventários INV03–INV10.
- Harmonizar equações e DAP mínimo antes de qualquer validação.
- Definir o recorte temporal do piloto (ex.: 2018–2025) e a referência GEDI correspondente.
- Confirmar licença exata do MapBiomas e decidir licença dos produtos.

### Próximo passo

Fase 1: montar o cubo de features (S2, S1, DEM, clima) e extrair GEDI L4A nos dois tiles,
com validação espacial por blocos desde o início.

## 2026-11-17 — Sessão 2

### Credenciais e acessos

- CDS API configurada em `~/.cdsapirc`; teste de ERA5-Land mensal (2018–2025) **bem-sucedido**.
- Descoberta importante: Sentinel-2 L2A é acessível **sem conta** via `earth-search` STAC +
  COGs públicos na AWS. Testado nos dois pilotos.
- Copernicus DEM GLO-30 também é público na AWS (`copernicus-dem-30m`), sem conta.
- Pendente: token Earthdata (GEDI via LP DAAC; Sentinel-1 RTC via ASF) e autorização das
  aplicações no perfil Earthdata.

### Ferramentas novas

- `tools/fetch_s2_pilot.py` — janela de 1600 px (16 km a 10 m), 6 bandas + NDVI/NDMI/NIRv + SCL.
- `tools/fetch_dem_pilot.py` — mosaico GLO-30 recortado.
- `tools/fetch_era5_land.py` — médias mensais de 8 variáveis.

### Artefatos gerados (fora do git, em `E:\Mapbiomas\biomass\pilots\`)

- `amazonia_s2_2024.tif` (50,9 MB; cena 20240720, 0% nuvem; NDVI mediano 0,86).
- `cerrado_s2_2024.tif` (54,4 MB; cena 20240819, 0% nuvem; 97,9% válido).
- `amazonia_dem30.tif` e `cerrado_dem30.tif` (576×576; ~26–175 m e 0–1525 m).
- `amazonia_era5land_2018_2025.nc` (105 kB; 8 variáveis mensais).

### Observações técnicas

- A janela S2 precisa ser calculada em coordenadas UTM (o tile é EPSG:32720/32723), não em
  lat/lon; o erro inicial foi corrigido com `pyproj`.
- A cena de 2024 é um instantâneo; o produto final deve usar composições sazonais (mediana e
  percentis), não uma única data.
- O DEM do Cerrado tem 0,17% de zeros na costura entre tiles (tratados como nodata).

### Próximo passo

Obter token Earthdata, validar acesso a GEDI L4A e Sentinel-1 RTC; em paralelo, implementar
composição sazonal S2 e o alinhamento à grade comum de 30 m.
## 2026-11-17 — Sessão 3

### Refatoração para o pacote

- A aquisição deixou de ser script solto: src/biomass_model/datasets/{s2,dem,era5,gedi}.py, com
  credentials.py, manifest.py, catalog.py e cli.py; comandos python -m biomass_model.cli.
- 	ools/fetch_s2_pilot.py, 	ools/fetch_dem_pilot.py e 	ools/fetch_era5_land.py removidos.
- Todo download grava manifesto com parâmetros, URLs, hashes, licença e conta em
  data/manifests/; documentação em docs/32.
- ADRs novos: 0012 (filtro GEDI), 0013 (grade e amostragem), 0014 (escala do piloto, ±0,08°).

### GEDI L4A: extração validada

- Busca por CMR e leitura HDF5 via driver GDAL (asterio), sem h5py (não compila no Python
  3.15).
- Extração nos 6 grânulos de teste do piloto amazônico: 3.361 footprints válidos; AGB mediana
  192,6 Mg ha⁻¹; 69% com degrade_flag == 0. Grânulos noturnos de 2021 e 2022 não têm predição
  válida no bbox (0 footprints), como já indicado na sondagem.
- Filtro adotado: l2==1 & l4==1 & agbd>=0 & 0,9<=sensitivity<=1,01; degrade_flag é mantido
  como covariável e há sensibilidade restrita (ADR-0012).

### Próximo passo

- Rodar a extração GEDI em lote nos dois pilotos, montar o stack de features na grade de 30 m e a
  tabela de treino; baseline com CV por blocos espaciais.
### Extração GEDI em lote (2019–2024, V2.1)

| Piloto | Footprints | Mediana AGB | % < 10 Mg ha⁻¹ | % degrade 0 |
|---|---|---|---|---|
| Amazônia | 22.244 | 186,7 Mg ha⁻¹ | 0,9% | 80,7% |
| Cerrado | 16.851 | 6,2 Mg ha⁻¹ | 59,6% | 80,1% |

- Amazônia: distribuição plausível (p05 45,6; p95 360,1); 2022 tem mediana baixa (110,1), a
  investigar (composição de órbitas/estação); 2019 tem só 41,8% de degrade_zero.
- Cerrado: **achado importante** — L4A subestima fortemente a savana aberta. Contra a mediana de
  19,4 Mg ha⁻¹ do IFN, o viés é grande e não é de filtro. Decisão: campo como referência primária
  no Cerrado (ADR-0015); L4A apenas auxiliar.
- Valores extremos (até ~2.600 Mg ha⁻¹) existem e serão vistos no controle de qualidade do treino.
- Saídas: E:\Mapbiomas\biomass\gedi\{amazonia,cerrado}_l4a_v21_2019_2024.csv; resumo versionado em
  data/reference/gedi_pilotos_resumo.csv; manifestos em data/manifests/.
### Features e baseline inicial (Amazônia)

- Tabela de treino construída em E:\Mapbiomas\biomass\derived\amazonia_training.csv: 19.879
  footprints dentro do domínio (todos classe 3), 25 features (9 bandas/índices S2, 13 de clima,
  elevação/declividade/aspecto), sem NA após filtro.
- Cerrado: 14.420 footprints no domínio (7.821 classe 4, 6.599 classe 3), 762 com NA de feature
  (borda da cena S2). Usado só para diagnóstico — não é alvo de treino (ADR-0015).
- Baseline RandomForest (400 árvores, CV por 25 blocos de ~5 km): **R² 0,097; RMSE 92,4;
  MAE 70,2; viés +1,6 Mg ha⁻¹** (n = 19.869). Métricas em data/reference/baselines.csv.
- Interpretação: dentro de um piloto de floresta densa e uniforme, uma data S2 satura e quase não
  explica a variação do L4A (correlações |r| < 0,05); elevação/declividade dominam a importância,
  provavelmente como proxy de estrutura/artefato, não de biomassa. É um piso honesto, não um
  resultado final.
- Próximos ganhos esperados: composições sazonais multi-ano, S1 (estrutura), textura e GLCM,
  harmonização temporal com o ano do footprint, e filtro de borda/sombra.
### Composição S2 e efeito de escala

- Adicionado s2-composite (mediana de 10 datas 2019–2024, máscara SCL). Resultado no footprint:
  R² 0,094 / RMSE 92,5 — **sem ganho** sobre uma data (R² 0,097). Conclusão: nuvem não era o
  gargalo; ruído do L4A e homogeneidade do piloto dominam.
- Agregação em células de 1 km (≥3 footprints; 327 células): **R² 0,285 / RMSE 34,3 / MAE 26,3**
  com viés +1,6; folds entre 0,10 e 0,31. O erro absoluto cai ~60% ao agregar, como esperado por
  reduzir ruído de referência e variância local — mas a variância do alvo também diminui; não é
  ganho "de graça".
- Implicação prática: o produto é mais defensável em 1 km (ou agregado por bloco) do que em 30 m,
  coerente com ADR-0013. A meta de 30 m deve ser apresentada como camada diagnóstica, não como
  promessa de acurácia.
- Artefatos: data/reference/baselines.csv (3 linhas), .metrics.json/.joblib em
  E:\Mapbiomas\biomass\derived\.
### Cerrado: referência de campo (PLOS 2018)

- S3 do artigo (DOI 10.1371/journal.pone.0196742) tem 77 sítios com coordenadas de 6 casas e AGB
  (4,8–50,2; mediana 20,8 Mg ha⁻¹); 75 caem no bioma Cerrado (2 fora: Amazônia e Caatinga).
- Coleta de janelas S2 2024 (4 km, cena menos nublada de mai–out) e DEM para os 75 sítios; ERA5-Land
  regional (2019–2024) em um único arquivo de 32 MB.
- **Achado de escopo:** só 45 dos 75 sítios caem em classes 3/4 do MapBiomas 2024; 30 estão em
  formações campestres/uso antrópico excluídas pelo domínio (ADR-0010). O filtro de domínio custa
  40% dos sítios de campo do Cerrado — registrar como limitação (RC12), não como erro.
- Baseline de campo (45 sítios, features de 1 km, blocos de 1°): **R² 0,328; RMSE 8,34; MAE 6,53
  Mg ha⁻¹**; 2 dos 5 folds negativos. Temperatura média domina a importância (gradiente
  climático), seguida de elevação. Com n=45, o resultado é indicativo, não conclusivo.
- Próximos passos: ampliar sítios de campo (INV03–INV10, RAINFOR), harmonizar data do inventário
  com a cena, e avaliar exclusão/estrato separado para formações campestres.

### Sentinel-1 RTC: acesso e ganho
- Descoberta de rota sem conta: colecao sentinel-1-rtc no STAC do Microsoft Planetary Computer
  (COGs assinados por planetary-computer). O plano original de ASF exigia Earthdata + app
  autorizada e nao era necessario.
- datasets/s1.py + comando s1: 8 datas (mai-out/2024), orbita descendente, mediana em potencia
  linear; bandas v_db, h_db, h_vv_db, 
vi, 
obs em 10 m.
- Efeito no baseline amazonico: footprint R2 0,094 -> **0,098** (RMSE 92,5 -> 92,3); 1 km
  R2 0,286 -> **0,289** (RMSE 34,3 -> 34,2). Ganho marginal, coerente com piloto homogeneo e com
  o ruido do L4A; S1 fica como feature opcional. Estatisticas temporais e coerencia ficam para
  quando houver serie maior.
- Decisao Q6 registrada: adotar limites da literatura (vies <=10%; RMSE <=30% Amazonia /
  <=40% Cerrado; IC90 80-95%), citando Avitabile 2016, Santoro 2021 e Duncanson 2022.

### Referência de campo: alinhamento temporal com Landsat
- O PLOS 2018 tem inventários de 1988-2014; a validação anterior usava S2 de 2024, seis a
  trinta anos depois — inválida para checar pixel. Corrigido com Landsat C2 L2 via MPC
  (`datasets/landsat.py`), mediana de cenas em ±45 dias da data do inventário.
- 50 sítios com janela Landsat (2004-2014), 42 no domínio 3/4 no ano do inventário
  (36 classe 4, 6 classe 3). Baseline: **R² 0,288 / RMSE 8,89 / viés +0,27** (42 sítios).
- O resultado anterior "melhor" (R² 0,328 com S2 de 2024) era artefato do descasamento
  temporal; agora o número é defensável. Clima continua sendo a variável dominante.

### Expansão multi-região e generalização (ADR-0016)
- Adicionados dois boxes por bioma, além do original: Amazônia leste (Tapajós, mediana 146),
  Amazônia oeste (Acre, 175), Cerrado nordeste (MG, 7,6) e Cerrado oeste (MT, 83, classe 3).
  Cada box ~17,8 km; GEDI 2020-2024; S2 composto 2020-2024; DEM/ERA5 próprios.
- Validação leave-one-box-out (3 boxes/bioma): footprint R² **−0,18** (Amazônia) e **−0,56**
  (Cerrado); 1 km R² −0,13 e +0,42 agregado, mas folds de 0,13/−0,25/−0,81 no Cerrado.
- Interpretação: o R² intra-box (0,10-0,29) era sobretudo autocorrelação espacial; entre
  regiões o modelo não transfere. O R² agregado de 1 km é enganoso porque captura a diferença
  de média entre boxes, não habilidade local.
- Decisão: validação principal passa a ser por região; produto nacional fica fora de questão
  sem mais sítios, calibração regional e referência de melhor qualidade.
- Artefatos: `amazonia_multi_training.csv` (40.598), `cerrado_multi_training.csv` (31.402),
  `.metrics.json/.predictions.csv` em `E:\Mapbiomas\biomass\derived\*_multi3_loo_*`.

### Teste de transformacao logaritmica do alvo
- Implementado `log_target` em `run_baseline` (RF em log1p, predicao com expm1 e piso 0).
- Resultado no leave-one-box-out: Amazonia piorou muito (R² −1,00 no footprint, vies −101
  Mg/ha) e Cerrado melhorou no footprint (−0,07 vs −0,56), mas piorou em 1 km (0,07; fold oeste
  −4,3). Nao adotado; fica disponivel como opcao.
- Licao: o problema nao e so escala do alvo, e transferencia entre regioes (paisagem e
  referencia). Reforca a necessidade de mais sitios e calibracao regional.
