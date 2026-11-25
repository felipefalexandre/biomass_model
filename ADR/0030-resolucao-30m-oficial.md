# ADR-0030 — Resolução: 30 m oficial, 1 km experimental

- **Data:** 2026-11-24
- **Status:** aceito (decisão do usuário)
- **Substitui parcialmente:** ADR-0026 (1 km oficial/30 m diagnóstico)

## Contexto

O piloto adotou 1 km como escala oficial e 30 m como diagnóstico, principalmente por
descasamento de suporte e por extrapolação em 30 m. O usuário decidiu priorizar 30 m como escala
oficial para permitir testes mais rápidos e maior detalhe espacial, mantendo 1 km como
experimental.

## Decisão

1. **30 m** é a resolução oficial do produto.
2. **1 km** é resolução experimental/diagnóstica, útil para testes rápidos, comparação e
   agregação.
3. A escolha não dispensa:
   - documentar o suporte espacial das observações de referência;
   - avaliar AOA e extrapolação em 30 m;
   - reportar IC e cobertura empírica em 30 m;
   - testar 100, 250 e 500 m como candidatos;
   - evitar confundir resolução nominal com acurácia.
4. Se a validação em 30 m não sustentar o produto, a decisão será revista em novo ADR, sem
   apagar resultados anteriores.

## Consequências

- O pipeline de inferência deve ser chunked e eficiente em 30 m.
- A agregação por polígono deve operar em 30 m com área real de interseção.
- A documentação e os model cards devem declarar 1 km como experimental.
- O mapa de 30 m só será chamado de produto após validação independente e gates MRV.

## Arquivos

`docs/45`, `docs/46`, `src/biomass_model/inference/map.py`, `ADR/0026-produto-mapa-primeiro.md`.
