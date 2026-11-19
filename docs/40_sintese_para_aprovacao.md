# 40 — Síntese para aprovação

**Data:** 2026-11-18 · **Status:** investigação concluída; nenhuma mudança de modelo feita.

## 1. Resposta à pergunta central

O sistema atual **não** estima o estoque de um ano nem o atualiza: ele espacializa um compósito
GEDI multi-ano (2020–2024). Para o objetivo declarado — estimar AGBD anual a partir de dados de
satélite **do próprio ano**, responder a mudanças reais e não depender de GEDI no inference — é
necessário um desenho de **estado + mudança**, com features anuais e validação temporal.

Isso não invalida o que foi feito: os 11 boxes, a validação LOO, a calibração local, o AOA e o
conformal continuam sendo a base de avaliação. O que muda é o **estimando temporal** e o papel do
GEDI (calibração, não produto).

## 2. Diagnóstico em cinco pontos

1. **Alvo e inferência:** hoje o alvo é GEDI L4A; no inference as features já não usam GEDI. A
   regra “GEDI só calibra” é compatível, mas precisa ser auditada e declarada.
2. **Tempo:** o compósito S2 é único para todos os anos; isso apaga mudanças. É a maior
   limitação para o objetivo.
3. **Referência:** calibração e teste compartilham GEDI (Linha A); campo é só PLOS 2018 (Linha B,
   R² 0,29). Falta validação pós-2019 na Amazônia.
4. **Representatividade:** a Amazônia não tem box abaixo de ~107 Mg ha⁻¹; o Cerrado tem dois
   regimes com vazio entre ~25 e ~50; não há cronossequência de regeneração nem pós-fogo.
5. **Contabilidade:** a máscara 3/4 do ano faz áreas desmatadas desaparecerem; para estoque é
   preciso reportar perda/ganho explicitamente.

## 3. Recomendação de sequência (maior potencial primeiro)

1. **E1 — features anuais + modelo direto (A1).** Sem novas dependências; usa S2/S1 de
   2019–2024. É o teste mais direto da hipótese “dados do ano capturam o estado”.
2. **E2 — fogo/PRODES/secundária + testes de mudança.** Transforma o modelo em algo que
   responde a mudanças; mede sinal, contraste e falso alarme.
3. **E7 — curvas de calibração local.** Define o custo real de MRV e testa se fisionomia/hierarquia
   reduzem a necessidade de amostras.
4. **E3/E4 — fisionomia e hierarquia.** Só depois de E1/E2, para não gastar esforço em
   estratificação sem sinal temporal.
5. **E5/E6 — estado-espaço e prior assimétrico.** Onde o ganho científico é maior (perda
   abrupta vs ganho gradual), mas com maior custo de implementação.
6. **E9 — polígono e incerteza.** Fecha o produto; depende de E1–E7.
7. **Linha B — PLOS/ORNL.** Em paralelo desde o início; sem ela, nenhum resultado é promovido.

## 4. O que dá para fazer com os dados atuais

- E1, E2 parcial (fogo/PRODES/MapBiomas precisam ser organizados), E7, E8, E9 em 1 km.
- Validação PLOS com Landsat anual (2004–2014).
- Auditoria de sensibilidade dos filtros GEDI.
- Nenhum mapa anual nacional: os boxes não cobrem o território.

## 5. O que depende de novos dados/parcerias

- **Campo pós-2019 na Amazônia** (não existe hoje): essencial para Linha B.
- **ORNL**: resolver fator/datum e calcular AGB/ha; validação 2009–2018.
- **MapBiomas pré-2004**: recupera 25 sítios PLOS.
- **PRODES/Fogo/Secundária/SoilGrids**: catálogo e ingestão.
- **Financiamento de campo** para calibração local (~100 células na Amazônia; ≥25 no Cerrado).

## 6. Decisões solicitadas (aprovação)

1. **Produto:** adotar AGBD anual + estoque + mudança, com 1 km oficial e 30 m diagnóstico?
2. **Independência:** GEDI (e derivados) proibido como feature/prior no inference?
3. **Taxonomia:** adotar níveis 1–2 (IBGE + MapBiomas + estrutura) e os critérios objetivos de
   especialização de `docs/36`?
4. **Critérios de aceite:** aprovar os limites de `docs/37` §6 (espacial, temporal, campo,
   incerteza, independência)?
5. **Prioridade:** começar por E1/E2/E7 e manter Linha B em paralelo?
6. **Aquisições:** autorizar MapBiomas pré-2004, PRODES/Fogo/Secundária, SoilGrids e a
   recuperação do ORNL?
7. **Campo:** buscar parceria/financiamento para validação independente pós-2019 na Amazônia?

## 7. Mapa dos entregáveis

| Entregável | Onde |
|---|---|
| 1. Auditoria científica | `docs/35` |
| 2. Revisão bibliográfica com DOI | `docs/36` §2 |
| 3. Matriz de representatividade | `docs/36` §4 + `data/reference/matriz_boxes.csv` |
| 4. Diagnóstico das limitações | `docs/35` §3 e §8 |
| 5. Matriz de hipóteses | `docs/36` §6 |
| 6. Plano de experimentos | `docs/37` §5–7 |
| 7. Comparação de arquiteturas | `docs/37` §4 |
| 8. Plano de avaliação GEDI | `docs/35` §7 + `docs/37` §5 |
| 9. Plano de validação independente | `docs/38` §2–4 |
| 10. Recuperação ORNL | `docs/38` §3 |
| 11. Avaliação por polígono | `docs/38` §6 |
| 12. Plano de incertezas | `docs/38` §6 |
| 13. Arquitetura Python | `docs/39` §2 |
| 14. Sequência de implementação | `docs/39` §3 |
| 15. Critérios de aprovação | `docs/37` §6 + `docs/39` §7 |
| 16. ADRs propostas | `ADR/0020`–`0024` |
| 17. Riscos e limitações | `docs/39` §5 |
| 18. Roadmap científico | `docs/39` §3 + §5 deste doc |

## 8. Regra de execução

Nada será implementado antes da aprovação. Na implementação, uma hipótese por vez, sempre com
baseline A0, split congelado, testes de regressão e registro de resultado negativo. Melhorias só
são promovidas se passarem pelos critérios de `docs/37` §6 e pela Linha B.


## 9. Atualização 2026-11-18: continuidade confirmada

O usuário aprovou os pontos anteriores e esclareceu o objetivo final (REDD+/ARR). A sugestão de
estimar por estrato/polígono foi incorporada como **camada de relatório**, não como substituta do
mapa. Permanecem: mapa anual estado+mudança, GEDI só calibração, validação A/B/T, calibração
local. Novos artefatos: `docs/41` (mapa vs estrato), `docs/42` (E1), `docs/43` (mudança
preliminar), `docs/44` (REDD+/ARR), ADR-0025/0026.

Decisões adicionais a confirmar: (i) incluir classes 2 e 6 no produto? (ii) 30 m apenas
diagnóstico? (iii) orçamento/parceria de campo?
