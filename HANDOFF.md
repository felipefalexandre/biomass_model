# HANDOFF — estado do projeto e como retomar

**Atualizado:** 2026-11-24 - **Ultimo commit:** consulte git log -1 - **Branch:** main
**Repo:** https://github.com/felipefalexandre/biomass_model · **Clone local:** ajuste ao seu caminho
**Testes:** `python -m pytest` → 60 passed.

Leia este arquivo antes de qualquer ação. Ele resume o que foi feito, onde estão os dados, o
que está validado e qual é o próximo passo. Não reinicie o projeto nem sobrescreva resultados.

> **Atualização 2026-11-24 — revisão de escopo e reimplementação:** auditoria de aderência em
> [`docs/46_auditoria_aderencia_escopo.md`](docs/46_auditoria_aderencia_escopo.md). Decisões
> aprovadas: campo é referência primária (ADR-0027); produto por polígono é de primeira classe
> (ADR-0028); fitofisionomia IBGE (ADR-0029); 30 m oficial e 1 km experimental (ADR-0030); foco em
> AGB e inventários 2000+ (ADR-0031); ingestão canônica (ADR-0032). O estado anterior é **baseline
> A0 experimental**, não produto de AGB real. Foram adicionados `inventory/`, `allometry/`,
> `stratification/` e `aggregation/`, além dos comandos `inventory` e `polygon`. As recomendações
> antigas de expandir mapas/features ficam subordinadas à base observacional e à validação.

---

## 1. Objetivo atual (escopo fechado)

- **Produto:** mapa raster anual de **AGB (Mg ha⁻¹) por pixel**, a partir de dados abertos do
  próprio ano. O usuário soma/poligoniza depois; **não** é produto separado.
- **GEDI:** usado apenas como referência de calibração/avaliação. **Nunca** como feature/prior no
  inference (ADR-0022).
- **Desmatamento/reflorestamento:** **fora do escopo**. Mapas/modelos de atividade são externos;
  a biomassa é insumo. Não estimar, prever ou detectar desmatamento (ADR-0021 revisado).
- **MRV:** requisitos **do produto de biomassa** são obrigatórios (G0–G7 em `docs/44`):
  escopo, proveniência, validação, incerteza, estratificação, reprodutibilidade, QA/QC, auditoria.
  Atividade, adicionalidade, leakage e permanência continuam externas.
- **Escala:** 30 m oficial; 1 km experimental/diagnóstico (ADR-0030, 2026-11-24). Classes 3/4 do MapBiomas são
  filtro espacial; fitofisionomia é camada separada (ADR-0025).
- **Classes 2 (campestre) e 6 (floresta alagável):** fora do domínio atual; decisão pendente.

---

## 2. Ambiente

- Python: `C:\Python315\python.exe` (3.15). Executar com `$env:PYTHONPATH="src"` no repo.
- Libs: rasterio, geopandas, numpy, pandas, scikit-learn, scipy, pyproj, netCDF4, pystac-client,
  planetary-computer, cdsapi, earthaccess. `h5py` **não** instala (GEDI é lido via rasterio HDF5).
- Credenciais (fora do repo; **não** imprimir):
  - CDS: `C:\Users\Felipe\.cdsapirc` (funciona).
  - Earthdata: `C:\Users\Felipe\.config\biomass_model\earthdata_token` (funciona).
- Dados: `E:\Mapbiomas\biomass` (~800 GB livres). Insumos: `E:\Mapbiomas\mapbiomas_col11_2004..2025.tif`,
  `E:\Mapbiomas\Biomas_250mil\lm_bioma_250.shp`.

Estrutura de dados:
```
E:\Mapbiomas\biomass\
  gedi\                 CSVs de footprints + HDF5
  pilots\               composites S2/S1/DEM/ERA5 dos boxes
  pilots\annual\        S2 anual + fenologia (2019-2022 para 2 boxes)
  derived\              tabelas, modelos .joblib, métricas, predições
  derived\maps\         GeoTIFFs do produto por pixel
  fields\plos2018\      janelas S2/DEM/Landsat dos sítios PLOS
  fields\ornl_brazil\   CSVs/KMZ do ORNL
  era5\                 ERA5 regional
```

---

## 3. Código e comandos

Módulos principais:
- `src/biomass_model/datasets/`: `s2` (inclui `fetch_annual`), `s1`, `landsat`, `dem`, `era5`,
  `sites`, `gedi`, `ornl`.
