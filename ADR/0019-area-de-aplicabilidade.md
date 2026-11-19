# ADR-0019 — Área de Aplicabilidade (AOA) obrigatória no produto

- **Data:** 2026-11-18
- **Status:** aceito
- **Contexto:** o modelo calibrado ainda erra em boxes cujas combinações de features não
  aparecem no treino (ex.: Acre e sul do Pará na Amazônia; savana do oeste baiano). Precisamos
  sinalizar onde a predição é extrapolação, em vez de entregar o número sem aviso.
- **Método:** distância euclidiana em features padronizadas pelo treino; limiar = quantil 95%
  da distância leave-one-out dos próprios pontos de treino (Meyer & Pebesma, 2021). Células
  acima do limiar ficam fora da AOA.
- **Resultado (1 km, calibração 10%):** Amazônia 86% dentro da AOA, com R² 0,48 dentro e 0,44
  no total; Cerrado 84% dentro, R² 0,72 dentro e 0,71 no total. A AOA não corrige a
  transferência (boxes Acre e Pará sul seguem negativos), mas identifica a extrapolação.
- **Decisão:** todo mapa de AGB deve trazer máscara AOA; células fora da AOA não recebem
  valor (ou recebem apenas com aviso explícito). O relatório de acurácia deve ser feito dentro
  da AOA, além do total.
- **Consequências:** cobertura espacial deixa de ser 100%; o produto passa a ter três classes:
  dentro da AOA, fora da AOA e fora do domínio MapBiomas 3/4. A calibração local deve priorizar
  áreas hoje fora da AOA.
- **Arquivos:** `src/biomass_model/modeling.py` (`run_region_aoa`), `docs/12`, `docs/25`,
  `docs/33`, `data/reference/baselines.csv`.
