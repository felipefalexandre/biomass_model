# 34 — Model card: AGB 1 km (piloto)

**Versão:** 2026-11-18 · **Status:** piloto calibrado, não é produto nacional · **Código:** `main`

## 1. O que é

Random Forest (400 árvores, `min_samples_leaf=3`) para densidade de biomassa acima do solo
(AGB, Mg ha⁻¹) em células de 1 km, treinado com GEDI L4A V2.1 (2019–2024) e features
ópticas/topográficas/climáticas/históricas. Dois modelos separados: Amazônia e Cerrado.

## 2. Dados de treino

| Bioma | Boxes | Footprints no domínio | Células de 1 km | Mediana AGB |
|---|---|---|---|---|
| Amazônia | 5 (central, Tapajós, Acre, Manaus, sul PA/MT) | 86.135 | 1.471 | 107–186 |
| Cerrado | 6 (central, MG, MT, SP, BA, floresta MT) | 72.426 | 1.786 | 2,8–83 |

- Referência: GEDI L4A, filtro `l2=1, l4=1, agbd≥0, 0,9≤sensibilidade≤1,01` (ADR-0012).
- Domínio: classes 3/4 do MapBiomas no ano (ADR-0010); 2020–2024.
- Features (35): 6 bandas S2 + NDVI/NDMI/NIRv (composto de até 25 datas), elevação/declividade/
  aspecto (GLO-30), 8 variáveis ERA5-Land (clima), 9 de histórico MapBiomas 2004–2018 (ADR-0018).
- 1 km = média das features dos footprints e média do alvo (≥3 footprints).

## 3. Desempenho (leave-one-box-out)

| Bioma | Sem calibração (1 km) | 10% calibração | Conformal IC90 | AOA |
|---|---|---|---|---|
| Amazônia | R² −0,09 | **0,39** (RMSE 44,9) | cobertura 0,89; largura 119 | 86% dentro; R² 0,48 |
| Cerrado | R² 0,56* | **0,73** (RMSE 22,8) | cobertura 0,89; largura 58 | 84% dentro; R² 0,72 |

\* agregado enganoso: folds de −1,08 a 0,20; só após calibração todos ficam positivos no
Cerrado. Na Amazônia, Acre e sul do Pará permanecem difíceis mesmo calibrados.

## 4. Uso pretendido

- Pesquisa aplicada e triagem de MRV **regional**, com calibração local e validação independente.
- Comparação relativa entre áreas dentro da mesma região calibrada.
- Base para mapas anuais, desde que a AOA e a incerteza acompanhem cada célula.

## 5. Fora de escopo

- Mapa nacional sem calibração por região.
- Créditos de carbono, compensação ou compliance sem validação de campo independente.
- Classes fora de 3/4 (campo, pastagem, agricultura), AGB > 300 Mg ha⁻¹, várzeas, manguezais.
- Afirmações em 30 m: o produto defensável é 1 km; 30 m é diagnóstico.
- Áreas fora da AOA.

## 6. Protocolo de calibração (obrigatório)

1. Treinar com todos os boxes disponíveis.
2. Coletar referência local espalhada: ~100 células de 1 km na Amazônia, ≥25 no Cerrado
   (ADR-0017 + adendo). Amostras concentradas não servem na Amazônia.
3. Retreinar incluindo a amostra local; **não** usar apenas correção linear (rejeitada).
4. Reportar R²/RMSE/viés no restante da amostra local e cobertura do IC90.
5. Aplicar máscara AOA e máscara de domínio MapBiomas.

## 7. Incerteza

Split conformal (10% calibração, 10% conformal). A cobertura nominal de 90% é atingida, mas a
largura é grande (58–142 Mg ha⁻¹), refletindo a transferência imperfeita. Intervalos devem ser
reportados por célula, não apenas a média.

## 8. Limitações e riscos

- GEDI é modelo, não verdade; viés conhecido em savana aberta (ADR-0015).
- Calibração e teste compartilham GEDI; falta validação de campo independente.
- Clima é climatologia 2019–2024, não condição do ano do inventário.
- Boxes cobrem ~17,8 km cada; não representam bordas, fogo recente ou gradientes extremos.
- Mudanças de coleção do MapBiomas exigem reprocessar histórico e revalidar.

## 9. Manutenção

- Retreinar ao atualizar MapBiomas, GEDI ou S2.
- Versionar features, tabelas e métricas; manifestos em `data/manifests/`.
- Revisar AOA e calibração a cada nova região.
- Licenças: código MIT; dados conforme `docs/32`; produto derivado a definir (`docs/21`).
