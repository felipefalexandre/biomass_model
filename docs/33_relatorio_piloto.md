# 33 — Relatório do piloto (AGB, 2019–2024)

**Data:** 2026-11-18 · **Status:** prova de conceito, sem produto nacional · **Código:** `main`
(`a43de70` ou posterior)

## 1. Objetivo

Testar, com dados abertos e ferramentas gratuitas, se é viável estimar AGBD em 30 m e 1 km na
Amazônia e no Cerrado usando GEDI L4A como referência, Sentinel-2/Sentinel-1/Landsat, DEM e
ERA5-Land, com validação espacialmente honesta. O piloto não busca acurácia final; busca
descobrir onde estão os gargalos e quanto custa resolvê-los.

## 2. Dados e área

Oito boxes de ~17,8 km (±0,08°), quatro por bioma, escolhidos para cobrir gradientes
(ADR-0014/0016):

| Bioma | Box | Lon, Lat | Footprints no domínio | Mediana AGB (Mg ha⁻¹) |
|---|---|---|---|---|
| Amazônia | central | −60,45, −6,90 | 19.879 | 186 |
| Amazônia | leste (Tapajós) | −54,95, −3,15 | 14.618 | 146 |
| Amazônia | oeste (Acre) | −67,30, −9,40 | 6.101 | 175 |
| Amazônia | norte (Manaus) | −60,00, −2,50 | 24.847 | 177 |
| Cerrado | central | −47,70, −13,95 | 14.420 | 6,5 |
| Cerrado | nordeste (MG) | −45,30, −16,70 | 10.800 | 7,6 |
| Cerrado | oeste (MT) | −52,20, −12,80 | 6.182 | 83 |
| Cerrado | sul (SP) | −48,45, −22,85 | 4.404 | 53 |

- GEDI L4A V2.1 (2019–2024), filtro `l2=1, l4=1, agbd≥0, 0,9≤sensibilidade≤1,01` (ADR-0012).
- S2 L2A composto (mediana de até 25 datas, máscara SCL), 10 m; S1 RTC (8 datas, 2024) testado
  em um box; Landsat C2 L2 (mediana ±45 dias) para os inventários antigos.
- DEM GLO-30 e ERA5-Land mensal (2018–2025).
- Domínio: classes 3/4 do MapBiomas Coleção 11 no ano (ADR-0010); clima usa climatologia
  2019–2024 como covariável espacial.

## 3. Protocolo de validação

1. **Dentro do box:** blocos espaciais de ~5 km (GroupKFold), que ainda permitem
   autocorrelação entre blocos vizinhos.
2. **Entre regiões (ADR-0016):** leave-one-box-out — treina em N−1 boxes e testa no box retido.
   Métrica principal: R²/RMSE **por box**. R² agregado é descritivo, não critério.
3. **Calibração local (ADR-0017):** adiciona uma fração do box retido ao treino e testa no
   restante.
4. **Campo:** PLOS 2018 (Cerrado) pareado ao Landsat da data do inventário; 42 sítios no
   domínio.

## 4. Resultados principais

### 4.1 Dentro do box (otimista)

| Modelo | Escala | R² | RMSE |
|---|---|---|---|
| S2 uma data (Amazônia central) | 30 m | 0,097 | 92,4 |
| S2 composto 10 datas | 30 m | 0,094 | 92,5 |
| S2 composto + S1 (8 datas) | 30 m | 0,098 | 92,3 |
| S2 composto | 1 km | 0,285 | 34,3 |
| S2 composto + S1 | 1 km | 0,289 | 34,2 |
| Campo Cerrado + Landsat na data | 1 km | 0,288 | 8,9 |

S2 multi-data e S1 não mudam o jogo; agregar para 1 km reduz o erro absoluto, mas parte do
ganho é redução de variância do alvo.

### 4.2 Entre regiões (honesto)

| Bioma | Escala | R² agregado | R² por fold |
|---|---|---|---|
| Amazônia | 30 m | 0,001 | 0,01 / −0,07 / 0,06 / −0,12 |
| Amazônia | 1 km | −0,10 | 0,17 / −0,61 / −0,19 / −0,21 |
| Cerrado | 30 m | −0,49 | −1,52 / 0,02 / −3,14 / 0,10 |
| Cerrado | 1 km | 0,24 | 0,19 / −1,34 / −0,20 / −0,38 |

**O R² intra-box era sobretudo autocorrelação espacial.** O modelo não transfere entre regiões,
especialmente para o box florestal do Cerrado (MT, mediana 83) e para a Amazônia central.

### 4.3 Calibração local (o achado operacional)

| Células de calibração (1 km) | Amazônia R² | Cerrado R² |
|---|---|---|
| 0 | −0,10 | 0,24 |
| 5 | 0,11 | 0,51 |
| 25 | 0,15 | 0,55 |
| 50 | 0,21 | 0,60 |
| 100 (aleatórias) | **0,25** | **0,66** |
| 100 (compactas no centro) | 0,04 | 0,45 |

Recomendação: ~100 células **espalhadas** na Amazônia (≈100 km² de referência) e ≥25 no
Cerrado; amostras concentradas não funcionam na Amazônia. A calibração usou GEDI (mesma fonte
do teste), então o ganho pode estar otimista; o ideal é campo independente.

### 4.4 Incerteza (split conformal, 1 km)

