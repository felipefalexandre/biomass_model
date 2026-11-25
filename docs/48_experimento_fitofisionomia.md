# 48 — Experimento: fitofisionomia IBGE como feature no modelo campo-first

**Data:** 2026-11-24 · **Status:** experimento concluído; hipótese não suportada.

## 1. Pergunta

A fitofisionomia IBGE 1:250.000, usada como variável categórica, melhora o modelo campo-first
F0 (PLOS 2018, Cerrado) em relação ao mesmo modelo sem essa variável?

Hipótese H1 de `docs/36`: a fisionomia reduz viés e melhora a transferência espacial.

## 2. Desenho

- Base: 40 sítios PLOS 2018 no domínio 3/4, com features Landsat/DEM/ERA5/histórico MapBiomas.
- Fitofisionomia: amostragem pontual do IBGE 2026 1:250.000, atributo `legenda_2`, usando
  interseção espacial; sem preenchimento por vizinho.
- Categorias entram como one-hot (`ibge_group`), junto com `fitofisionomia_group` e `bioma`.
- Validação primária: blocos de 200 km com buffer de 25 km.
- Sensibilidade: leave-one-block-out de 100 km com buffer de 25 km.
- Modelo: RandomForest 400 árvores, `min_samples_leaf=3`, mesmo split e seed.

## 3. Distribuição da fitofisionomia nos 40 sítios

| Classe IBGE (`legenda_2`) | Sítios | AGB média (Mg ha⁻¹) | AGB mediana |
|---|---:|---:|---:|
| Savana Arborizada | 17 | 26,6 | 27,5 |
| Savana Parque | 9 | 22,1 | 15,8 |
| Pecuária (pastagens) | 7 | 27,9 | 32,1 |
| Savana Gramíneo-Lenhosa | 2 | 31,5 | 31,5 |
| Savana Florestada | 2 | 29,9 | 29,9 |
| Agricultura | 1 | 4,8 | 4,8 |
| Contato (Ecótono) | 1 | 24,1 | 24,1 |
| Agropecuária | 1 | 37,0 | 37,0 |

Agrupando: **30 sítios `savanna`** e **10 sítios `unknown`** (pastagem, agricultura, água ou
contato). Não há sítios `forest` na amostra. A AGB média é 25,8 Mg ha⁻¹ no grupo `savanna` e
26,1 Mg ha⁻¹ no grupo `unknown`.

**Achado de qualidade:** 10 de 40 sítios (25%) caem em classes antrópicas/água no IBGE 1:250k,
apesar de o PLOS descrevê-los como Cerrado sensu stricto. Isso indica incompatibilidade de escala,
data ou legenda entre a referência de campo e o mapa IBGE.

## 4. Resultados

| Configuração | Validação | n OOF | R² | RMSE | MAE | Viés |
|---|---|---|---:|---:|---:|---:|
| F0 sem IBGE | bloco 200 km | 16 | 0,262 | 10,81 | 7,88 | −3,59 |
| F0 + `ibge_group` | bloco 200 km | 16 | 0,256 | 10,86 | 7,92 | −3,63 |
| F0 sem IBGE | LOO 100 km | 40 | 0,197 | 9,54 | 7,15 | +0,15 |
| F0 + `ibge_group` | LOO 100 km | 40 | 0,200 | 9,52 | 7,13 | +0,11 |

As diferenças são menores que a variabilidade entre folds. Não há ganho consistente.

## 5. Conclusão

- **H1 não é suportada** nesta amostra.
- A variável IBGE adiciona duas categorias efetivas (`savanna` e `unknown`), sem separar
  fisionomias com relações AGB distintas.
- A alta fração de sítios em classes antrópicas/água sugere que o IBGE 1:250k não é adequado
  para pareamento ponto a ponto com o PLOS sem uma etapa de reconciliação.
- A fitofisionomia continua sendo uma camada estrutural do sistema (ADR-0029), mas **não deve ser
  promovida como feature** com base neste experimento.
- O resultado é registrado como negativo; não houve promoção de modelo.

## 6. Artefatos

- Features com IBGE: `E:\Mapbiomas\biomass\derived\plos2018_features_landsat_ibge.csv`
- Modelo bloco 200 km: `E:\Mapbiomas\biomass\derived\field_plos2018_ibge_rf_block200.*`
- Modelo LOO 100 km: `E:\Mapbiomas\biomass\derived\field_plos2018_ibge_rf.*`

## 7. Próximos passos

1. Tentar reconciliação temporal/escala IBGE–MapBiomas–campo antes de reutilizar a variável.
2. Testar estratificação (não feature) em áreas com suporte amostral suficiente.
3. Avaliar `legenda_1` e atributos estruturais (altura/cobertura) como alternativas.
4. Aumentar a amostra de campo e incluir fitofisionomias florestais.
5. Não usar esta variável em produção enquanto o pareamento não for validado.
