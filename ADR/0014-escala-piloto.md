# ADR-0014 — Escala do piloto: caixa de ~17 km por bioma

**Status:** aceito
**Data:** 2026-11-17

## Contexto

O piloto precisa ser pequeno o bastante para iterar em horas e grande o bastante para conter
variabilidade de biomassa e footprints GEDI suficientes. As ferramentas anteriores usavam 512 px
(~5 km) na seleção e 1600 px (~16 km) na aquisição, o que ficou inconsistente.

## Decisão

- **Caixa do piloto:** ±0,08° (~17,8 km de lado) em torno do ponto escolhido.
- **Sentinel-2:** janela de 1600 px a 10 m (~16 km), compatível com a caixa.
- **DEM:** `--half 0.08`, mesma caixa.
- **ERA5-Land:** caixa com `pad 0.1°` (mínimo para conter a célula de 0,1°).
- **GEDI:** mesmo bbox `±0,08°` do ponto, para que treino e features cubram exatamente o piloto.
- A seleção de pilotos (`tools/suggest_pilots_from_ifn.py`) continua em 512 px para varredura
  rápida; a caixa definitiva é a de 17 km.

## Consequências

- Área de ~289 km² por piloto; com S2 1600² e grade de 30 m (~570² pixels), há pixels suficientes
  para um baseline, mas a amostra GEDI ainda é a restrição real.
- Inconsistência anterior (512 vs 1600 px) resolvida e documentada.
- Expansão futura é por justaposição de caixas, sem mudar o código.

## Evidência

- `data/reference/pilotos_selecionados.csv`; `docs/32`; artefatos em `E:\Mapbiomas\biomass\pilots`.
