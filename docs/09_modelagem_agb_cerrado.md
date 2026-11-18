# 09 — Modelagem de AGB no Cerrado

## 1. Por que o Cerrado é o caso mais difícil

- **Gradiente estrutural extremo:** campo limpo, campo sujo, campo cerrado, cerrado *sensu
  stricto*, cerradão, matas de galeria e florestas estacionais. A AGBD vai de ~5 a >150 Mg ha⁻¹
  (Miranda et al. 2014; Ribeiro et al. 2011; Oliveira et al. 2019).
- **Estrutura esparsa e baixa:** sensores ópticos veem sobretudo o estrato herbáceo, que não é o
  alvo principal de biomassa lenhosa; a relação sinal–biomassa é fraca.
- **Fogo:** recorrente, altera estrutura e composição, e cria não estacionariedade.
- **Sazonalidade:** contraste seco/úmido muito forte, com mudança de reflectância e de área
  foliar.
- **GEDI:** cobertura menor e desempenho pior em biomassa baixa; L4A não é otimizado para savana.
- **Dados de campo:** escassos, dispersos e com protocolos heterogêneos.

## 2. Estratégia

### 2.1 Estratificação por fitofisionomia

Usar as classes do MapBiomas (e, quando possível, subclasses/atributos) para agrupar em:

| Grupo | Descrição | Faixa esperada de AGBD |
|---|---|---|
| G1 | campo limpo/sujo (lenhoso mínimo) | muito baixa (<15) |
| G2 | campo cerrado / cerrado ralo | baixa (15–40) |
| G3 | cerrado *sensu stricto* / denso | média (40–100) |
| G4 | cerradão e floresta estacional | alta (>100) |

As faixas são **orientativas**, baseadas na literatura citada, e não devem ser usadas como
rótulo de treino (evita circularidade); servem para diagnóstico e para checar plausibilidade.

### 2.2 Features prioritárias

- **Textura e estrutura do dossel:** GLCM, variogramas, sombreamento, fração de solo exposto.
- **Índices sensíveis a vegetação seca:** NDII, NBR, índices de senescência.
- **Séries temporais:** métricas de sazonalidade e de resposta a chuva (S2/Landsat).
- **Radar:** S1 VH/VV, coerência; sensível a troncos e estrutura, útil onde óptico falha.
- **Topografia e solo:** declividade, fertilidade/textura (SoilGrids) — savanas ocorrem em solos
  pobres e bem drenados.
- **Fogo:** cicatriz de queimada (quando disponível) como feature de estado.

### 2.3 Modelagem em duas etapas (sugestão avaliável)

1. **Etapa de presença/cobertura lenhosa:** prever fração de cobertura arbórea ou probabilidade de
   estrato lenhoso.
2. **Etapa de AGBD condicional:** prever AGBD dado que há lenhosas, com features de estrutura.

Isso evita que o modelo "aprenda" que solo exposto tem AGBD zero e misture os dois problemas.
A avaliar contra o modelo de uma etapa (`docs/25`).

### 2.4 Referência

- GEDI L4A apenas onde há cobertura suficiente e qualidade adequada; **não** usar em campo
  limpo/sujo como se fosse AGBD confiável.
- Parcelas de Cerrado (Ribeiro 2011 e compilações) como referência/validação, com atenção à
  faixa de DAP (5–27,6 cm no estudo de Ribeiro) e à extrapolação.
- Equações específicas por fitofisionomia (Miranda et al. 2014 sintetiza 12 equações distintas):
  a escolha da equação é uma **decisão de projeto documentada**, não um detalhe.

## 3. BGB no Cerrado

Ver `docs/10`. Ponto central: a razão raiz/parte aérea no Cerrado é alta e variável; Ribeiro et
al. (2011) mediram BGB de 37.501,8 kg ha⁻¹ (SE 23%) contra AGB de 62.965,5 kg ha⁻¹ (SE 14,6%)
em cerrado *sensu stricto*, indicando que **ignorar BGB subestima o estoque total de forma
material**. O mesmo estudo alerta que a razão é menor que a de outras estimativas para cerrado
s.s., ou seja, há incerteza real.

### 2.1 Evidência do piloto: L4A não serve como alvo no Cerrado

A extração GEDI L4A no piloto (`-47,70, -13,95`; 2019–2024) deu 16.851 footprints com mediana de
**6,2 Mg ha⁻¹** e 59,6% abaixo de 10 Mg ha⁻¹; o painel do IFN tem mediana de 19,4 Mg ha⁻¹. O viés
de savana aberta não é corrigível por filtro de qualidade. Por isso o modelo do Cerrado é treinado
em **parcelas de campo com coordenadas**, e o L4A entra apenas como covariável, benchmark externo e
diagnóstico de cobertura (ADR-0015). Nenhuma métrica contra L4A será apresentada como validação.

### 2.2 Primeiro modelo de campo: PLOS 2018

O S3 do artigo de Roitman et al. (2018) tem 77 sítios com coordenadas e AGB; 75 são Cerrado. Só 45
caem nas classes 3/4 do MapBiomas 2024 — os outros 30 são formações campestres ou uso antrópico,
excluídas pelo domínio (ADR-0010). Com features de 1 km e CV por blocos de 1°, o baseline de 45
sítios deu R² 0,328, RMSE 8,34 e MAE 6,53 Mg ha⁻¹ (2 folds negativos). Temperatura média domina a
importância, seguida de elevação. n=45 é indicativo, não conclusivo; a perda de 40% dos sítios por
causa do domínio é uma limitação registrada (RC12), e não um erro a esconder.

## 4. Erros esperados e como tratá-los

| Erro | Origem | Tratamento |
|---|---|---|
| AGBD superestimada em campo sujo | sinal óptico do estrato herbáceo | etapa de cobertura; máscara de lenhosas |
| AGBD subestimada em cerradão | saturação/limite de referência | modelo separado para G4 |
| Viés por fogo | não estacionariedade | feature de fogo; validação por tempo desde fogo |
| Viés por sazonalidade | composição em estação errada | composições fixas por estação |
| Extrapolação para floresta estacional | treino concentrado em s.s. | AOA; estratificação |

## 5. Critérios de aceite para o Cerrado

- Erro por grupo fisionômico reportado separadamente (não só agregado).
- IC de 90% com cobertura próxima do nominal **dentro de cada grupo**.
- Nenhuma estimativa de G1/G2 apresentada sem ressalva de baixa sensitividade.
- BGB com envelope de cenários (mínimo/central/máximo), não valor único.

## 6. Riscos dominantes

| Risco | Mitigação |
|---|---|
| Referência GEDI inadequada | filtrar por cobertura; usar campo |
| Fisionomias misturadas | estratificação fina; AOA |
| Fogo | feature e análise de sensibilidade |
| BGB incerto | cenários e transparência |
| Escassez de campo | compilação aberta; declarar limitação |
