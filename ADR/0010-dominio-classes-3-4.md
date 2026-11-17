# ADR-0010 — Domínio = classes brutas 3 e 4 do MapBiomas (Coleção 11)

**Status:** aceito
**Data:** 2026-11-17
**Substitui:** ADR-0009

## Contexto

O ADR-0009 definiu o domínio como a máscara de elegibilidade da etapa anterior: pixels com classe
3/4 do MapBiomas em **todos** os anos de 2007 a 2016. Essa máscara foi desenhada para outro
objetivo (desmatamento) e exclui regeneração, vegetação que mudou de classe e áreas que eram
antrópicas em qualquer ano do período.

O usuário definiu que, neste projeto, a estimativa deve cobrir **apenas as áreas de classe 3 e 4
do MapBiomas**, no ano de referência, com possibilidade de estratificar por tipo de vegetação. A
legenda oficial da Coleção 11 foi baixada e conferida (`data/reference/mapbiomas/`).

## Opções

1. Manter a máscara 2007–2016 (ADR-0009).
2. Usar as classes 3/4 no ano-alvo.
3. Usar toda a vegetação natural (classes 1–12) e reportar por classe.

## Decisão

Adotar a opção 2 como **domínio primário**:

```
dominio(t) = (classe_mapbiomas(t) == 3) | (classe_mapbiomas(t) == 4)
```

- Classe **3 = Formação Florestal** (predominante na Amazônia).
- Classe **4 = Formação Savânica** (predominante no Cerrado).
- A máscara estável 2007–2016 deixa de ser o domínio e passa a ser **estrato opcional**
  ("vegetação estável"), usado para comparação com os produtos da etapa anterior.
- Mangue (5), floresta alagável (6) e formações campestres (11/12) ficam **fora** da v1; a
  exclusão é declarada e pode ser revista em versão futura.

## Consequências

- O denominador muda a cada ano; totais anuais não são comparáveis sem declarar a área elegível
  do ano.
- Comparabilidade com a etapa de desmatamento só é válida quando o estrato "estável" é aplicado
  explicitamente.
- Não há mais confusão entre os códigos brutos do MapBiomas (3/4) e o `ClassCode` derivado do
  pipeline de desmatamento (`rules.py`): a conversão é local, testada e documentada.
- A estratificação passa a ser: bioma × classe (3/4) × tipologia/estrato.

## Evidência

- Legenda oficial Coleção 11 (PDF baixado; classes 3 e 4 confirmadas).
- Distribuição empírica: classe 3 domina a floresta amazônica (93,3% no tile piloto) e classe 4
  domina a savana do Cerrado (53,6% no tile piloto).
- Ver `docs/17`, `docs/22` (RE01) e `docs/26`.
