# ADR-0018 — Histórico MapBiomas como feature

- **Data:** 2026-11-18
- **Status:** aceito
- **Contexto:** o modelo não transferia entre regiões (ADR-0016). Faltava representar
  histórico de uso: floresta secundária em regeneração e savana com diferentes idades
  estruturalmente se parecem espectralmente, mas diferem em biomassa.
- **Decisão:** usar a série MapBiomas 2004–2018 (anterior aos footprints GEDI 2019–2024, sem
  vazamento) para derivar, por footprint: anos no domínio 3/4, anos como floresta (3), anos
  como savana (4), número de mudanças de classe, anos desde a última mudança e classe em
  2004/2010/2014/2018. Prefixo `mb_`.
- **Resultado (leave-one-box-out, 4 boxes/bioma):**

  | Bioma | Escala | Sem histórico | Com histórico |
  |---|---|---|---|
  | Amazônia | 30 m | R² 0,001 | 0,014 |
  | Amazônia | 1 km | −0,102 | **0,083** |
  | Cerrado | 30 m | −0,491 | **−0,017** |
  | Cerrado | 1 km | 0,240 | **0,290** |

  Com calibração local de 10%: Amazônia 0,16 → **0,25**; Cerrado 0,54 → **0,56**. Conformal
  com histórico: cobertura IC90 0,914 (Amazônia) e 0,89 (Cerrado).
- **Ressalvas:** o box florestal do Cerrado (MT) continua falhando (fold −3,3); o histórico não
  substitui calibração local; classes do MapBiomas têm erro próprio.
- **Consequências:** histórico passa a ser parte do conjunto de features recomendado
  (`train-table --history`); reprocessar tabelas ao mudar a coleção do MapBiomas.
- **Arquivos:** `src/biomass_model/features.py`, `docs/25`, `docs/33`, `docs/31`,
  `data/reference/baselines.csv`.
