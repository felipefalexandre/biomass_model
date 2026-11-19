# 44 — Requisitos REDD+/ARR e o que o modelo entrega

**Data:** 2026-11-18 · **Status:** requisitos; não é certificação nem parecer.

## 1. Para que o produto será usado

Projetos REDD+ (desmatamento evitado, degradação, conservação) e ARR (afforestation,
reforestation, revegetation) precisam de:

- **Fator de emissão/remoção:** biomassa (AGB/BGB) e carbono por hectare, por estrato.
- **Dados de atividade:** área desmatada/queimada/regenerada por ano.
- **Estoque e mudança de estoque:** linha de base, monitoramento periódico, estoque final.
- **Estratificação:** fitofisionomia, classe de idade, solo/clima, histórico.
- **Incerteza:** por célula, por estrato e por polígono/projeto.
- **MRV:** reprodutibilidade, versão, auditoria, validação independente, documentação.

O modelo entra como **camada de biomassa/carbono** e **mudança de biomassa**. Ele não entrega
adicionalidade, linha de base contrafactual, vazamento (leakage), permanência ou elegibilidade —
esses são desenho de projeto e precisam de dados e métodos próprios.

## 2. Mapa de requisitos → produto

| Requisito | Produto | Status |
|---|---|---|
| Estoque por estrato/polígono | Tabela por polígono (média, total, IC, classe) | `polygon-stats` implementado |
| Mapa espacial | AGBD anual 1 km (30 m diagnóstico) + IC + AOA | planejado (P1–P8) |
| Mudança anual | ΔAGB com perda/ganho e transições | não validado (docs/43) |
| Estratificação | Crosswalk fitofisionomias + composição | crosswalk inicial |
| Incerteza | conformal por célula; block bootstrap por polígono | parcial |
| Validação independente | campo (PLOS/ORNL/IFN/novos) | parcial (só Cerrado antigo) |
| Reprodutibilidade | manifestos, versões, testes | bom |
| Auditoria/versionamento | model card + ADRs + diário | bom |

## 3. O que já pode e o que não pode ser dito

**Pode:**
- estimar AGBD média e estoque por polígono em 1 km, com IC estatístico e máscara de domínio;
- comparar regiões e anos sob as mesmas regras e versões;
- gerar mapa anual para análise espacial e comparação com desmatamento (após P1–P8).

**Não pode, hoje:**
- afirmar acurácia de campo na Amazônia (não há validação pós-2019);
- afirmar detecção de mudança (docs/43);
- emitir créditos ou parecer de elegibilidade;
- extrapolar para classes 2/6, várzeas, manguezais ou áreas fora da AOA;
- usar 30 m como escala de relatório.

## 4. Requisitos mínimos para uso em MRV

1. **Validação independente** por bioma/estrato, com ≥30 sítios e período compatível; R² ≥0,40 e
   |viés| ≤15% (critério provisório de `docs/37`).
2. **Mudança** com ≥3 eventos por tipo, sinal ≥80% (perda) e contraste ≥3× buffer.
3. **Incerteza** com cobertura IC90 85–95% por bioma/ano e por polígono.
4. **Estratificação** acordada (IBGE/MapBiomas/idade) e composição documentada.
5. **Modelo versionado**, com features, hiperparâmetros, sementes, manifestos e model card.
6. **Auditoria de independência:** nenhum produto de biomassa no inference.
7. **Plano de atualização anual** e detecção de drift.

## 5. Lacunas críticas para REDD+/ARR

- Campo pós-2019 na Amazônia (inexistente no projeto).
- Orçamento/parceria para ~100 células de calibração na Amazônia e ≥25 no Cerrado.
- Validação de mudança com eventos e/ou campo repetido.
- BGB e solo (modelo separado; hoje não há).
- Classes 2 (campestre) e 6 (floresta alagável): incluir ou declarar exclusão.
- 30 m: decidir se será apenas diagnóstico (recomendado).

## 6. Sequência para prontidão MRV

1. P1–P2 (features anuais + eventos) e validação de mudança.
2. P6 (PLOS/ORNL) e campo novo; calibrar por estrato.
3. P7 (polígono/incerteza) e P8 (produto anual).
4. Model card e protocolo de auditoria; só então uso externo.
