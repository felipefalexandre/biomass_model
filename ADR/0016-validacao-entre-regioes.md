# ADR-0016 — Validação entre regiões e generalização

- **Data:** 2026-11-18
- **Status:** aceito
- **Contexto:** os baselines iniciais usavam um único box de ~17,8 km por bioma. A CV por
  blocos de 5 km dentro do box produziu R² 0,10 (Amazônia, footprint) e 0,29 (1 km), mas esse
  desenho não mede generalização espacial: blocos vizinhos compartilham clima, solo e histórico
  de perturbação.
- **Decisão:** adicionar boxes independentes por bioma e adotar **leave-one-box-out** como
  validação principal. Métricas agregadas de todos os boxes são descritivas; o critério de
  aceite (`docs/25`) é avaliado **por região/fold**.
- **Evidência:** com 3 boxes por bioma (Amazônia: central, leste/Tapajós, oeste/Acre; Cerrado:
  central, nordeste/MG, oeste/MT), o R² leave-one-box-out ficou negativo no footprint
  (Amazônia −0,18; Cerrado −0,56) e, em 1 km, −0,13 (Amazônia) e +0,42 agregado no Cerrado,
  mas com folds de 0,13/−0,25/−0,81. O R² agregado é inflado pela diferença de média entre
  boxes, não por habilidade dentro da região.
- **Consequências:**
  1. Nenhum modelo atual pode ser apresentado como produto nacional; são provas de conceito
     regionais.
  2. O relato deve separar R² agregado e R² por região, sempre com RMSE/viés por fold.
  3. Próximos caminhos: mais regiões de treino (5–10 por bioma), calibração regional,
     estratificação por classe/estrutura e referência de campo com melhor qualidade.
  4. O piloto único deixa de ser suficiente para decisões de acurácia; `docs/14` e `docs/24`
     devem orçar a expansão amostral.
- **Arquivos:** `docs/25`, `docs/31`, `docs/22` (RC13), `data/reference/baselines.csv`.
