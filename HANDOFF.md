# HANDOFF — estado do projeto e como retomar

**Atualizado:** 2026-11-24 · **Último commit:** `4427545` (reimplementação local não commitada) · **Branch:** `main`
**Repo:** `C:\Users\Felipe\Documents\biomass_model` · **Remote:** `github.com/felipefalexandre/biomass_model`
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

## 10. Reimplementação 2026-11-24

Implementado e testado (60 testes):

- `src/biomass_model/inventory/`: esquema canônico, validação, escrita CSV/Parquet/GeoPackage e
  adaptadores PLOS 2018, IFN/SFB, ORNL e GEDI L4A.
- `src/biomass_model/allometry/`: Chave 2005, palmeira e liana.
- `src/biomass_model/stratification/`: normalização, crosswalk IBGE–MapBiomas e rasterização de
  fitofisionomia.
- `src/biomass_model/aggregation/polygon.py`: Produto C com geometria, interseção real
  célula–polígono, média, mediana, estoque, IC por block bootstrap e tabela por classe/fitofisionomia.
- CLI: `inventory --source {plos2018,ifn,ornl,gedi}` e `polygon --input ... --raster ...`.
- ADRs 0027–0032 e atualização de README/HANDOFF.

Estado dos dados canônicos (2026-11-24):

- PLOS 2018: 77 sítios, validação sem erros.
- IFN/SFB: 439.970 registros → 7.466 UAs canônicas (Amazônia 1.937; Cerrado 2.537; demais biomas
  preservados no catálogo). Equação padrão `AGB_Chave`, com fallback sinalizado.
- ORNL: 10 sítios/sítio-ano recuperados; 7 sem geometria (UTM/KMZ a resolver).
- GEDI L4A: adaptador pronto; ainda não usado no treino novo.
- Tabela combinada: `E:\Mapbiomas\biomass\derived\observations_field.csv` (7.553 observações).
- IBGE vegetação 1:250.000 versão 2026 baixada em `E:\Mapbiomas\ibge\versao_2026` (vege_area.zip,
  371.806.036 bytes, sha256 `bcacc74011c86ba11ef4f4826bed38836340191208c9e98e821d52f0d68a5fb7`).
- Fitofisionomia rasterizada (`legenda_2`) para os boxes centrais 2021:
  `derived\fitofisionomia_amazonia_central_2021.tif` (3 classes; 67.041 água, 324.519 FOD aluvial,
  2.168.440 FOD submontana) e `derived\fitofisionomia_cerrado_central_2021.tif` (319.200 pastagem,
  1.800.418 savana arborizada, 440.382 savana parque). JSON com grupos e classe MapBiomas ao lado.
- `observation_features.py`: features Landsat/S2, DEM, ERA5 e histórico MapBiomas para a tabela
  canônica, sem vazamento temporal no histórico.
- `validation/spatial.py`: blocos espaciais com buffer para reduzir vazamento.
- `training/field.py`: RandomForest campo-first com validação por bloco+buffer, baseline e métricas.
- Baseline campo-first F0 (PLOS 2018, Cerrado, `docs/47`):
  - features: `derived\plos2018_features_landsat.csv` (77 sítios; 40 usados no domínio; 36 features).
  - validação primária 200 km/buffer 25 km: n=16, R²=0,262, RMSE=10,81, viés=−3,59;
    baseline R²=−0,130; IC90 cross-conformal cobertura 0,813, largura 33,8 Mg ha⁻¹.
  - sensibilidade 100 km/buffer 25 km: n=40, R²=0,197, RMSE=9,54, viés=+0,15;
    baseline R²=−0,063; IC90 cobertura 0,900, largura 28,5 Mg ha⁻¹.
  - artefatos: `derived\field_plos2018_rf_block200.*` e `derived\field_plos2018_rf.*`.
  - status: **não promovido**; amostra antiga/pequena, sem holdout independente e IC otimista
    no cenário de blocos.
- Fitofisionomia IBGE como feature (`docs/48`): amostragem pontual do IBGE 2026 `legenda_2`;
  40 sítios → 30 `savanna` e 10 `unknown` (pastagem/agricultura/água/contato), sem `forest`.
  Resultado: sem ganho consistente (bloco 200 km R² 0,256 vs 0,262; LOO R² 0,200 vs 0,197).
  Hipótese H1 não suportada; **não promover** a variável como feature. Artefatos:
  `derived\plos2018_features_landsat_ibge.csv`, `derived\field_plos2018_ibge_rf*`.
- Registro de modelos (`docs/49`, ADR-0033): `model-registry`/`model-list`/`model-compare`/
  `model-promote`; registro em `E:\Mapbiomas\biomass\model_registry`. F0 registrado como
  challenger, sem champion.

Próximos passos recomendados:

1. Processar IFN completo e ORNL completo; resolver coordenadas UTM/KMZ e duplicidades.
2. Obter IBGE 1:250k e gerar a camada de fitofisionomia para os boxes.
3. Migrar o treinamento para consumir a tabela canônica (campo como referência primária).
4. Gerar features anuais em 30 m e mapas com IC/AOA; 1 km apenas experimental.
5. Implementar validação espacial com buffer, temporal e por fitofisionomia.
6. Só depois promover modelo candidato e completar G0–G7.
