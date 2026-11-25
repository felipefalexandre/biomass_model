# ADR-0033 — Registro de modelos e promoção champion/challenger

- **Data:** 2026-11-24
- **Status:** aceito (decisão de governança do projeto)
- **Relaciona-se a:** ADR-0024, ADR-0027, ADR-0032

## Contexto

Os experimentos geram métricas, modelos e predições em arquivos isolados. Sem um registro
versionado não é possível comparar gerações, preservar o benchmark, impedir promoção automática
ou auditar qual modelo produziu um produto.

## Decisão

1. Todo modelo candidato é registrado em `registry.json`, com:
   - `model_id`, família, status, data, commit, hash das métricas;
   - caminhos para métricas, predições e artefato `.joblib`;
   - alvo, `n`, métricas principais e modo de validação.
2. O status segue o esquema **champion/challenger**:
   - `challenger`: candidato;

   - `champion`: versão operacional aprovada;

   - `retired`: versão substituída.
3. Novos dados ou modelos **não** substituem o champion automaticamente. A promoção exige
   comando explícito e justificativa.
4. Quando um champion é promovido, o champion anterior da mesma família é rebaixado e o evento
   fica no histórico do registro.
5. O registro não substitui a validação científica: promover um modelo não o torna produto MRV.
   Os critérios de `docs/37` §6 continuam obrigatórios.
6. O registro deve ser preservado e versionado; artefatos grandes ficam fora do git, mas os
   caminhos e hashes ficam registrados.

## Consequências

- Comparações entre gerações passam a ter histórico auditável.
- Nenhuma promoção silenciosa.
- O model card e o produto devem apontar para o `model_id` promovido.
- O registro é deliberadamente simples (JSON/CLI); pode evoluir sem banco de dados.

## Arquivos

`src/biomass_model/model_registry/`, `docs/49_governanca_modelos.md`,
`ADR/0024-criterios-aceitacao.md`.
