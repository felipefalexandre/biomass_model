# 00 — Resumo executivo

## 1. Problema

Estimar biomassa vegetal (AGB, BGB, total), carbono e CO₂e para Amazônia e Cerrado, de forma
defensável cientificamente, reprodutível e baseada apenas em **dados abertos** e **ferramentas
gratuitas**, com código em Python.

O problema não é "treinar um modelo". É responder a uma pergunta de **estimativa** com
**incerteza quantificada** e **rastreabilidade**, em um domínio onde:

- os dados de campo são escassos, enviesados e heterogêneos;
- os produtos globais de biomassa divergem entre si (por vezes por fatores > 2 em florestas
  tropicais);
- a estrutura da vegetação varia abruptamente entre floresta ombrófila, floresta estacional,
  savana, savana arborizada e campo;
- a autocorrelação espacial invalida a validação por k-fold aleatório;
- o Cerrado tem estrutura de biomassa baixa, esparsa e sensível a fogo, mal representada por
  modelos calibrados em florestas.

## 2. Decisão central

Adotar uma arquitetura em **duas camadas acopladas**:

1. **Camada de predição (mapa):** modelo(s) de aprendizado de máquina treinados em referências
   de AGBD (GEDI L4A e/ou parcelas de campo), com features ópticas (Sentinel-2, Landsat),
   radar (Sentinel-1), topografia (DEM) e clima. Produz um mapa de AGBD por pixel (30 m) e por
   domínio (bioma × classe de vegetação × ano).
2. **Camada de estimativa (inferência):** estimador de **inferência híbrida** — desenho
   amostral probabilístico para a parte observada (GEDI/parcelas) e modelo para a parte
   não observada — com variância combinando incerteza de amostragem e de modelo.

Essa separação evita o erro mais comum em trabalhos de biomassa: confundir a acurácia do mapa
(erro por pixel) com a incerteza da estimativa de área/total (erro de desenho amostral).

## 3. Decisões-chave desta fase

| # | Decisão | Justificativa | ADR |
|---|---|---|---|
| D1 | Python local com rasterio/GeoPandas/scikit-learn/XGBoost; sem dependência de GEE na trilha principal | Requisito de ferramentas gratuitas e reprodutibilidade offline; GEE registrado como alternativa/redflag | ADR-0001 |
| D2 | Dois modelos separados por bioma (Amazônia, Cerrado) | Estruturas e faixas de biomassa distintas; modelos globais degradam o Cerrado | ADR-0002 |
| D3 | GEDI L4A como referência principal, explicitamente tratado como **produto de modelo** | Cobertura espacial e amostral superior a parcelas; mas é dado derivado, com erro próprio | ADR-0003 |
| D4 | Inferência híbrida com variância de dois componentes | Reconhece que a referência é modelo e que a amostra é probabilística | ADR-0004 |
| D5 | BGB como modelo separado (solo, clima, estrutura); R:S apenas como linha de base | BGB não é observável por satélite e não deve ser derivada da AGB | ADR-0011 |
| D6 | Validação por blocos espaciais e leave-one-region-out | Evita otimismo por autocorrelação | ADR-0006 |
| D7 | Carbono e CO₂e em módulo separado, com fatores explícitos e versionados | Evita confusão de unidades | ADR-0007 |
| D8 | Domínio = classes brutas 3 e 4 do MapBiomas no ano-alvo | Escopo definido pelo usuário; máscara 2007–2016 é apenas estrato | ADR-0010 |
| D9 | Pilotos: sul do Amazonas e Chapada dos Veadeiros, escolhidos por cobertura do IFN | Garante biomassa de campo próxima para validação | `docs/17`, `docs/31` |

## 4. O que este planejamento **não** faz

- Não produz números de biomassa.
- Não propõe um modelo "final" antes da etapa de avaliação (`docs/25`).
- Não resolve as dependências externas (acesso a campo, decisões de escopo) listadas em `docs/30`.
- Não assume que GEDI, ICESat-2 ou produtos globais substituem validação independente.

## 5. Estado atual

- Planejamento documental: **concluído** (docs 00–32, catálogo, matriz, ADRs).
- Código: **em execução** — grade, aquisição no pacote (`datasets` + CLI + manifestos),
  tabela de treino e baseline; nenhum produto final.
- Dados: legenda MapBiomas, painel do SFB, suplementos do Cerrado, S2/DEM/ERA5 dos dois pilotos e
  GEDI L4A 2019–2024 **baixados e documentados** (`docs/32`).
- Pilotos: definidos para Amazônia e Cerrado (`docs/17`, `docs/31`), caixa de ~17 km (ADR-0014).
- Baseline Amazônia: R² 0,097 / RMSE 92,4 Mg ha⁻¹ com uma data S2 e CV espacial — piso honesto,
  não resultado final (`data/reference/baselines.csv`).
- Cerrado: L4A subestima savana aberta; campo passa a ser referência primária (ADR-0015).
- Pendências que bloqueiam a fase de execução: ver `docs/30`.

## 6. Critérios de sucesso (resumo)

1. Estimativas com **intervalo de confiança de 90%** por domínio e ano.
2. Viés relativo dentro de limites acordados (`docs/25`), medidos em validação espacial
   independente.
3. Reprodutibilidade: mesma versão de dados + mesmo código ⇒ mesmos artefatos (hash).
4. Rastreabilidade: cada número rastreável a um artefato versionado e a uma decisão registrada.
5. Transparência sobre limitações: redflags e incertezas documentadas no produto final.
