# 54 — Reconciliação IBGE 1:250.000 × MapBiomas (Cerrado central 2021)

**Data:** 2026-11-24 · **Status:** diagnóstico concluído; correspondência não é direta.

## 1. Objetivo

Quantificar a discordância entre a fitofisionomia IBGE 1:250.000 (`legenda_2`) e as classes
3/4 do MapBiomas no box Cerrado central 2021, antes de usar a fitofisionomia como filtro,
estrato ou feature.

## 2. Dados e método

- **Fitofisionomia:** `derived\fitofisionomia_cerrado_central_2021_30m.tif` (IBGE 2026,
  reamostrada para 30 m).
- **MapBiomas:** `E:\Mapbiomas\mapbiomas_col11_2021.tif`, reprojetado para a grade da
  fitofisionomia por vizinho mais próximo.
- **Domínio:** pixels com MapBiomas 3 ou 4.
- **Área:** pixel de 30 m (0,09 ha).
- **Comando:** `python -m biomass_model.cli fitofisionomia-reconcile ...`

## 3. Resultado

Área total no domínio 3/4: **20.287,53 ha** (225.417 pixels).

### Por grupo fitofisionômico IBGE

| Grupo | Área (ha) | Fração |
|---|---:|---:|
| Savanna | 17.798,04 | 87,73% |
| Antropogênico (pastagem) | 2.489,49 | 12,27% |

### Por classe MapBiomas

| Classe | Área (ha) | Fração |
|---|---:|---:|
| 4 — Formação Savânica | 13.540,14 | 66,74% |
| 3 — Formação Florestal | 6.747,39 | 33,26% |

### Detalhe por classe IBGE

| Classe IBGE | Grupo | Área total (ha) |
|---|---|---:|
| Pecuária (pastagens) | anthropogenic | 2.489,49 |
| Savana Arborizada | savanna | 16.268,76 |
| Savana Parque | savanna | 1.529,28 |

## 4. Leitura

- **12,27% da área MapBiomas 3/4 é classificada como pastagem pelo IBGE 1:250k.** Isso não é
  ruído desprezível: é uma discordância estrutural entre “cobertura atual” (MapBiomas) e
  “vegetação mapeada” (IBGE).
- A correspondência “3/4 = vegetação natural” não é direta; a fitofisionomia IBGE não deve ser
  usada como filtro rígido sem uma etapa de reconciliação.
- O filtro de grupos do Produto C (`forest,savanna,campestre`) remove essa área explicitamente,
  mas o mapa A0 continua estimando AGB nela porque sua máscara é MapBiomas 3/4.
- A classe “Pecuária” deve ser tratada como **não vegetação natural** ou revisada com dados
  atuais; não assumir que é Cerrado só porque o MapBiomas a colocou em 3/4.

## 5. Consequências para o sistema

1. A fitofisionomia permanece camada estrutural, não filtro automático.
2. O Produto C deve declarar a fonte e o filtro de grupos usados.
3. O treinamento/validação por fitofisionomia deve excluir ou isolar classes antrópicas/água.
4. A máscara final do produto precisa combinar MapBiomas 3/4 **e** uma decisão explícita sobre
   fitofisionomia não vegetacional.
5. A reconciliação deve ser repetida para a Amazônia e para outros anos/boxes.

## 6. Artefatos

- `E:\Mapbiomas\biomass\derived\fitofisionomia_vs_mapbiomas_cerrado_central_2021.csv`
- JSON de códigos reclassificado:
  `E:\Mapbiomas\biomass\derived\fitofisionomia_cerrado_central_2021.json`

## 7. Próximos passos

1. Repetir para Amazônia central e demais boxes.
2. Definir uma regra explícita de elegibilidade fitofisionômica (grupos permitidos).
3. Avaliar se a área “pastagem IBGE” deve ser excluída do mapa A0.
4. Incorporar a regra ao model card e ao Produto C.
