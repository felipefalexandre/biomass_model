# ADR-0029 — Fitofisionomia IBGE 1:250.000 como camada estrutural

- **Data:** 2026-11-24
- **Status:** aceito (decisão do usuário)
- **Relaciona-se a:** ADR-0023, ADR-0025

## Contexto

As classes 3 e 4 do MapBiomas são filtros de domínio e classes agregadas, não fitofisionomias.
O crosswalk atual é indicativo e não foi usado no treinamento. O novo escopo exige que a
fitofisionomia influencie treinamento, calibração, avaliação, incerteza e apresentação.

## Decisão

1. Usar o mapeamento oficial de vegetação do IBGE (1:250.000) como referência fitofisionômica.
2. Construir uma tabela de correspondência documentada entre IBGE, MapBiomas, bioma, vegetação
   potencial/atual e estágios de regeneração/degradação, incluindo transições e ambiguidades.
3. Não assumir correspondência direta entre legenda IBGE e classes MapBiomas.
4. Testar formalmente a fitofisionomia como:
   - variável categórica do modelo;
   - estrato de calibração;
   - estrato de amostragem;
   - componente de modelo hierárquico;
   - critério de seleção de modelos especialistas;
   - combinação das abordagens.
5. Não criar um modelo independente por fitofisionomia sem os critérios objetivos de suporte
   amostral de `docs/36` §5. Caso contrário, usar partial pooling ou feature categórica.
6. A camada de fitofisionomia deve ser versionada, com código, fonte, data e licença.

## Consequências

- A classe MapBiomas 3/4 continua sendo o filtro de domínio.
- A fitofisionomia passa a ser uma camada separada e um componente estrutural do sistema.
- Resultados por fitofisionomia só podem ser reportados quando houver suporte amostral e
  granularidade cartográfica suficientes.

## Arquivos

`docs/36`, `docs/41`, `data/reference/fitofisionomias_crosswalk.csv`,
`src/biomass_model/stratification/`.
