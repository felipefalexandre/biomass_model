# ADR-0032 — Ingestão canônica e evolutiva de inventários

- **Data:** 2026-11-24
- **Status:** aceito (decisão do usuário)
- **Relaciona-se a:** ADR-0027, ADR-0031

## Contexto

A incorporação de novos inventários hoje depende de scripts manuais. Não há esquema canônico,
controle de duplicidade, harmonização de unidades/equações, proveniência por observação nem
registro de status de uso. Isso impede o aprendizado evolutivo.

## Decisão

1. Criar um esquema canônico de observações com, no mínimo:
   - identificador único, fonte, versão, tipo de observação, data de referência;
   - geometria, CRS, precisão de localização, suporte espacial e área amostral;
   - bioma, fitofisionomia, classe de cobertura, AGB, unidade, incerteza, método e equação;
   - indicadores de qualidade, licença, referência bibliográfica e status de uso no modelo.
2. Cada fonte terá um adaptador responsável por aquisição, leitura, padronização, QA, unidades,
   harmonização espacial/temporal, deduplicação e proveniência.
3. A ingestão deve ser **idempotente**: executar duas vezes não duplica observações.
4. A tabela resultante deve ser armazenada preferencialmente em Parquet/GeoParquet, com fallback
   em CSV/GeoPackage quando a dependência não estiver disponível.
5. Nenhuma fonte entra simultaneamente no treino e na validação independente. O status de uso
   deve ser explícito.
6. Fontes derivadas de um mesmo inventário em repositórios diferentes devem ser identificadas e
   deduplicadas.

## Consequências

- O treinamento passa a consumir a tabela canônica, não CSVs ad hoc.
- A curadoria de inventários vira parte permanente do sistema.
- A promoção de modelos depende de proveniência e qualidade documentadas.

## Arquivos

`src/biomass_model/inventory/`, `data/reference/inventarios_abertos.md`, `docs/46`.