Com calibração e conjunto conformal de 10% cada, a cobertura do IC90 foi 0,884 (Amazônia) e
0,901 (Cerrado), dentro da faixa 80–95%, mas com largura média de 134 e 76 Mg ha⁻¹. O intervalo
é honesto: o modelo calibrado acerta a cobertura, mas a incerteza é grande.

### 4.5 Cerrado com 6 boxes: representação de fisionomia

Adicionar um segundo box de floresta estacional (MT, 31.707 footprints, mediana 79) e um de
savana aberta (BA, 4.913, mediana 2,8) mudou o quadro do Cerrado:

| Configuração | Escala | R² | Observação |
|---|---|---|---|
| 4 boxes, histórico | 1 km | 0,29 | fold floresta −3,3 |
| 6 boxes, histórico | 1 km | 0,56 | fold floresta ~0; boxes pequenos falham |
| 6 boxes + 10% calibração | 1 km | **0,73** | todos os boxes positivos (0,07–0,44) |
| 6 boxes + conformal | 1 km | 0,71 | cobertura 0,888; largura 58 |

O gargalo do Cerrado era representação de fisionomia, não apenas calibração. A Amazônia
segue mais difícil (saturação em AGB alta e heterogeneidade).

### 4.6 Amazônia com 5 boxes: gradiente e extrapolação

O quinto box (sul do Pará/MT, mediana 107) preenche o gradiente que faltava (146–186). Sem
calibração, o LOO piora (−0,09 em 1 km) porque o box de menor biomassa é extrapolação e chega a
−20 no fold. Com 10% de calibração local, R² 0,39 em 1 km (0,25 com 4 boxes) e conformal 0,43
(cobertura 0,892; largura 119). O box do Acre ainda falha com calibração (−0,13).

### 4.7 Diagnóstico dos folds que falham

Decompondo o erro por box (1 km, sem calibração):

| Box | Viés (Mg ha⁻¹) | R² após remover viés | Inclinação obs~pred |
|---|---|---|---|
| Amazônia central | −24,8 | 0,07 | 0,92 |
| Amazônia leste | −14,9 | 0,23 | 0,97 |
| Amazônia norte | −18,4 | 0,13 | 1,53 |
| Amazônia oeste | −7,1 | 0,15 | 1,01 |
| Amazônia sul | **+78,2** | −0,31 | 0,17 |
| Cerrado central | +7,8 | 0,20 | 0,63 |
| Cerrado floresta | −16,8 | −0,01 | 0,13 |
| Cerrado nordeste | −2,6 | 0,24 | 0,93 |
| Cerrado noroeste | +5,3 | 0,22 | 1,05 |
| Cerrado oeste | −25,1 | −0,05 | −0,31 |
| Cerrado sul | −9,6 | 0,06 | 1,03 |

A falha é sobretudo **deslocamento de nível e compressão** (inclinações de 0,13 a 1,53), não
apenas ruído: o modelo aprende a média de outras regiões. Isso explica por que a calibração
local (que reancora o nível) funciona e por que a correção linear simples não basta (a
inclinação também muda).

### 4.8 Referência de campo e tempo

- Os inventários do PLOS 2018 são de 1988–2014. A validação anterior com S2 de 2024 era
  temporalmente inválida (R² 0,328); com Landsat na data, R² 0,288 / RMSE 8,9 / 42 sítios.
- GEDI L4A subestima savana aberta (mediana 6,2 contra 19,4 do IFN no piloto central), o que
  motivou ADR-0015 (campo primeiro no Cerrado).

## 5. Limitações

- Referência GEDI ruidosa e enviesada por região/estrutura; sensibilidade e `degrade_flag`
  não são usáveis como features (não existem na predição).
- Domínio 3/4 exclui formações campestres (RC12) e 30 dos 75 sítios de campo do Cerrado.
- Calibração e teste compartilham a mesma referência (GEDI); falta validação independente.
- Clima é climatologia recente, não condição do ano do inventário.
- Nenhum box cobre bordas, várzeas, queimadas recentes ou gradientes altitudinais extremos.
- Modelo global único não é adequado; sem calibração local o erro é inaceitável.

## 6. Decisões registradas

ADR-0012 (filtro GEDI), 0013 (grade/amostragem), 0014 (escala do piloto), 0015 (campo no
Cerrado), 0016 (validação entre regiões), 0017 (calibração local obrigatória).

## 7. Próximos passos priorizados

| Prioridade | Ação | Custo/observação |
|---|---|---|
| 1 | Expandir para 6–10 boxes por bioma, cobrindo bordas e gradientes | ~1 dia de download/processamento por lote |
| 2 | Coletar/obter referência de campo independente (RAINFOR, ORNL, IFN) | requer curadoria e allometria |
| 3 | Protocolo de calibração local: ~100 células espalhadas (Amazônia), ≥25 (Cerrado) | define custo de MRV |
| 4 | Incerteza: RF quantílico/conformal + AOA, com cobertura IC90 por região | depende de modelo calibrado |
| 5 | BGB como modelo separado solo/clima (Spawn 2020, SoilGrids) | sem referência direta; declarar limites |
| 6 | Relatório de produto: mapa + máscara de domínio + IC + model card | só após 1–3 |

## 8. Reprodutibilidade

- Comandos: `docs/32`; credenciais fora do repositório; manifestos em `data/manifests/`.
- Tabelas e métricas: `E:\Mapbiomas\biomass\derived\*` (não versionadas); resumos em
  `data/reference/baselines.csv`.
- Testes: `python -m pytest` (23 passando).
