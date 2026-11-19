# Sistema de Estimativa de Biomassa Vegetal — Amazônia e Cerrado

**Status:** piloto concluído (5 boxes na Amazônia, 6 no Cerrado) com calibração local, AOA e IC conformal. Cerrado calibrado R² 0,73 / RMSE 22,8 (1 km); Amazônia 0,39 / 44,9. Não é produto nacional: exige calibração por região e validação de campo independente. Ver `docs/33` (relatório) e `docs/34` (model card).
**Escopo:** AGB (v1) e BGB (modelo separado), carbono e CO₂e, a partir de dados abertos e ferramentas gratuitas, em Python. O modelo estima biomassa/estoque; não estima desmatamento nem reflorestamento (atividade é externa).
**Domínio:** classes 3 (Formação Florestal) e 4 (Formação Savânica) do MapBiomas Coleção 11, Amazônia e Cerrado.
**Data de referência desta versão:** 2026-11-17
**Autor:** Felipe Alexandre (registro de trabalho)

---

## 1. O que é este repositório

Este repositório contém o **planejamento completo** de um sistema modular para estimar biomassa
vegetal acima e abaixo do solo nos biomas Amazônia e Cerrado, com rastreabilidade de decisões,
catálogo de dados, matriz de evidências, análise de incerteza, plano de validação e registro
explícito de restrições (redflags) e perguntas abertas.

Ele contém o **planejamento completo** de um sistema modular para estimar biomassa vegetal acima
e abaixo do solo nos biomas Amazônia e Cerrado, com rastreabilidade de decisões, catálogo de
dados, matriz de evidências, análise de incerteza, plano de validação e registro explícito de
restrições (redflags) e perguntas abertas.

O código começa pelo contrato de grade e pelas ferramentas de seleção de pilotos. Ainda **não há
modelo treinado nem mapa de biomassa**. Qualquer número aqui presente é: (a) proveniente de fontes
publicadas e citadas, ou (b) resultado de contagem simples sobre dados abertos baixados, sempre
identificado como tal.

## 2. Regras que governam este planejamento

1. **Nada de referências inventadas.** Toda referência citada tem identificador verificável
   (DOI/PII) ou está marcada como `[VERIFICAR]` na lista de pendências.
2. **Nada de resultados inventados.** Estimativas só entram após execução e validação.
3. **Não presumir que o modelo mais complexo é o melhor.** A escolha é feita por desempenho
   validado, custo e interpretabilidade (ver `docs/07` e `docs/25`).
4. **Não confundir** biomassa (Mg de matéria seca) com carbono (Mg C) nem com CO₂e (Mg CO₂e).
   As conversões estão isoladas em `docs/11`.
5. **Autocorrelação espacial** não é ignorada: validação, inferência e incerteza tratam
   dependência espacial explicitamente (`docs/12`, `docs/13`).
6. **BGB no Cerrado** não é tratado como subproduto automático da AGB: BGB é um modelo separado,
   com preditores de solo e clima (`docs/10`, ADR-0011).
7. **Somente dados abertos e ferramentas gratuitas** na trilha principal. Se algo só existir em
   versão paga, isso é registrado como **redflag** (`docs/22`), sem interromper o trabalho.
8. **Perguntas que dependem do usuário** são registradas, não respondidas por suposição
   (`docs/30`).

## 3. Índice dos documentos

