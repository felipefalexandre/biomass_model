# 03 — Revisão metodológica

Este documento resume as famílias de métodos relevantes, seus pressupostos, vantagens e falhas
conhecidas. Ele fundamenta as escolhas de `docs/07` e a matriz de `docs/04`. Não é uma revisão
exaustiva da literatura; é uma revisão **orientada a decisão**.

## 1. Allometria e dados destrutivos

**Ideia:** estimar biomassa individual a partir de variáveis dendrométricas (DAP, altura, densidade
da madeira) por equações ajustadas em árvores abatidas e pesadas.

- Equações pantropicais clássicas: Chave et al. (2005, *Oecologia*), com forma
  AGB = f(ρ, D, H) e versões sem altura; Chave et al. (2014, *GCB*) com modelo de 4 e 5
  parâmetros, incluindo um termo ambiental (E).
- Densidade da madeira: base global de Chave et al. (2009, *Ecology Letters*) e o repositório de
  Zanne et al. (2009, Dryad).
- Cerrado: equações específicas e dados destrutivos de Ribeiro et al. (2011, *For. Ecol. Manage.*),
  que reportam AGB média de 62.965,5 kg ha⁻¹ (SE 14,6%) e BGB de 37.501,8 kg ha⁻¹ (SE 23%) em
  cerrado *sensu stricto* no sudeste, com razão raiz/parte aérea dentro da faixa de savanas.
  Miranda et al. (2014, *Biotropica*) sintetizam equações e variação entre fisionomias.

**Forças:** base física direta; permite separar componentes (fuste, galhos, folhas, raízes).
**Limitações:** amostras pequenas e localizadas; extrapolação geográfica arriscada; equações
pantropicais erram mais em savanas e em árvores fora da faixa de diâmetro; altura difícil de medir.

**Uso no projeto:** fornecer a **referência de campo** e as **equações de BGB**; calibrar/validar
quando houver parcelas; nunca extrapolar uma equação local para o bioma inteiro sem verificação.

## 2. Inventário florestal e amostragem por desenho

**Ideia:** a biomassa é uma característica populacional; estima-se por amostragem probabilística,
com variância derivada do desenho (stratified, cluster, two-stage).

- Referência metodológica: Ståhl et al. (2016, *Forest Ecosystems*), que formaliza estimadores
  *design-based* e *model-based* e a combinação híbrida.
- No Brasil: IFN (SFB) e inventários estaduais; acesso e granularidade a confirmar (`docs/30`).

**Forças:** inferência válida sem modelo; intervalos de confiança honestos.
**Limitações:** custo; amostras pequenas para domínios finos; não produz mapa.

**Uso:** define o **estimador de referência** para áreas com dados de campo e o alvo de
comparação para a abordagem assistida por modelo.

## 3. Sensoriamento óptico

**Ideia:** reflectância (bandas, índices de vegetação, textura, séries temporais) correlaciona-se
com estrutura e fração de cobertura.

- Sentinel-2 MSI (10–20 m) e Landsat 8/9 OLI (30 m) são a espinha dorsal gratuita.
- Índices usuais: NDVI, EVI, SAVI, NDII, NBR; métricas de textura e fenologia.
- Problema clássico de **saturação** em AGB alta (>150–200 Mg ha⁻¹), exatamente na Amazônia.

**Forças:** cobertura, resolução, série histórica, custo zero.
**Limitações:** saturação, sensibilidade a nuvem/sombra, sensível a sub-bosque e composição.

## 4. Radar

**Ideia:** micro-ondas penetram nuvens e respondem a estrutura (troncos, dossel) e umidade.

- Sentinel-1 C-band (gratuito) é sensível a estrutura de dossel e a mudanças, com saturação
  relativamente cedo em C-band; polarizações VV/VH e razões ajudam.
- L-band (ALOS PALSAR, histórico) satura mais tarde, mas disponibilidade contínua é limitada.

**Forças:** independe de nuvem; útil na Amazônia e em épocas chuvosas.
**Limitações:** saturação, ruído speckle, geometria de aquisição, difícil em vegetação baixa.

## 5. LiDAR espacial

**Ideia:** medir estrutura vertical diretamente (perfil de dossel).

- GEDI (ISS, 2019–2023; dados disponíveis): footprints ~25 m, cobertura entre ~51,6°N e S,
  amostragem em trilhas; produtos L4A (AGBD por footprint) e L4B (agregado em grade).
  Referências: Dubayah et al. (2020, *Sci. Remote Sens.*), Duncanson et al. (2022, *RSE*).
