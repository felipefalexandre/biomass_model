# 49 — Governança de modelos: registro e champion/challenger

**Data:** 2026-11-24 · **Status:** implementado; nenhum modelo promovido a champion.

## 1. Objetivo

Manter histórico auditável de modelos candidatos, comparar métricas e impedir que a aquisição de
novos dados ou um experimento substitua automaticamente o modelo operacional.

## 2. Estrutura

`registry.json` (em `E:\Mapbiomas\biomass\model_registry` por padrão de uso) contém:

- `model_id`, `family`, `status` (`challenger`, `champion`, `retired`);
- data, caminho e SHA-256 das métricas;
- caminhos para `.joblib` e predições;
- alvo, `n`, número de features e modo de validação;
- métricas principais (`r2`, `rmse`, `mae`, `medae`, `bias`, relativos);
- histórico de registro, promoção e rebaixamento.

O registro **não** move artefatos grandes para o git. Ele registra caminho e hash; os arquivos
continuam no armazenamento de dados.

## 3. Regras

1. Todo experimento que gera `*.metrics.json` deve ser registrado.
2. O status inicial é `challenger`.
3. Promoção é explícita e exige justificativa.
4. Ao promover um champion, o anterior da mesma família vira `retired`.
5. Promover não significa aprovar para MRV; os critérios de `docs/37` §6 continuam valendo.
6. O `model_id` promovido deve aparecer no model card e no produto.

## 4. Comandos

```powershell
python -m biomass_model.cli model-register `
  --metrics E:\Mapbiomas\biomass\derived\field_plos2018_rf_block200.metrics.json `
  --registry E:\Mapbiomas\biomass\model_registry `
  --model-id field_plos2018_block200 --family field_first --status challenger

python -m biomass_model.cli model-list --registry E:\Mapbiomas\biomass\model_registry
python -m biomass_model.cli model-compare --registry E:\Mapbiomas\biomass\model_registry --metric rmse
python -m biomass_model.cli model-promote --registry E:\Mapbiomas\biomass\model_registry `
  --model-id <id> --reason "texto"
```

## 5. Estado atual

Registrados como **challengers** (2026-11-24):

- `field_plos2018_block200`: validação primária, n=16, R²=0,262, RMSE=10,81.
- `field_plos2018_loo`: sensibilidade, n=40, R²=0,197, RMSE=9,54.

Nenhum é champion: a amostra é antiga/pequena, não há holdout independente e a cobertura do IC90
no cenário de blocos ficou abaixo do nominal.

**Cuidado:** os dois modelos usam esquemas de validação diferentes (`spatial_block_buffer` e
`spatial_block_buffer_loo`). A comparação por RMSE no registro é descritiva; não é uma decisão de
promoção. Comparações de promoção exigem o mesmo split congelado.

## 6. Próximos passos

1. Registrar também o baseline A0 GEDI como `retired`/referência histórica.
2. Adicionar hash do conjunto de features e do split congelado.
3. Implementar comparação automática com o champion e regra de promoção.
4. Integrar o registro ao comando `update` e ao relatório do produto.