| # | Documento | Conteúdo |
|---|---|---|
| 00 | [Resumo executivo](docs/00_resumo_executivo.md) | Visão geral, decisões-chave, estado |
| 01 | [Escopo e estimandos](docs/01_escopo_e_estimandos.md) | Definição formal do que é estimado |
| 02 | [Perguntas e hipóteses](docs/02_perguntas_e_hipoteses.md) | Perguntas de pesquisa e hipóteses testáveis |
| 03 | [Revisão metodológica](docs/03_revisao_metodologica.md) | Estado da arte, famílias de métodos |
| 04 | [Matriz de evidências](docs/04_matriz_de_evidencias.md) | Evidência → decisão, com força e limitações |
| 05 | [Catálogo de dados](docs/05_catalogo_de_dados.md) | Fontes, licenças, acesso, papel |
| 06 | [Avaliação de dados](docs/06_avaliacao_de_dados.md) | Qualidade, vieses, lacunas, compatibilização |
| 07 | [Arquitetura metodológica](docs/07_arquitetura_metodologica.md) | Desenho geral em camadas |
| 08 | [AGB na Amazônia](docs/08_modelagem_agb_amazonia.md) | Estratégia específica |
| 09 | [AGB no Cerrado](docs/09_modelagem_agb_cerrado.md) | Estratégia específica |
| 10 | [BGB e raízes](docs/10_bgb_e_raizes.md) | Abaixo do solo |
| 11 | [Carbono e CO₂e](docs/11_carbono_e_co2e.md) | Conversões e unidades |
| 12 | [Incerteza e inferência](docs/12_incerteza_e_inferencia.md) | Design-based, model-based, híbrida |
| 13 | [Validação e acurácia](docs/13_validacao_e_acuracia.md) | Protocolos, métricas, benchmarks |
| 14 | [Desenho amostral e campo](docs/14_desenho_amostral_e_campo.md) | Amostragem, parcelas, dados de campo |
| 15 | [Sensores e features](docs/15_sensores_e_features.md) | S1/S2/Landsat/SRTM/GEDI/clima |
| 16 | [Mudança temporal](docs/16_mudanca_temporal.md) | Série temporal, desmatamento, degradação |
| 17 | [Integração MapBiomas](docs/17_integracao_mapbiomas.md) | Estratificação e polígonos |
| 18 | [Pipeline](docs/18_pipeline_de_processamento.md) | Etapas, artefatos, contratos |
| 19 | [QA/QC e reprodutibilidade](docs/19_qa_qc_e_reprodutibilidade.md) | Controles e versionamento |
| 20 | [Computação e escala](docs/20_computacao_e_escalabilidade.md) | Requisitos, estratégia local/cloud |
| 21 | [Governança e licenças](docs/21_governanca_dados_e_licencas.md) | Uso, redistribuição, citação |
| 22 | [Redflags](docs/22_redflags_e_restricoes.md) | Restrições registradas |
| 23 | [Riscos e mitigação](docs/23_riscos_e_mitigacao.md) | Riscos técnicos e científicos |
| 24 | [Plano de implementação](docs/24_plano_de_implementacao_e_fases.md) | Fases, entregáveis, critérios de saída |
| 25 | [Plano de avaliação](docs/25_plano_de_avaliacao_e_benchmarks.md) | Experimentos e critérios de aceite |
| 26 | [ADRs](docs/26_registro_de_decisoes.md) | Registro de decisões de arquitetura |
| 27 | [Glossário](docs/27_glossario.md) | Termos e unidades |
| 28 | [Referências: status](docs/28_referencias_status.md) | O que foi verificado |
| 29 | [Bibliografia](docs/29_bibliografia.md) | Lista final citável |
| 30 | [Perguntas abertas](docs/30_perguntas_abertas.md) | Pendências para o usuário |
| 31 | [Diário de pesquisa](docs/31_diario_de_pesquisa.md) | Registro cronológico de decisões e achados |
| 32 | [Aquisição de dados](docs/32_aquisicao_de_dados.md) | Contas, comandos, saídas e manifestos |
| 33 | [Relatório do piloto](docs/33_relatorio_piloto.md) | Resultados consolidados e próximos passos |
| 34 | [Model card AGB](docs/34_model_card_agb.md) | Uso, métricas, limites e calibração |
| 35 | [Auditoria científica](docs/35_auditoria_cientifica.md) | Diagnóstico do sistema atual |
| 36 | [Base científica](docs/36_base_cientifica_e_fitofisionomias.md) | Literatura, taxonomia, representatividade |
| 37 | [Plano experimental anual](docs/37_plano_experimental_anual.md) | Estimativa anual, mudança, critérios |
| 38 | [Validação e incerteza](docs/38_validacao_independente_e_incerteza.md) | PLOS, ORNL, polígono |
| 39 | [Arquitetura e roadmap](docs/39_arquitetura_e_roadmap.md) | Módulos, fases, riscos |
| 40 | [Síntese para aprovação](docs/40_sintese_para_aprovacao.md) | Decisões solicitadas |
| 41 | [Produtos: mapa vs estrato](docs/41_produtos_mapa_vs_estrato.md) | Arquitetura de produto e viabilidade |
| 42 | [Resultados E1](docs/42_resultados_e1.md) | Features anuais vs compósito |
| 43 | [Estabilidade temporal](docs/43_resultado_mudanca_preliminar.md) | Pares anuais e ruído |
| 44 | [Requisitos REDD+/ARR](docs/44_requisitos_redd_arr.md) | O que o modelo entrega |
| 45 | [Protótipo do mapa anual](docs/45_prototipo_mapa_anual.md) | Mapa por pixel 1 km |