- `src/biomass_model/features.py`: tabelas de treino/campo, histórico MapBiomas, features.
- `src/biomass_model/modeling.py`: `run_baseline`, `run_region_cv` (calibração),
  `run_region_conformal`, `run_region_aoa`, `run_region_residual_calibration`.
- `src/biomass_model/polygon.py`: estatística por polígono (QA opcional).
- `src/biomass_model/mrv.py`: `mrv-check` (G3/G4/G6 automáticos).
- `src/biomass_model/inference/map.py`: `predict_map` (1 km), `predict_map_30m` (30 m + AOA/IC),
  `add_intervals`.
- `src/biomass_model/cli.py`: todos os subcomandos.

Comandos úteis:
```powershell
$env:PYTHONPATH="src"; python -m pytest
python -m biomass_model.cli list
python -m biomass_model.cli annual-map --help
python -m biomass_model.cli s2-annual --lon -47.70 --lat -13.95 --year 2021 --out <tif>
python -m biomass_model.cli annual-map --model <joblib> --s2 <tif> --dem <tif> --era5 <nc> `
  --mapbiomas-dir E:\Mapbiomas --year 2021 --resolution 30 `
  --training-csv <csv> --residuals <pred.csv> --out <tif>
python -m biomass_model.cli mrv-check --csv <pred.csv> --out <json>
```

---

## 4. Dados de treino/referência (estado atual)

11 boxes (~17,8 km), GEDI L4A V2.1 2019–2024:
- Amazônia (5): central, leste (Tapajós), oeste (Acre), norte (Manaus), sul (PA/MT) — 86.135
  footprints no domínio.
- Cerrado (6): central, nordeste (MG), oeste (MT), sul (SP), noroeste (BA), floresta (MT) —
  72.426 footprints.

Features: S2 (compósito anual ou multi-ano) + S1 opcional + DEM + ERA5 + histórico MapBiomas
2004–2018 (9 features). Treino em 1 km: média das features/alvo dos footprints (≥3).

