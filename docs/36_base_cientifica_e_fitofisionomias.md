# 36 — Base científica, fitofisionomias e representatividade

**Data:** 2026-11-18 · **Status:** investigação; nenhuma decisão de modelo tomada aqui.

## 1. Por que fitofisionomia importa para um modelo anual

Relações AGB–reflectância–estrutura mudam entre fisionomias: dossel fechado satura o óptico em
AGB alta; savana aberta tem resposta dominada por fração lenhosa e sombra; floresta estacional
tem sazonalidade distinta da ombrófila; formações secundárias têm AGB baixa e crescimento rápido.
Um único modelo global mistura essas relações. A hipótese desta etapa é que **estratificar por
fisionomia/estado sucessional** melhora transferência e resposta a mudanças — mas ela pode ser
rejeitada; o protocolo em `docs/37` testa isso contra o baseline.

## 2. Evidências verificadas (matriz)

Status “verificado” = DOI/volume conferidos em `docs/28` ou nesta auditoria; “a verificar” = DOI
de memória, **não citar** até conferência.

| Estudo | DOI | Achado relevante | Implicação |
|---|---|---|---|
| Chave et al. 2005, Oecologia | 10.1007/s00442-005-0100-x | Alometria pantropical com D, H, ρ | Base para AGB de árvores individuais no ORNL/PLOS |
| Chave et al. 2014, GCB | 10.1111/gcb.12629 | Alometria com estresse climático | Comparar com 2005; incerteza de equação |
| Chave et al. 2004, Phil. Trans. R. Soc. B | 10.1098/rstb.2003.1425 | Propagação de erros em AGB | Estrutura para incerteza de campo |
| Avitabile et al. 2016, GCB | 10.1111/gcb.13139 | Fusão de mapas; RMSE 15–21% menor; viés ~5 Mg/ha | Benchmarks e limites realistas |
| Santoro et al. 2021, ESSD | 10.5194/essd-13-3927-2021 | Mapa CCI 2010, 100 m | Comparação de distribuição, não verdade |
| Duncanson et al. 2022, RSE | 10.1016/j.rse.2021.112845 | Validação do L4A; erros por PFT/região | GEDI é referência com erro; não é verdade |
| Dubayah et al. 2023, GEDI L4B | 10.3334/ORNLDAAC/2299 | AGBD 1 km 2019–2023 + SE | Benchmark e checagem, **não** usar como prior no inference |
| Li et al. 2024, Sci. Remote Sens. | 10.1016/j.srs.2024.100161 | L4A subestima savana; modelos locais superam | Explica viés do Cerrado; justifica calibração local |
| Bullock et al. 2023, ERL | 10.1088/1748-9326/acdf03 | Inferência híbrida GEDI+NFI; L4A subestima | Método para combinar campo e GEDI |
| Hunter et al. 2013, Biogeosciences | 10.5194/bg-10-8385-2013 | Descreve o DDLS fator 10 do ORNL; área nominal ~0,6 ha | Chave para recuperar AGB/ha do ORNL |
| Goodman et al. 2014, Ecol. Appl. | 10.1890/13-0070.1 | Dimensões de copa melhoram AGB | Estrutura de copa como feature, se disponível |
| Ledo et al. 2016, Ecol. Appl. | 10.1002/eap.1450 | Erro composto em D–H e AGB | Incerteza alométrica |
| GEDI fuel load Cerrado (2022), RSE | 10.1016/j.rse.2021.112764 | GEDI no Cerrado para camadas de combustível | Uso de métricas estruturais no Cerrado |
| Roitman et al. 2018, PLOS ONE | 10.1371/journal.pone.0196742 | 77 sítios de campo no Cerrado | Única linha B atual |
| Ploton et al. 2020, Nat. Commun. | 10.1038/s41467-020-18321-y (a verificar) | Validação espacial revela baixo desempenho de mapas | Justifica LOO e desconfiança de R² alto |
| Meyer & Pebesma 2021, MEE | 10.1111/2041-210X.13650 (a verificar) | Área de aplicabilidade | Base do AOA já implementado |
| Roberts et al. 2017, Ecography | 10.1111/ecog.02881 (a verificar) | CV para dados espaciais/temporais | Base para CV anual e espacial |
| Poorter et al. 2015, Nature | 10.1038/nature16512 (a verificar) | Resiliência de florestas secundárias | Curvas de crescimento para regeneração |
| Spawn et al. 2020, Sci. Data | 10.1038/s41597-020-0444-4 (a verificar) | AGB/BGB global 1 km | BGB separado; benchmark |
| Mokany et al. 2006, GCB | 10.1111/j.1365-2486.2005.001043.x (a verificar) | Root:shoot por bioma | BGB futuro |
| Hengl et al. 2017, PLOS ONE | 10.1371/journal.pone.0169748 (a verificar) | SoilGrids 250 m | Covariável de solo |
| Saatchi et al. 2011, PNAS | 10.1073/pnas.1019576108 (a verificar) | Mapa pan-tropical | Benchmark histórico |
| Baccini et al. 2012, NCC | 10.1038/nclimate1354 (a verificar) | Mapa pantropical | Benchmark histórico |
| Araza et al. 2022, RSE | 10.1016/j.rse.2022.112917 (a verificar) | Estrutura de avaliação de mapas | Protocolo de acurácia/incerteza |