## 4. Estrutura do repositório

```
biomass_model/
├── src/biomass_model/     # pacote Python (grid, datasets, cli)
├── tests/                 # testes (pytest)
├── tools/                 # scripts de análise (seleção de pilotos)
├── docs/                  # planejamento 00–32
├── ADR/                   # decisões arquiteturais
├── data/
│   ├── catalogo_dados.csv
│   ├── matriz_evidencias.csv
│   ├── manifests/         # proveniência dos downloads (hash, licença, conta)
│   ├── reference/         # legenda, inventários catalogados, pilotos
│   └── raw/               # downloads volumosos (ignorado pelo git)
└── pyproject.toml
```

Comandos:

```powershell
python -m pip install -e ".[dev,data]"
python -m pytest
python -m biomass_model.cli list
python -m biomass_model.cli s2 --lon -60.45 --lat -6.9 --start 2024-07-01 --end 2024-09-30 --out E:\Mapbiomas\biomass\pilots\amazonia_s2_2024.tif
python -m biomass_model.cli dem --lon -60.45 --lat -6.9 --out E:\Mapbiomas\biomass\pilots\amazonia_dem30.tif
python -m biomass_model.cli era5 --lon -60.45 --lat -6.9 --start-year 2018 --end-year 2025 --out E:\Mapbiomas\biomass\pilots\amazonia_era5land_2018_2025.nc
python -m biomass_model.cli gedi --west -60.53 --south -6.98 --east -60.37 --north -6.82 --start 2019-01-01 --end 2024-12-31 --out E:\Mapbiomas\biomass\gedi\piloto_amazonia.csv --work-dir E:\Mapbiomas\biomass\gedi\h5
```

Detalhes de contas, comandos e manifestos em [`docs/32`](docs/32_aquisicao_de_dados.md).

## 5. Artefatos estruturados

- `data/catalogo_dados.csv` — catálogo legível por máquina das fontes de dados.
- `data/matriz_evidencias.csv` — evidência científica → decisão de projeto.
- `data/reference/inventarios_abertos.csv` — fontes de campo/inventário e status de acesso.
- `data/reference/pilotos_selecionados.csv` — tiles piloto escolhidos.
- `ADR/` — decisões arquiteturais em formato curto (contexto, decisão, consequências).

## 6. Contexto herdado da etapa anterior

A etapa anterior (concluída) produziu, em `E:\Mapbiomas\outputs_eligibilidade`:

- máscara de elegibilidade (pixels com classe 3/4 do MapBiomas em **todos** os anos 2007–2016);
- série anual de desmatamento 2014–2025 (com *warm-up* 2014–2015, uso recomendado a partir de 2016);
- área de estudo de 622.532.566,8 ha, dos quais 386.714.878,6 ha elegíveis (62,12%);
- Amazônia: 423.361.243,8 ha totais / 297.014.653,96 ha elegíveis;
- Cerrado: 199.171.323,0 ha totais / 89.700.224,66 ha elegíveis.

Esses produtos são reutilizados aqui apenas como **estrato opcional** e referência de comparação.
O domínio deste projeto é a classe 3/4 do MapBiomas **no ano-alvo** (ADR-0010), não a máscara
estável de 2007–2016.

## 7. Como ler este material

Comece por `00` (decisões), depois `01` (o que se quer estimar), `05`–`07` (dados e desenho),
`12`–`13` (incerteza e validação) e, por fim, `22`, `25`, `30` e `31` (restrições, critérios de
aceite, pendências e diário).
