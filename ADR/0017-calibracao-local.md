# ADR-0017 — Calibração local obrigatória por região

- **Data:** 2026-11-18
- **Status:** aceito
- **Contexto:** o leave-one-box-out (ADR-0016) mostrou que o modelo treinado em outras regiões
  não transfere (R² ≈ 0 ou negativo em 1 km). Ao mesmo tempo, as regiões têm médias e
  distribuições de AGB muito diferentes (Amazônia 108–186; Cerrado 6–83 Mg ha⁻¹).
- **Teste:** `run_region_cv` reserva cada box, treina nos demais e adiciona uma fração de
  células do box retido como calibração local.
- **Resultado (1 km, 4 boxes/bioma):**

  | Bioma | sem calibração | 10% aleatório | 25% aleatório | 10% em faixa contígua |
  |---|---|---|---|---|
  | Amazônia | R² −0,10 | **0,16** | 0,21 | 0,11 |
  | Cerrado | R² 0,24 | **0,54** | 0,62 | 0,52 |

  A calibração aleatória de ~24–35 células (≈25–35 km² de referência GEDI) já recupera a maior
  parte do sinal. A faixa contígua é pior na Amazônia (0,11), indicando que a amostra local
  precisa cobrir a variabilidade da região, não um canto dela.
- **Decisão:** nenhum mapa será entregue sem calibração local. O protocolo operacional é:
  1. treinar o modelo multi-região;
  2. coletar referência local (GEDI e/ou campo) em ~10% da área ou ≥30 células de 1 km,
     distribuídas na região;
  3. recalibrar/retreinar e reportar acurácia na parte não usada da calibração.
- **Ressalvas:** (i) a calibração usou a mesma referência GEDI do teste, o que pode inflar o
  ganho; (ii) a validação ideal é com campo independente; (iii) o número de células deve ser
  revisto por bioma/estrato.
- **Consequências:** o produto é regionalmente calibrado, não global; o custo de campo/MRV
  passa a incluir ~30 células por região; `docs/14` e `docs/24` devem prever isso.
- **Arquivos:** `src/biomass_model/modeling.py` (`run_region_cv`), `docs/25`, `docs/31`,
  `data/reference/baselines.csv`.

## Adendo (2026-11-18): tamanho e geometria da amostra

Varredura de células de calibração (1 km, 4 boxes/bioma, amostra aleatória):

| Células | Amazônia R² | Cerrado R² |
|---|---|---|
| 0 | −0,10 | 0,24 |
| 5 | 0,11 | 0,51 |
| 10 | 0,05 | 0,52 |
| 25 | 0,15 | 0,55 |
| 50 | 0,21 | 0,60 |
| 100 | **0,25** | **0,66** |

Calibração **compacta** (100 células no centro do box): Amazônia 0,04; Cerrado 0,45. Ou seja,
o ganho depende de a amostra cobrir a variabilidade espacial, não de estar concentrada.
Recomendação revista: ~100 células espalhadas na Amazônia e ≥25 no Cerrado; amostras
compactas não são aceitáveis na Amazônia.
