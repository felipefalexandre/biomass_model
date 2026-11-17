# 04 — Matriz de evidências

Cada linha liga uma **afirmação** que sustenta uma decisão de projeto à **evidência** disponível,
com força, aplicabilidade ao Brasil e limitações. A versão legível por máquina está em
`data/matriz_evidencias.csv`.

## 1. Escala de força

| Código | Significado |
|---|---|
| A | evidência forte, replicada, diretamente aplicável |
| B | evidência sólida, aplicável com ressalvas |
| C | evidência limitada/indireta; requer verificação local |
| D | hipótese/opinião de especialista; não usar como base única |

## 2. Matriz

| ID | Afirmação usada no projeto | Evidência | Força | Aplicabilidade BR | Limitações | Decisão afetada |
|---|---|---|---|---|---|---|
| E01 | Equações pantropicais com ρ, D, H são o padrão para AGB de árvores tropicais | Chave et al. 2005, Oecologia, DOI 10.1007/s00442-005-0100-x | A | alta (Amazônia) | erro maior fora da faixa de D; altura incerta | referência de campo, BGB |
| E02 | Modelos de 4–5 parâmetros com termo ambiental melhoram a estimativa pantropical | Chave et al. 2014, GCB, DOI 10.1111/gcb.12629 | A | alta | exige dados ambientais e de campo | calibração de campo |
| E03 | Densidade da madeira é preditor necessário e há base global utilizável | Chave et al. 2009, Ecol. Lett. 12:351–366, DOI 10.1111/j.1461-0248.2009.01285.x; Zanne et al. 2009, Dryad 10.5061/dryad.234 | A | alta | média por táxon mascara variação intraespecífica | allometria/BGB |
| E04 | No Cerrado, AGB e BGB medidas destrutivamente indicam razão raiz/parte aérea relevante e SE alto | Ribeiro et al. 2011, For. Ecol. Manage. 262:491–499, DOI 10.1016/j.foreco.2011.04.017 | B | alta (cerrado s.s., SE) | um sítio; SE de BGB ~23% | BGB no Cerrado |
| E05 | A biomassa varia fortemente entre fisionomias do Cerrado e as equações locais diferem | Miranda et al. 2014, Biotropica 46:125–138, DOI 10.1111/btp.12095 | B | alta | revisão; dados heterogêneos | estratificação |
| E06 | AGB de cerrado varia de ~12 a >100 Mg ha⁻¹ conforme fisionomia | Miranda et al. 2014; Ribeiro et al. 2011; Oliveira et al. 2019, Carbon Balance Manage., DOI 10.1186/s13021-019-0121-0 | B | alta | protocolos não padronizados | estratificação/benchmark |
| E07 | Mapas pantropicais de AGB existem e divergem entre si | Saatchi et al. 2011, PNAS, DOI 10.1073/pnas.1019576108; Baccini et al. 2012, NCC, DOI 10.1038/nclimate1354; Avitabile et al. 2016, GCB 22:1406–1420 | A | alta | resolução e erros variáveis | benchmark |
| E08 | Produto global de AGB por satélite em 100 m está disponível e documentado | Santoro et al. 2021, ESSD, DOI 10.5194/essd-13-3927-2021 | B | alta | 100 m; erros regionais | benchmark |
| E09 | Mapas harmonizados de AGB e BGB (2010) permitem comparação de estoques | Spawn et al. 2020, Sci. Data, DOI 10.1038/s41597-020-0444-4 | B | alta | 1 km; ano único | benchmark |
| E10 | GEDI fornece AGBD por footprint (~25 m) e agregados | Dubayah et al. 2020, Sci. Remote Sens., DOI 10.1016/j.srs.2020.100002; Duncanson et al. 2022, RSE 270:112845, DOI 10.1016/j.rse.2021.112845 | A | alta (amostral) | L4A é produto de modelo; saturação/erro em alta AGB; cobertura amostral | referência principal |
| E11 | Desempenho de GEDI varia por PFT/região e é pior onde há poucos dados | Duncanson et al. 2022 | A | alta | não cobre todo o Cerrado | AOA/estratificação |
| E12 | Estimadores design-based e híbridos permitem IC válidos combinando amostra e modelo | Ståhl et al. 2016, Forest Ecosystems, DOI 10.1186/s40663-016-0064-9 | A | alta | exige desenho de amostragem declarado | inferência |
| E13 | CV aleatório superestima desempenho de mapas espaciais | Roberts et al. 2017, Ecography, DOI 10.1111/ecog.02881; Ploton et al. 2020, Nat. Commun., DOI 10.1038/s41467-020-18321-y | A | alta | exige blocos/estratégia adequada | validação |
| E14 | É possível estimar a área de aplicabilidade de um modelo espacial | Meyer & Pebesma 2021, MEE, DOI 10.1111/2041-210X.13650 | A | alta | limiar depende de escolhas | AOA |
| E15 | CV com correspondência de distâncias vizinhas reduz otimismo | Milà et al. 2022, MEE 13:1304–1316, DOI 10.1111/2041-210X.13851 | B | alta | requer implementação cuidadosa | validação |
| E16 | Reanálise climática de alta resolução é insumo viável para features | Muñoz-Sabater et al. 2021, ESSD, DOI 10.5194/essd-13-4349-2021 | A | alta | 9 km; não é observação local | features |
| E17 | Dados de inventário florestal nacional existem, mas acesso/granularidade são restritos | IFN/SFB (a confirmar) | C | média | acesso e formato não confirmados | amostragem/campo |
| E18 | BGB não pode ser medido diretamente por sensoriamento remoto | Ribeiro et al. 2011; Miranda et al. 2014 | A | alta | depende de equações/razões | BGB |
| E19 | A fração de carbono da matéria seca é usualmente tratada como ~0,47 | IPCC (diretrizes 2006/2019 Refinement) — valores exatos a extrair das tabelas | B | alta | varia por componente/espécie | carbono |
| E20 | Produtos de sensoriamento não substituem validação independente | Ploton et al. 2020; Meyer & Pebesma 2021 | A | alta | — | validação |

## 3. Evidências ausentes (lacunas críticas)

| Lacuna | Impacto | Como tratar |
|---|---|---|
| Parcelas de campo acessíveis e georreferenciadas no Cerrado | alto | buscar IFN/teses/dados abertos; registrar como pergunta aberta |
| Erro de GEDI L4A estratificado para o Cerrado brasileiro | alto | calibrar com parcelas independentes; análise de sensibilidade |
| Equações de BGB para fisionomias de Cerrado | alto | usar múltiplas equações e reportar envelope |
| Máscara de degradação consistente | médio | limitar afirmações a desmatamento; degradação como fase futura |
| Série radiometricamente harmonizada Landsat/S2 | médio | harmonização explícita no pipeline |
| Dados de altura de dossel wall-to-wall (ex.: produto global de altura) | médio | usar como feature auxiliar com caveat |

## 4. Regra de uso

Uma decisão só pode ser classificada como "baseada em evidência" se tiver ao menos uma linha
com força A ou B **e** aplicabilidade declarada. Decisões apoiadas apenas em C/D devem ser
marcadas como "provisórias" nos ADRs.
