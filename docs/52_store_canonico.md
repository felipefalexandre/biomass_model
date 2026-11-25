# 52 — Store canônico idempotente de observações

**Data:** 2026-11-24 · **Status:** implementado; nenhum dado de campo apagado.

## 1. Objetivo

Materializar o ADR-0032: uma tabela canônica persistente, com ingestão idempotente e manifesto
de proveniência, para que novos inventários possam ser incorporados sem scripts ad hoc e sem
duplicação.

## 2. Estrutura

```text
E:\Mapbiomas\biomass\inventory_store\
  observations.csv     # tabela canônica
  manifest.json        # fontes, hashes, licenças, datas, contagens
  observations.lock    # lock transitório de escrita
```

O store usa CSV por simplicidade e portabilidade. Parquet/GeoParquet continua recomendado quando
`pyarrow` estiver disponível.

## 3. Regras

1. A chave de fonte é `source:source_version`.
2. A assinatura da fonte é o SHA-256 do arquivo ou, para diretório, de nomes+tamanhos+mtimes.
3. Se a assinatura não mudou, a ingestão é **skipped**.
4. Se mudou, as observações daquela fonte com o mesmo `observation_id` são substituídas.
5. Duplicatas de `observation_id` são resolvidas mantendo a última.
6. A escrita é protegida por lock (`O_CREAT|O_EXCL`), evitando perda de dados em execuções
   concorrentes.
7. O manifesto registra caminho, hash, licença, notas, linhas e data de ingestão.

## 4. Estado atual

`E:\Mapbiomas\biomass\inventory_store\observations.csv`:

| Fonte | Linhas |
|---|---:|
| IFN/SFB | 7.466 |
| PLOS 2018 | 77 |
| CEDA Manaus 2014 | 23 |
| ORNL SLB | 10 |
| **Total** | **7.576** |

Distribuição por bioma: Cerrado 2.614; Amazônia 1.970; Caatinga 1.744; Mata Atlântica 1.078;
Pampa 170. O store mantém biomas fora do domínio atual no catálogo; o treinamento filtra.

## 5. Comandos

```powershell
python -m biomass_model.cli inventory-store --source plos2018 `
  --path data\raw\inventarios\plos2018\s003.xlsx `
  --store E:\Mapbiomas\biomass\inventory_store

python -m biomass_model.cli inventory-store --source ceda `
  --path E:\Mapbiomas\biomass\fields\ceda_manaus\Manaus2014_Plots100x60m_AGB.shp `
  --store E:\Mapbiomas\biomass\inventory_store
```

## 6. Limitações

- A assinatura de diretório usa metadados (nome/tamanho/mtime), não hash de conteúdo.
- Duplicatas entre fontes diferentes com IDs distintos não são detectadas automaticamente; é
  necessário um teste de sobreposição espacial/inventário.
- CSV não é transacional em caso de falha de disco; o lock evita concorrência, não corrupção
  parcial. Migrar para Parquet com escrita atômica é recomendado.
- O store não substitui o catálogo de fontes nem o data card.

## 7. Próximos passos

1. Migrar para Parquet/GeoParquet com escrita atômica.
2. Detectar duplicatas entre repositórios do mesmo inventário.
3. Registrar hash de conteúdo por arquivo de fonte.
4. Integrar o store ao `update` e ao treinamento.
