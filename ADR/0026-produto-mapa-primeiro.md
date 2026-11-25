# ADR-0026 — Produto mapa-first com tabela por polígono

- **Data:** 2026-11-18
- **Status:** aceito; resolução substituída por ADR-0030; polígono expandido por ADR-0028
- **Contexto:** o usuário quer estoque por estrato/polígono e também mapa para comparar com
  desmatamento. O teste de viabilidade mostrou que estimar por estrato com médias transferidas de
  outra região erra de −41% a +43%, enquanto o mapa mantém padrão espacial e permite recorte.
- **Decisão proposta:**
  1. Produto principal: mapa anual de AGBD (1 km oficial; 30 m diagnóstico) com IC, AOA e máscara 3/4.
  2. A soma/polígono é cálculo do usuário; tabela por polígono é apenas utilidade de QA, não produto.
  3. Não haverá produto “polygon-only” independente; o modo rápido, se existir, usa médias de
     estrato locais/calibradas e é apenas um atalho de relatório, sem mapa nem análise de perda.
  4. Composição do usuário é entrada opcional/checagem, não ajuste forçado do mapa.
- **Consequências:** implementar primeiro o mapa anual; `polygon-stats` já disponível para agregar.
  Sem mapa, não há comparação espacial com desmatamento.
- **Arquivos:** `docs/41`, `src/biomass_model/polygon.py`.