- ICESat-2 ATL08: altura de dossel e métricas ao longo de trilhas, com beam pattern distinto.

**Forças:** observação direta de estrutura; menos saturação; referência para treinar modelos.
**Limitações críticas:** L4A/L4B são **produtos de modelo** (não medição direta de biomassa),
com erro dependente de PFT/região e pior desempenho em alta AGB e em dados esparsos; cobertura
é amostral, não wall-to-wall; geolocalização e inclinação de terreno introduzem erro; a missão
GEDI terminou a aquisição científica em 2023 (status e continuidade a confirmar).

**Uso:** referência principal para treinar o mapa, com todas as ressalvas acima.

## 6. Produtos globais de biomassa

- Saatchi et al. (2011, *PNAS*), Baccini et al. (2012, *Nature Climate Change*): mapas
  pantropicais baseados em inventário + sensoriamento.
- Avitabile et al. (2016, *GCB*): fusão de múltiplos mapas pan-tropicais com dados de referência.
- Santoro et al. (2021, *ESSD*): CCI Biomass 2010, 100 m, baseado em observações de satélite.
- Spawn et al. (2020, *Scientific Data*): mapas harmonizados de carbono de AGB e BGB (2010).

**Forças:** cobertura global, comparação e *benchmarking*.
**Limitações:** divergem entre si; resolução grosseira; não substituem estimativa local; erros
estruturais em Cerrado e em florestas secundárias.

**Uso:** **benchmark**, nunca "verdade". Comparar distribuições e mapas de diferença.

## 7. Aprendizado de máquina

**Famílias:** regressão linear/GLM (interpretável), Random Forest, gradient boosting (XGBoost,
LightGBM), k-NN, redes neurais (CNN/PointNet para séries e nuvens), Gaussian processes (custo alto).

**Forças:** capturam não linearidade e interações; bom desempenho preditivo.
**Limitações:** overfitting espacial; extrapolação silenciosa; pouca interpretabilidade;
importância de variável não é causalidade; dependência de dados de treino enviesados.

**Decisão:** começar simples (baseline linear/GLM + RF), adicionar complexidade só se a validação
espacial justificar (`docs/25`).

## 8. Inferência híbrida

**Ideia (Ståhl et al. 2016):** combinar (i) uma amostra probabilística de referência com
(ii) um modelo que prevê para toda a população. A variância tem dois componentes:
erro de amostragem da referência e erro do modelo.

Forma conceitual (para uma média populacional):

```
μ̂ = (1/N) Σ_{i∈U} ŷ_i                      (parte modelo, wall-to-wall)
   ajustada por resíduos observados na amostra S (parte desenho)
Var(μ̂) ≈ Var_desenho(resíduos) + Var_modelo
```

A forma exata depende de o modelo ser tratado como fixo ou estimado; ver `docs/12`.

**Forças:** aproveita dados amostrais e cobertura total; permite IC honesto.
**Limitações:** exige suposições sobre o mecanismo de amostragem; se a referência não é
probabilística (ex.: GEDI com amostragem sistemática e filtros de qualidade), a inferência é
**model-based/quasi-design**, não design-based puro. Isso precisa ser declarado.

## 9. Validação espacial e área de aplicabilidade

- Roberts et al. (2017, *Ecography*): CV com estrutura espacial/temporal/hierárquica.
- Ploton et al. (2020, *Nature Communications*): validação espacial revela desempenho pobre de
  mapas ecológicos em escala ampla — argumento central contra k-fold aleatório.
- Meyer & Pebesma (2021, *MEE*): *area of applicability* (AOA) por dissimilaridade de features,
  com limiar derivado do erro de CV.
- Milà et al. (2022, *MEE*): NNDM-LOO CV, que iguala a distribuição de distâncias
  treino–teste à distribuição predição–treino.

**Decisão:** usar CV por blocos espaciais **e** AOA; reportar métricas dentro e fora da AOA.

## 10. Lacunas metodológicas conhecidas

1. **BGB** não é observável por satélite; depende de equações e razões, com incerteza alta no
   Cerrado (fogo, solo, sazonalidade).
2. **Biomassa muito baixa** (<20 Mg ha⁻¹) é mal estimada por óptico e por GEDI.
3. **Florestas secundárias** têm trajetórias rápidas e composição distinta; modelos treinados em
   primária erram.
4. **Degradação** (fogo, extração seletiva, borda) é sutil e frequentemente invisível ao óptico.
5. **Mudança temporal** exige consistência radiométrica entre sensores/anos.
6. **Incerteza de referência** raramente é propagada; a maioria dos mapas a ignora.
