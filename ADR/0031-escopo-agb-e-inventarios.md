# ADR-0031 — Escopo de AGB e aquisição de inventários

- **Data:** 2026-11-24
- **Status:** aceito (decisão do usuário)
- **Relaciona-se a:** ADR-0011, ADR-0021, ADR-0027

## Contexto

O planejamento antigo incluía BGB, carbono, CO₂e, desmatamento, reflorestamento, adicionalidade,
vazamento, permanência e créditos. O novo escopo prioriza AGB. O usuário autorizou investir em
inventários antigos (2000 em diante) e novos, sempre com dados abertos e confiáveis.

## Decisão

1. O escopo prioritário é **AGB** (Mg ha⁻¹ e Mg), com incerteza e rastreabilidade.
2. BGB, carbono, CO₂e, desmatamento/reflorestamento, adicionalidade, vazamento, permanência,
   elegibilidade, créditos e projeções futuras ficam **fora da prioridade** até consolidação da
   AGB. Não serão implementados agora.
3. A aquisição de inventários prioriza:
   - dados abertos e licença compatível;
   - cobertura de 2000 em diante, incluindo inventários antigos e novos;
   - representatividade por bioma e fitofisionomia;
   - independência em relação aos produtos usados no treinamento;
   - documentação de protocolo, equação, incerteza e suporte espacial.
4. Inventários catalogados não contam como incorporados até passarem por ingestão, controle de
   qualidade, harmonização e registro de proveniência.
5. Classes 2 (Formação Campestre) e 6 (Floresta Alagável) permanecem fora do domínio até decisão
   explícita.

## Consequências

- O foco imediato é a base observacional de campo e a validação independente.
- A documentação antiga de BGB/carbono/desmatamento deve ser marcada como fase futura, não como
  escopo vigente.
- A aquisição de inventários precisa de um pipeline canônico, não de scripts ad hoc.

## Arquivos

`docs/46`, `docs/10`, `docs/11`, `docs/16`, `data/reference/inventarios_abertos.md`.