Tabelas prontas em `E:\Mapbiomas\biomass\derived\`:
- `amazonia_multi5_hist_training.csv`, `cerrado_multi6_hist_training.csv` (com histórico).
- `e1_<bioma>_annual_merged.csv` (features anuais 2019–2022, 2 boxes) e `e1_<bioma>_static_merged.csv`.
- `e1_<box>_<ano>_annual.csv` / `_static.csv` (por box/ano).
- Modelo do protótipo: `e1_cerrado_central_annual_model.joblib` (RF, 40 features, treinado
  2019–2022 do box central).

---

## 5. Resultados-chave (não reinterpretar como validação de campo)

- Baseline estático (1 km, dentro do box): Amazônia R² 0,285; Cerrado ~0,29; S1/S2 composto não
  melhoram.
- Leave-one-box-out (LOO): sem transferência; com histórico: Amazônia 1 km R² 0,083; Cerrado
  footprint −0,017, 1 km 0,290 (agregado enganoso; folds ruins).
- Calibração local 10% (retreinar): Amazônia 0,393 (5 boxes); Cerrado 0,727 (6 boxes).
- Conformal: cobertura IC90 ~0,89; larguras 119 (Amazônia) e 58 (Cerrado) Mg ha⁻¹.
- AOA: 1 km 86% (Amazônia) / 84% (Cerrado); 30 m no box central 87,5% dos válidos.
- E1 (S2 anual vs compósito): neutro/negativo; não promovido (`docs/42`).
- E2a (pares GEDI): ruído domina; não valida mudança (`docs/43`).
- PLOS 2018: 42 sítios no domínio; R² 0,288 / RMSE 8,9 com Landsat na data.
- ORNL: fator 10 confirmado (`w=DBH/10`); densidades: JAM_A01 254,7; JAM_A02 308,3;
  TAP_A01 329,8/323,0/321,4 Mg ha⁻¹; coordenadas em `data/reference/ornl_sites_coords.csv`.
- Mapa 30 m (Cerrado central 2021): 284.089 pixels, 225.414 válidos, média 21,3, IC90 ±53,3,
  AOA 87,5% (dentro 19,7; fora 32,6). 1 km: 256 células, média 15,9 (sem calibração).

Tabelas versionadas: `data/reference/baselines.csv`, `matriz_boxes.csv`,
`plos2018_auditoria.csv`, `ornl_agb_sites.csv`, `ornl_sites_coords.csv`,
`fitofisionomias_crosswalk.csv`, `polygon_feasibility.csv`.

---

## 6. Decisões registradas (ADRs)

- 0012 filtro GEDI; 0013 grade; 0014 escala; 0015 campo no Cerrado; 0016 LOO entre regiões;
  0017 calibração local; 0018 histórico MapBiomas; 0019 AOA; **0020** duas linhas + temporal;
  **0021** produto anual de biomassa (sem modelar desmatamento); **0022** GEDI só calibração;
  **0023** taxonomia fitofisionômica; **0024** critérios de aceite; **0025** domínio 3/4 é
  filtro, fitofisionomia é estrato; **0026** produto é mapa por pixel (soma do usuário).

Docs-chave: `docs/35` auditoria, `36` base científica, `37` plano, `38` validação/incerteza,
`39` arquitetura, `40` síntese, `41` mapa vs estrato, `42` E1, `43` estabilidade, `44` MRV/REDD+,
`45` protótipo do mapa.

---

## 7. O que está pronto vs. o que falta

> **Nota:** esta seção é o plano de 2026-11-18. A prioridade atual está na seção 10
> (reimplementação 2026-11-24: campo, inventários, fitofisionomia, validação).

**Pronto:**
- Aquisição e tabelas dos 11 boxes; histórico; validação LOO; calibração local; conformal; AOA;
  mapa 1 km e 30 m (protótipo) com IC/AOA; ORNL recuperado (3 sítios); PLOS validado; MRV-check.

**Falta (em ordem):**
1. **Features anuais para todos os boxes e anos** (hoje só 2 boxes, 2019–2022). Incluir 2023/2024
   e eventualmente S1 anual.
2. **Mapas 30 m/1 km para todos os boxes/anos**; rodar `annual-map` com `--training-csv` e
   `--residuals`; conferir AOA/IC.
3. **Calibração local por região** e retreino; curvas de aprendizado (5–200 células).
4. **Validação de campo (G2):**
   - PLOS: comparar predições (Landsat/S2 do ano) nos 42 sítios; reservar 1/3 por bloco espacial.
   - ORNL: aplicar a todos os sítios (readmes para comprimento de transecto; palmeiras/lianas
     com alometria própria); parear com Landsat/S2/GEDI do ano; gerar tabela de validação.
5. **Fechar G0–G7** e model card por versão anual; `mrv-check` em cada produto.
6. Decidir classes 2/6; manter 1 km oficial/30 m diagnóstico até evidência contrária.

---

## 8. Pegadinhas e correções já feitas

- `aggregate_cells` agora agrupa por **célula e ano** (antes colapsava anos).
- S2 é 10 m: para 1 km usar `--block 100`; para 30 m usar `--resolution 30`.
- `predict_map` reamostra S2 para a grade alvo; AOA/IC são opcionais e via CSV.
- PowerShell: evitar heredocs/backticks; preferir scripts .py via write tool; `Set-Content`
  gera BOM (usar UTF8Encoding($false)); console mostra mojibake mas bytes UTF-8 estão certos.
- GEDI: `agbd_se`/PI existem mas não são usados como peso/incerteza (gap).
- Modelo de mapa atual foi treinado em features de footprints; há descasamento de suporte com
  médias de 1 km/30 m — documentar e testar.
- Não usar GEDI no inference; não usar mapas de AGB de terceiros.

---

## 9. Como retomar em 5 minutos

> **Nota:** o passo 5 abaixo é o plano anterior. Use a seção 10 para a prioridade vigente.

1. `cd C:\Users\Felipe\Documents\biomass_model` e `git pull`.
2. `$env:PYTHONPATH="src"; python -m pytest` (deve dar 30 passed).
3. Ler este arquivo + `docs/37`, `docs/44`, `docs/45`.
4. Conferir dados em `E:\Mapbiomas\biomass` e credenciais.
5. Próximo passo recomendado: expandir features anuais para todos os boxes/anos (item 7.1) e
   rodar mapas com AOA/IC (7.2); em paralelo, validação PLOS/ORNL (7.4).

**Nada foi commitado com credenciais.** Último estado: árvore limpa, `main` sincronizado.

---

## 10. Reimplementação 2026-11-24 — estado atual

### 10.1 Código novo

- `inventory/`: esquema canônico, adaptadores PLOS/IFN/ORNL/CEDA/GEDI, validação e store
  idempotente.
- `inventory/store.py`: `E:\Mapbiomas\biomass\inventory_store` com lock e manifesto.
- `observation_features.py`: features Landsat/S2, DEM, ERA5 e histórico MapBiomas.
- `training/field.py` e `training/inference.py`: RF campo-first, blocos+buffer, IC conformal,
  AOA e baseline por estrato.
- `validation/spatial.py`: blocos espaciais com buffer.
- `uncertainty/conformal.py`: cross-conformal por fold.
- `applicability/aoa.py`: AOA e distância ao treino.
- `model_registry/`: registro e champion/challenger.
- `stratification/`: crosswalk, rasterização, amostragem pontual e reconciliação IBGE–MapBiomas.
- `aggregation/polygon.py`: Produto C com geometria real, área de interseção, IC, AOA e
  fitofisionomia.
- `datasets/ibge.py`, `datasets/ceda.py`, `datasets/ornl.py`: aquisição e coordenadas.

### 10.2 Dados canônicos

Store: `E:\Mapbiomas\biomass\inventory_store\observations.csv` → **7.576 observações**:

| Fonte | Linhas |
|---|---:|
| IFN/SFB | 7.466 |
| PLOS 2018 | 77 |
| CEDA Manaus 2014 | 23 |
| ORNL SLB | 10 |

- ORNL: **25 sítios geolocalizados** a partir de 30 zips de transectos; os 10 sítios-ano com AGB
  têm geometria. `data/reference/ornl_sites_coords.csv`.
- CEDA: 23 parcelas 100×60 m, OGL.
- IBGE 1:250k 2026 baixado em `E:\Mapbiomas\ibge\versao_2026`.
- Fitofisionomia `legenda_2` rasterizada para os boxes centrais 2021 (Amazônia e Cerrado).

### 10.3 Resultados principais

- **F0 PLOS 2018 (Cerrado)** — bloco 200 km/buffer 25 km: n=16, R²=0,262, RMSE=10,81,
  viés=−3,59; baseline R²=−0,130; IC90 cobertura 0,813.
- **Sensibilidade LOO 100 km**: n=40, R²=0,197, RMSE=9,54; cobertura 0,900.
- **Fitofisionomia IBGE como feature**: sem ganho consistente; H1 não suportada (`docs/48`).
- **Validação CEDA Manaus 2014** (`docs/51`): F0 Cerrado aplicado à Amazônia; n=21,
  observado 132,3 vs predito 28,1; R²=−8,2; viés=−104,2; AOA 0/21.
- **Validação ORNL** (`docs/56`): n=10; observado 209,9 vs predito 29,0; R²=−1,52;
  RMSE=233,7; viés=−180,9; AOA 0/10.
- **Produto C** (`docs/53`): polígono 5×5 km no mapa A0 30 m; 2.217,7 ha analisados,
  AGB média 14,02, total 31.089 Mg, AOA 84,1%. Com filtro de grupos vegetacionais:
  1.348,6 ha, AGB 15,43, total 20.805 Mg, AOA 90,2%.
- **Reconciliação IBGE–MapBiomas** (`docs/54`): no Cerrado central 2021, 20.287,53 ha em 3/4;
  87,73% savanna e 12,27% pastagem IBGE. Correspondência não é direta.

### 10.4 Infra e governança

- Model registry: `E:\Mapbiomas\biomass\model_registry`; F0 block200 e LOO como
  **challengers**, nenhum champion.
- `docs/57_setup_nova_maquina.md`: instalação, credenciais, dados, reconstrução e testes do zero.
- Testes: `python -m pytest` → **84 passed** (2026-11-27).
- Nenhuma credencial ou dado bruto foi commitado.

### 10.5 Próximos passos

1. Modelo amazônico com CEDA + ORNL e validação leave-one-source/region-out.
2. Buscar mais inventários amazônicos independentes (RAINFOR, novos campos).
3. Alinhar features Landsat/S2 antes de gerar mapa 30 m campo-first.
4. Definir regra explícita de elegibilidade fitofisionômica.
5. Completar validação temporal e portões G0–G7; nada é MRV ainda.

---

## 11. Target consolidado e catálogo de features (2026-11-27)

**Decisão de arquitetura:** `ADR/0034` — evolução incremental, sem reestruturação integral
(princípio já registrado em `docs/46` §8.1).

### 11.1 Código novo

- `src/biomass_model/targets.py`: consolida **1 linha por UA** (Tier A pixel 30 m tem
  precedência sobre Tier B célula ~1,1 km), com `agb_min/agb_mg_ha/agb_max`,
  `n_repeticoes`, suporte, flags e plausibilidade (≤500 Mg/ha). Exporta CSV, GeoPackage
  e manifesto com SHA-256.
- `src/biomass_model/feature_catalog.py`: valida `data/reference/features_biomassa.csv`,
  seleciona por grupo/prioridade, exclui sempre GEDI/LiDAR/ICESat-2/lon-lat e calcula
  `feature_set_hash` estável (ADR-0033).
- `src/biomass_model/target_observations.py`: converte o target em observações canônicas,
  amostra estratificada reproduzível e manifesto; comando `target-observations`.
- `tools/fetch_target_features.py`: baixa janelas S2/DEM por sítio, com fallback temporal
  e status durável.
- `tools/gca_index_overlap.py`: mede sobreposição do Global Canopy Atlas (INV12) com as
  pegadas IFN; GCA é validação estrutural, nunca feature (`docs/64`).
- CLI: `target-consolidate`, `features-catalog` e `target-observations`.
- Testes: `tests/test_targets.py`, `tests/test_feature_catalog.py`,
  `tests/test_target_observations.py` (16 novos).

### 11.2 Execução real

| Artefato | Conteúdo |
|---|---|
| `data/processed/target/target_uas.csv` | 1.184 UAs (96 A + 1.088 B), todos os biomas; SHA-256 `9bb951…` |
| `data/processed/target/target_uas_amazonia_cerrado.csv` | 824 UAs (36 A + 788 B); SHA-256 `349279…` |
| `data/processed/target/target_uas.gpkg` | pontos do target (EPSG:4326); SHA-256 `0ccec5…` |
| `features-catalog --max-priority 1` | 27 features; hash `205c859…` |

**Achado:** o Tier A no escopo é **36 UAs** (não 96); 60 pixels confirmados estão em
Caatinga/Mata Atlântica. O downscaling para 30 m depende de validação independente e AOA,
não de pseudo-réplicas. Detalhes e limitações: `docs/63`.

### 11.3 Próximos passos

1. Cubo de features no suporte do target (30 m e ~1,1 km), amostra de UAs, prioridade 1.
2. E3 (baseline por estrato vs RF) com blocos espaciais + buffer e curva de aprendizado.
3. E4 (ablação SAR/textura/fenologia) e E5 (dois estágios 1 km→30 m).
4. Ingestão de Maracá (dataset de biomassa `10.17632/2j354jtddx.2`) e RAINFOR (após área).

### 11.4 Global Canopy Atlas (2026-11-27)

- **INV12**, LiDAR aerotransportado (CHM 1 m); 3.458 aquisições, 56.554 km².
- Índice extraído sem baixar 2,6 GB: 1.240 aquisições no Brasil (9.181 km²).
- Sobreposição: **4 UAs do target** e **6 UAs IFN**; insuficiente para calibrar.
- Papel: validação estrutural/referência secundária; **nunca feature** (ADR-0022/0027).
- Avaliação completa: `docs/64`; ferramenta: `tools/gca_index_overlap.py`.

### 11.5 Piloto de features e E3 (2026-11-27)

- `target-observations`: 60 UAs Tier B; **58 usáveis** (2 sem S2 em ±2 anos).
- Features: S2 de uma data (6 bandas + 7 índices), terreno e histórico MapBiomas;
  **26 colunas**, hash `d85879e…`; S1, clima, solo e textura ficam para a próxima rodada.
- E3 (200 km/25 km): **R² 0,774, RMSE 42,6, viés −1,6** contra baseline
  R² 0,323/RMSE 73,8; n teste 18; cobertura IC90 0,78 (nominal 0,90).
- **Leitura:** o ganho é sobretudo entre biomas; R² within-bioma negativo. Sem a
  categórica de bioma, R² 0,721 e as features espectrais (NBR/NDII/NDMI/EVI) assumem.
- Limitações: S2 de uma data, suporte de 1 km, sem validação independente.
- Detalhes: `docs/65`; figura `docs/figuras/e3_piloto_58.png`.

