# 31 — Diário de pesquisa

Registro cronológico do que foi feito, decidido e descoberto. Complementa os ADRs (decisões) e
`docs/30` (pendências).

## 2026-11-17 — Sessão 1

### Decisões recebidas do usuário

1. Piloto: um tile pequeno por bioma, escolhido por nós, desde que tenha biomassa real.
2. Anos: intervalo de anos, preferencialmente recentes, para comparar com inventários, bases
   abertas e artigos.
3. Começar por AGB; BGB como modelo separado, focado em solo, acoplado (não derivado).
4. Dados e intermediários em `E:\Mapbiomas\biomass`.
5. Domínio: classes 3 e 4 do MapBiomas, Amazônia e Cerrado; estratificação por vegetação é
   desejável.
6. Referência obrigatória: legenda MapBiomas Coleção 11 e códigos IBGE de vegetação.
7. Inventários: buscar dados abertos e armazenar em pasta de referência.
8. Dúvidas não respondidas: seguir o padrão dos docs/ADRs.

### O que foi feito

- Download da legenda oficial Coleção 11 (PDF + texto extraído).
- Download do Painel de Biomassa e Carbono do SFB (IFN): `biomassa.csv` (53 MB, 439.970
  registros), `equacoes.csv`, `metadados.pdf`.
- Download dos suplementos S3–S5 do artigo de Cerrado (PLOS ONE 2018, DOI
  10.1371/journal.pone.0196742).
- Criação de `data/reference/inventarios_abertos.md` e `.csv` (10 fontes catalogadas).
- Ferramenta `tools/suggest_pilots_from_ifn.py`: cruza adensamento do IFN com fração de classes
  3/4 do MapBiomas.
- Seleção dos pilotos:
  - Amazônia: lon −60,45, lat −6,90; 512 px; 93,3% classe 3; 511 UAs do IFN na célula.
  - Cerrado: lon −47,70, lat −13,95; 512 px; 79,1% classes 3+4 (25,6% + 53,6%); 605 UAs.
- Scaffolding: `pyproject.toml`, `src/biomass_model/grid.py`, `tests/test_grid.py` (5 testes
  passando), `tools/select_pilots.py`.

### Achados

- O painel do SFB é aberto e tem coordenadas (~0,1°) e AGB por unidade amostral — serve para
  validação regional, não para pareamento pixel a pixel.
- Estatísticas calculadas por nós no CSV do SFB: Amazônia 151,6 Mg ha⁻¹ (média) / 112,0
  (mediana); Cerrado 33,9 / 19,4. A diferença média–mediana mostra distribuição assimétrica;
  não usar a média como "valor do bioma".
- O cluster do IFN em −60,45/−6,90 tem alta fração de floresta e muitas UAs; é melhor piloto
  amazônico do que Belterra, que não tinha UA do IFN em 50 km.
- A legenda confirma 3 = Formação Florestal e 4 = Formação Savânica; a distribuição empírica
  confirma (3 domina a Amazônia; 4 domina o Cerrado).

### Pendências geradas

- Baixar (ou obter via login gratuito) os inventários INV03–INV10.
- Harmonizar equações e DAP mínimo antes de qualquer validação.
- Definir o recorte temporal do piloto (ex.: 2018–2025) e a referência GEDI correspondente.
- Confirmar licença exata do MapBiomas e decidir licença dos produtos.

### Próximo passo

Fase 1: montar o cubo de features (S2, S1, DEM, clima) e extrair GEDI L4A nos dois tiles,
com validação espacial por blocos desde o início.
