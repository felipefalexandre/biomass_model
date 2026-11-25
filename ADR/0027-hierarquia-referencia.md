# ADR-0027 — Hierarquia de referência: campo primário, GEDI auxiliar

- **Data:** 2026-11-24
- **Status:** aceito (decisão do usuário)
- **Substitui parcialmente:** ADR-0003 (GEDI como referência principal)
- **Relaciona-se a:** ADR-0012, ADR-0015, ADR-0022

## Contexto

O sistema foi construído com GEDI L4A como alvo de treinamento. O GEDI L4A é um produto
modelado, com erro próprio, e não uma medição direta de AGB em campo. A validação independente
disponível é limitada a 42 sítios antigos do Cerrado (PLOS 2018). O novo escopo exige AGB real,
com referência de campo e GEDI apenas como camada auxiliar.

## Decisão

1. **Medições de campo são a referência primária** para treinamento, calibração e validação.
2. **LiDAR calibrado por campo** é referência estrutural secundária, com erro e suporte
   documentados.
3. **GEDI L4A** é referência auxiliar de calibração/avaliação e nunca verdade de campo. Seu erro
   (`agbd_se`/PI) deve ser registrado e, quando possível, usado como peso ou componente de
   incerteza.
4. **Produtos globais de AGB** são benchmark/comparação, nunca fonte de verdade nem validação
   independente do próprio produto.
5. O modelo/mapa GEDI-only atual passa a ser **baseline A0 experimental**. Ele não é o produto de
   AGB e seus artefatos são preservados para comparação e reprodutibilidade.
6. Nenhum modelo será promovido a produto operacional sem validação de campo independente.

## Consequências

- O treinamento principal deve incorporar inventários de campo.
- A calibração local deve ser feita com campo, não apenas com GEDI.
- Resultados anteriores continuam válidos como Linha A (fidelidade ao GEDI), não como acurácia
  de AGB real.
- A comunicação do produto deve declarar explicitamente a diferença entre medição, observação
  estrutural e estimativa modelada.

## Arquivos

`docs/46`, `docs/34`, `docs/38`, `data/reference/inventarios_abertos.md`.