**Regra:** benchmark não é verdade. Divergência é resultado a explicar.

## 3. Taxonomia fitofisionômica proposta

Não assumir que classe de uso/cobertura = fitofisionomia. Proposta hierárquica, com
granularidade dependente da qualidade cartográfica e da amostra:

| Nível | Conteúdo | Fonte candidata | Uso |
|---|---|---|---|
| 0 | Bioma | IBGE/MapBiomas | Estrato obrigatório |
| 1 | Grupo de formação: florestal, savânica, campestre, úmida | IBGE Manual Técnico da Vegetação Brasileira (2ª ed., 2012) | Estrato de modelo |
| 2 | Fisionomia: ombrófila densa/aberta, estacional, campinarana, cerradão, cerrado s.s., campo cerrado/sujo/limpo, mata de galeria/ciliar | IBGE 1:250.000 + MapBiomas + literatura regional | Estrato ou feature categórica |
| 3 | Estrutura contínua: altura, cobertura, densidade, complexidade | S2/S1/Landsat (séries), **não GEDI no inference** | Covariável contínua |
| 4 | Estado sucessional/perturbação: idade secundária, fogo, corte | MapBiomas Vegetação Secundária, MapBiomas Fogo, PRODES | Feature temporal |
| 5 | Contexto: solo, clima, posição topográfica | SoilGrids, ERA5, DEM | Covariável estática |

**Limite explícito:** MapBiomas separa “Formação Florestal” (3) e “Formação Savânica” (4), mas não
separa campo limpo/sujo/cerrado s.s./cerradão. Para o Cerrado, a granularidade fina exigirá IBGE
1:250k e/ou classificação estrutural própria; não será inventada a partir de classes de uso.

## 4. Matriz de representatividade (real)

Ver `data/reference/matriz_boxes.csv`. Resumo:

- **Amazônia:** 5 boxes, todos floresta (classe 3); nenhum box de floresta aberta, estacional,
  inundável, campinarana ou secundária. AGB mediana 107–196; não há cauda abaixo de ~100.
- **Cerrado:** 6 boxes; classe 4 domina só em central/nordeste/noroeste; classe 3 domina em
  oeste/floresta/sul. **Nenhum** box de campo limpo/sujo (excluídos pelo domínio).
- **Fisionomias presentes em apenas um box:** floresta estacional do Cerrado aparece em
  oeste/floresta/sul (3 boxes), mas com históricos distintos; savana aberta só em
  central/nordeste/noroeste.
- **Ausências críticas para o objetivo anual:** sem cronossequência de regeneração, sem
  pós-fogo, sem borda florestal sistemática, sem várzea/igapó, sem gradiente altitudinal.
- **Pseudo-replicação:** 16–25 blocos de 5 km por box para 4,4–31,7 mil footprints.
- **Extrapolação já dentro do box:** AOA 0,57 (Amazônia leste) e 0,67 (Cerrado nordeste).

## 5. Critérios objetivos para especialização (propostos)

Um modelo específico por fisionomia só será treinado se houver, **simultaneamente**:

1. ≥ 8 blocos espaciais independentes de 5 km;
2. ≥ 500 células de 1 km (ou ≥ 5.000 footprints) após filtros;
3. ≥ 2 boxes distintos (evitar treinar e testar na mesma paisagem);
4. cobertura de AGB em pelo menos 2 ordens de grandeza ou amplitude ≥ 50 Mg ha⁻¹.

Caso contrário: *partial pooling* hierárquico ou feature categórica, nunca modelo isolado.

## 6. Hipóteses científicas (a testar, não assumir)

| ID | Hipótese | Pode ser rejeitada se |
|---|---|---|
| H1 | Fisionomia categórica reduz viés por box | R²/RMSE por box não melhora de forma consistente |
| H2 | Modelos hierárquicos superam modelo único e modelos isolados | partial pooling não supera M1/M2 em LOO |
| H3 | Histórico/idade de regeneração melhora resposta temporal | sem ganho em mudanças conhecidas |
| H4 | Features anuais (S2/S1/Landsat do ano) capturam mudança real | ΔAGB não correlaciona com mudança observada |
| H5 | Modelo de estado com prior assimétrico (perda abrupta, ganho gradual) supera modelo direto | piora estabilidade ou não reduz falso ganho |
| H6 | Calibração local pode ser reduzida com fisionomia/hierarquia | necessidade de amostras locais não cai |
| H7 | GEDI pode calibrar sem ser dependência operacional | inference exige GEDI ou derivados |
| H8 | 1 km é a escala defensável para estoque; 30 m é diagnóstico | 30 m supera 1 km em validação de campo/polígono |
