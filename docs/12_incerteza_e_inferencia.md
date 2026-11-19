# 12 — Incerteza e inferência

## 1. Três paradigmas

### 1.1 Design-based (baseado no desenho)

A população é fixa; a aleatoriedade vem da amostragem. A estimativa é não enviesada para o
estimador escolhido, e a variância vem do desenho (estratos, clusters, probabilidades desiguais).

- Requer: amostra probabilística, probabilidades de inclusão conhecidas.
- Não requer: modelo correto.
- Problema: dados de sensoriamento (GEDI) **não** são amostra probabilística da biomassa.

### 1.2 Model-based (baseado no modelo)

A população é realizada, mas desconhecida; o modelo define a distribuição. A inferência depende
da validade do modelo.

- Requer: modelo plausível e validação.
- Problema: intervalos otimistas se o modelo estiver mal especificado ou extrapolar.

### 1.3 Híbrida (recomendada)

Combina um modelo (para toda a população) com uma amostra de referência (para corrigir viés e
quantificar incerteza). É a abordagem de Ståhl et al. (2016).

```
μ̂_híbrida = (1/N) Σ_i ŷ_i  +  correção_baseada_na_amostra
```

Dependendo da variante:

- **Híbrida clássica:** resíduos da amostra corrigem a predição; variância inclui termo de
  amostragem + termo de modelo.
- **Híbrida com modelo tratado como estimado:** variância inclui incerteza dos parâmetros do
  modelo (bootstrap).
- **Quasi-design:** quando a amostra não é probabilística (GEDI), usa-se o desenho aproximado e
  declara-se que a inferência é condicional ao modelo de amostragem.

## 2. O que este projeto adota

1. **Estimador principal:** híbrido com dois componentes de variância.
2. **Componente de amostragem:** bootstrap por blocos espaciais (preserva autocorrelação).
3. **Componente de modelo:** bootstrap dos parâmetros/reamostragem de treino + variabilidade
   entre algoritmos (ensemble), quando aplicável.
4. **Componente de referência:** propagação do erro de GEDI L4A (se disponível na documentação)
   ou cenários (baixo/central/alto).
5. **Declaração de limitação:** a amostra GEDI não é probabilística; a inferência é
   **quasi-design/model-assisted**, e isso deve constar em todo relatório.

## 3. Decomposição de variância

```
Var(μ̂) = Var_amostragem + Var_modelo + Var_referência + 2·Cov(...)
```

Na prática:

- Estimar `Var_modelo` por bootstrap do treino (reajustar o modelo B vezes).
- Estimar `Var_amostragem` por bootstrap espacial da referência.
- Estimar `Var_referência` por cenários ou pela incerteza reportada de GEDI.
- Reportar o **peso relativo** de cada componente; isso orienta onde investir (mais campo?
  melhor modelo? melhor referência?).

## 4. Autocorrelação espacial

- Dados próximos são parecidos; tratar como independentes subestima a variância.
- Medidas: semivariograma, Moran's I, distância de decorrelação.
- Consequências:
  - CV aleatório superestima desempenho (Roberts 2017; Ploton 2020).
  - Bootstrap ingênuo subestima a variância.
- Soluções:
  - blocos espaciais (ex.: 50–100 km) para CV e bootstrap;
  - NNDM-LOO (Milà et al. 2022) quando o objetivo é validar mapa;
  - modelo de variância com covariância espacial para áreas pequenas.

## 5. Área de aplicabilidade (AOA)

- Calcular dissimilaridade de features de cada pixel em relação ao treino (ex.: distância no
  espaço de variáveis, com limiar derivado do erro de CV — Meyer & Pebesma 2021).
- Marcar pixels fora da AOA; **não** estimar neles sem sinalização.
- Relatar a fração da área dentro da AOA por domínio.

## 6. Intervalos e cobertura

- Reportar IC 90% (padrão) e erro padrão.
- Verificar **cobertura empírica** do IC em validação (não apenas nominal).
- Se a cobertura for < nominal, o IC é otimista: inflar ou rever o modelo de erro.

## 7. Erros de interpretação a evitar

| Erro | Correção |
|---|---|
| "RMSE do mapa = incerteza da estimativa total" | são coisas diferentes; usar decomposição |
| "IC 90% = ±1,64 × RMSE" | não, se houver autocorrelação e erro de modelo |
| "bootstrap de pixels" | pixels não são independentes; usar blocos |
| "GEDI é amostra aleatória" | não é; declarar quasi-design |
| "modelo com R² alto é confiável" | R² em CV aleatório engana; usar CV espacial |

## 8. Entregáveis de incerteza

1. Tabela por domínio: estimativa, EP, IC 90%, n, fração na AOA.
2. Decomposição de variância por domínio.
3. Mapa de desvio-padrão e mapa de AOA.
4. Relatório de cobertura empírica dos ICs.
5. Lista de suposições e o que aconteceria se forem violadas (análise de sensibilidade).

## Incerteza no piloto (2026-11-18)

Implementado split conformal em `modeling.run_region_conformal` (CLI `region-conformal`):
calibração (10%) treina, conjunto conformal (10%) estima o quantil dos resíduos e o restante
testa. Em 1 km, com calibração local:

| Bioma | R² | RMSE | Cobertura IC90 | Largura média |
|---|---|---|---|---|
| Amazônia | 0,16 | 48,2 | 0,884 | 134 Mg ha⁻¹ |
| Cerrado | 0,49 | 28,2 | 0,901 | 76 Mg ha⁻¹ |

A cobertura nominal é atingida, mas os intervalos são largos — consequência direta da
transferência imperfeita entre regiões. Calibração e conjuntos conformais vêm da mesma
referência GEDI; com campo independente, a largura tende a aumentar.
