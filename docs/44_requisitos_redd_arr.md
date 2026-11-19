# 44 — Requisitos REDD+/ARR e o que o modelo entrega

**Data:** 2026-11-18 · **Status:** requisitos; não é certificação nem parecer.

## 1. Papel do modelo

O modelo entrega **biomassa/carbono por hectare** e **estoque por polígono/estrato**, por ano,
a partir de dados de satélite abertos. Ele **não** estima desmatamento, reflorestamento,
adicionalidade, vazamento ou permanência: esses componentes vêm de mapas/modelos de atividade e
do desenho do projeto. A biomassa é insumo para os cálculos de emissão/remoção.

## 2. Requisitos do projeto → o que o modelo fornece

| Requisito | Produto do modelo | Status |
|---|---|---|
| Fator de emissão/remoção (biomassa) | AGBD por célula/estrato (Mg ha⁻¹) + IC | parcial |
| Estoque por polígono | Tabela: área, média, total, IC, estrato | `polygon-stats` implementado |
| Mapa espacial anual | COG AGBD 1 km + IC + AOA | planejado (P1–P8) |
| Estratificação | Crosswalk fitofisionomias + composição | inicial |
| Incerteza | conformal por célula; block bootstrap por polígono | parcial |
| Validação independente | campo (PLOS/ORNL/IFN/novos) | parcial (Cerrado antigo) |
| Reprodutibilidade | manifestos, versões, testes | bom |
| Auditoria | model card + ADRs + diário | bom |

**Fora do modelo (externo):** mapas de desmatamento/fogo/regeneração, linha de base de
desmatamento, adicionalidade, leakage, permanência, elegibilidade e certificação.

## 3. O que já pode e o que não pode ser dito

**Pode:**
- estimar AGBD média e estoque por polígono em 1 km, com IC e máscara de domínio;
- comparar regiões/anos sob as mesmas regras;
- gerar mapas anuais que o usuário sobrepõe a mapas de desmatamento para calcular emissões
  (a sobreposição é feita fora do modelo).

**Não pode, hoje:**
- afirmar acurácia de campo na Amazônia (não há validação pós-2019);
- afirmar detecção de desmatamento/reflorestamento (não é o escopo);
- emitir créditos ou parecer de elegibilidade;
- extrapolar para classes 2/6, várzeas, manguezais ou fora da AOA;
- usar 30 m como escala de relatório.

## 4. Requisitos mínimos para uso em MRV

1. **Validação independente** por bioma/estrato, com ≥30 sítios e período compatível; R² ≥0,40 e
   |viés| ≤15% (critério provisório de `docs/37`).
2. **Estoque por polígono** com erro compatível com o IC declarado (sem viés >15%).
3. **Incerteza** com cobertura IC90 85–95% por bioma/ano e por polígono.
4. **Estratificação** acordada (IBGE/MapBiomas/idade) e composição documentada.
5. **Modelo versionado** (features, hiperparâmetros, sementes, manifestos, model card).
6. **Auditoria de independência:** nenhum produto de biomassa no inference.
7. **Plano de atualização anual** e detecção de drift de features.

## 5. Lacunas críticas

- Campo pós-2019 na Amazônia (inexistente no projeto).
- Orçamento/parceria para ~100 células de calibração na Amazônia e ≥25 no Cerrado.
- ORNL com fator/datum resolvidos para validação histórica.
- BGB e solo (modelo separado; hoje não há).
- Classes 2 (campestre) e 6 (floresta alagável): incluir ou declarar exclusão.
- 30 m: decidir se será apenas diagnóstico (recomendado).

## 6. Sequência para prontidão MRV

1. P1 (features anuais) e P2 (covariáveis de estado opcionais).
2. P3 (fisionomia/hierarquia) se houver ganho.
3. P6 (PLOS/ORNL) e campo novo; curvas de calibração.
4. P7 (polígono/incerteza) e P8 (produto anual).
5. Model card, protocolo de auditoria e validação externa.

## 7. Portões MRV obrigatórios do produto de biomassa

Estes portões são **indispensáveis para gerar o produto** (mapa, estoque, estrato). Não são
opcionais nem “fase futura”. Um produto só é liberado se todos estiverem documentados e
verificáveis. Eles não certificam projeto nem substituem auditoria externa.

| Portão | Requisito | Evidência mínima | Bloqueia? |
|---|---|---|---|
| G0 Escopo | Versão, ano, bioma, domínio, resolução, limitações | model card + changelog | sim |
| G1 Dados/proveniência | Fontes, licenças, contas, datas, hashes, versões | `data/manifests/` + catálogo | sim |
| G2 Validação | LOO espacial + campo independente; métricas por box/estrato | relatório de métricas + sítios reservados | sim |
| G3 Incerteza | IC por célula e por polígono; cobertura e componentes | conformal + bootstrap espacial | sim |
| G4 Estratificação | Crosswalk, composição, AOA, máscara 3/4 e lacunas | crosswalk + fração AOA + mapa de domínio | sim |
| G5 Reprodutibilidade | Código versionado, seeds, ambiente, testes | commit + `pytest` + manifesto | sim |
| G6 QA/QC | Faixas válidas, nodata, bordas, consistência anual, duplicatas | relatório de QA + flags | sim |
| G7 Auditoria | Premissas, limitações, decisões, histórico de versões | ADRs + diário + model card | sim |

### 7.1 Indispensável (dentro do produto)

- acurácia contra referência independente, com sítios nunca usados no ajuste;
- incerteza calibrada em cada escala (célula, estrato, polígono);
- estratificação explícita e rastreável (fitofisionomia/composição);
- domínio e AOA explícitos, com áreas não estimadas;
- linhagem completa de dados e código;
- QA/QC automatizado e registrado;
- versionamento anual e changelog;
- limitações e premissas escritas;
- capacidade de auditoria por terceiro (reproduzir o número).

### 7.2 Fora do produto

- mapas/modelos de desmatamento, fogo e regeneração (atividade);
- linha de base de desmatamento, adicionalidade, leakage, permanência;
- elegibilidade, certificação e emissão de créditos.

A MRV do projeto combina **este produto de biomassa** com **dados de atividade externos**; o
modelo não precisa gerar nem prever a atividade.

### 7.3 Verificação automatizada (implementada)

python -m biomass_model.cli mrv-check --csv <predicoes.csv> avalia G6 (faixas, duplicatas), G4 (domínio/AOA) e G3 (cobertura IC quando há lo/hi/obs). G0/G1/G2/G5/G7 permanecem manuais por exigirem artefatos externos (model card, manifestos, relatório de campo, commit, ADRs).

### 7.4 Critério de liberação

Um ano/região só é publicado como base MRV se G0–G7 estiverem completos. Sem campo independente,
o produto pode existir como **experimental**, explicitamente marcado, mas não como base MRV.
