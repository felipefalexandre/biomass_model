# 41 — Dois produtos: mapa espacial vs estimativa por estrato/polígono

**Data:** 2026-11-18 · **Status:** estudo de viabilidade concluído; decisão proposta.
**Pergunta:** gerar um mapa e recortar, ou estimar direto por estrato/polígono?

## 1. O que é “classe 3/4” e o que é fitofisionomia

A legenda oficial da Coleção 11 (documento “Descrição das classes”, ago/2026) define:

- **3 = Formação Florestal** (nível 2, dentro de Floresta): agrega, na Amazônia, Floresta Ombrófila
  Densa, Ombrófila Aberta, Estacional Sempre-Verde, Estacional Semidecidual, Estacional Decidual,
  campinarana, floresta de bambu e floresta secundária; no Cerrado, cerradão, mata de galeria e
  mata ciliar.
- **4 = Formação Savânica**: agrega savana arborizada, savana parque, cerrado denso/típico/ralo/
  rupestre, entre outras.
- **6 = Floresta Alagável** (nova classe da Coleção 11) **não** está em 3; **2 = Formação
  Campestre** (campo sujo/limpo) **não** está em 4.

Portanto: **3/4 são filtro espacial e classes agregadas, não fitofisionomias.** O mapa do MapBiomas
não separa, por pixel, ombrófila densa de aberta, nem cerrado típico de rupestre. Para estimar por
fitofisionomia é preciso uma fonte adicional (IBGE 1:250.000, MapBiomas Vegetação Secundária,
estrutura derivada de satélite) ou a composição fornecida pelo usuário. O crosswalk inicial está em
`data/reference/fitofisionomias_crosswalk.csv` (faixas indicativas, a calibrar).

Consequência para o desenho: o domínio 3/4 define **onde** o produto é válido; a fitofisionomia
define **como** a biomassa se relaciona com as covariáveis. São camadas distintas.

## 2. Duas arquiteturas

### A. Mapa primeiro (wall-to-wall)

1. Estimar AGBD por célula (1 km oficial; 30 m diagnóstico) para o ano.
2. Aplicar máscara de domínio (3/4), AOA e incerteza.
3. Para um polígono, recortar e agregar (média ponderada por área), com block bootstrap.

**Prós:** responde qualquer polígono; mostra onde está a biomassa; permite comparar com mapas de
desmatamento (sobreposição externa; o modelo não estima perda); a composição pode vir do mapa;
incerteza espacialmente explícita.
**Contras:** exige inferência em toda a área (custo computacional); depende de o modelo ser válido
em todos os pixels (AOA); risco de precisão aparente em 30 m; erros espacialmente correlacionados.

### B. Estrato primeiro (polygon-only)

1. Usuário fornece polígono + composição por fitofisionomia (%).
2. Modelo/priors fornecem AGBD médio por estrato (local ou literatura).
3. Estoque = Σ (área_i × AGBD_i); incerteza por composição + médias.

**Prós:** barato e rápido; não precisa mapear pixels; direto para relatório; robusto a ruído de
pixel; fácil de auditar por estrato.
**Contras:** não localiza padrões nem permite sobreposição espacial; depende de composição confiável;
AGBD por estrato transferido de outra região enviesa o total; não valida padrões espaciais; não
gera mapa.

### C. Híbrido (recomendado)

Mapa como produto principal; tabela por polígono derivada por zonal stats; composição do usuário
entra como **entrada opcional/restrição** (checagem de consistência e relatório por estrato). Se o
usuário só tem composição, o sistema pode rodar em “modo polígono” usando médias locais
calibradas, com aviso de que não há mapa nem verificação espacial.

## 3. Teste de viabilidade com dados reais

Predições LOO de 1 km no Cerrado (6 boxes). “Mapa” = média das células; “estrato” = composição
local × médias de classe **transferidas de outros boxes**; referência = média GEDI das células.

| Polígono | Células | AGBD obs. | Mapa | Viés mapa | Estrato (médias locais) | Estrato (médias transferidas) | Viés estrato |
|---|---|---|---|---|---|---|---|
| Cerrado central | 329 | 22,5 | 30,4 | +34,7% | 30,4 | 29,6 | +31,4% |
| Cerrado floresta | 346 | 91,4 | 74,6 | −18,4% | 74,6 | 54,0 | **−40,9%** |
| Cerrado nordeste | 330 | 14,1 | 11,4 | −18,8% | 11,4 | 20,2 | **+43,1%** |

Composição e médias por classe (Mg ha⁻¹):

| Polígono | % classe 3 | % classe 4 | Média 3 local | Média 3 transferida | Média 4 local | Média 4 transferida |
|---|---|---|---|---|---|---|
| Central | 35,9 | 64,1 | 52,8 | 63,6 | 17,8 | 10,6 |
| Floresta | 99,4 | 0,6 | 74,6 | 54,2 | 66,3 | 12,6 |
| Nordeste | 10,9 | 89,1 | 23,5 | 63,8 | 9,9 | 14,8 |

Leitura:
- O mapa já tem viés (LOO não calibrado), mas o **estrato com médias transferidas é pior e instável**
  (−41% a +43%), porque a mesma classe 3 vale 52,8 no central e 74,6 na floresta, e as médias de
  outros boxes não representam o polígono.
- “Estrato com médias locais” é idêntico ao mapa por construção; a diferença não está na
  agregação, mas em **de onde vêm as médias por estrato**.
- Block bootstrap no polígono central: IC90 do total ≈ ±6,7% (com correlação espacial), mas isso
  cobre apenas erro de amostragem das células, não o viés de modelo/referência.

## 4. Fórmulas: onde elas entram

- **Alometria** (Chave 2005/2014, equações locais) estima AGB de **árvores/parcelas** a partir de
  D, H, ρ. Não se aplica a pixels.
- **Modelo espacial** estima AGBD de **células** a partir de satélite/clima/solo.
- **Estrato** é uma camada intermediária: AGBD média por fitofisionomia, estimada por campo,
  modelo ou literatura, com incerteza e domínio de validade. Serve como prior/restrição e como
  camada de relatório; não substitui o mapa onde há variação espacial.

Para “fórmulas para todas as fitofisionomias”, o entregável realista é uma **tabela de priors por
estrato** (média, faixa, fonte, validade), calibrada com campo; o crosswalk já lista as
fitofisionomias e faixas indicativas. Sem campo/IBGE, a granularidade fina não é identificável.

## 5. Recomendação

1. **Mapa primeiro** (1 km oficial; 30 m diagnóstico) com IC, AOA e máscara 3/4. É o produto que
   sustenta REDD+/ARR: estoque e insumo para sobreposição com mapas externos de atividade.
2. **Tabela por polígono derivada** (área, média, estoque, IC, por estrato), usando composição do
   mapa ou do usuário. É o produto de relatório, não uma arquitetura alternativa.
3. **Modo polígono** apenas como atalho de relatório: exige médias por estrato **locais/
   calibradas**; nunca usar médias de outro bioma/região sem aviso. Sem mapa, não há análise de
   verificação espacial nem sobreposição com atividade.
4. **Não** aplicar alometria de árvore a pixel.
5. Para fitofisionomias finas: cruzar IBGE 1:250k + MapBiomas secundária + estrutura; se a
   composição vier do usuário, registrar a fonte e a incerteza.

**Decisão de continuidade:** o plano aprovado (mapa anual de biomassa, GEDI só calibração,
Linhas A/B/T) permanece. A sugestão de estimar por estrato/polígono entra como **camada de
relatório e checagem**, não como substituta do mapa. Ver ADR-0026.

## 6. Implicações de implementação

- `src/biomass_model/polygon.py` + CLI `polygon-stats`: agregação com block bootstrap e por classe
  (já implementado nesta etapa).
- Produto futuro: `inference/annual_map.py` gera COG por ano; `polygon-stats` recorta; a tabela
  por estrato usa `fitofisionomias_crosswalk.csv`.
- Entrada de composição do usuário: CSV `polygon_id, fitofisionomia, percentual` (validar soma
  100%, incerteza opcional).
- Decisão pendente: incluir **classe 6 (Floresta Alagável)** e **2 (Campestre)** no produto? Hoje
  ficam fora do domínio 3/4.

## 7. Riscos

- Estrato primeiro pode parecer mais barato, mas transfere viés regional sem deixar rastro visual.
- Mapa primeiro pode dar falsa confiança em 30 m; manter 1 km como oficial.
- Composição do usuário pode ser incompatível com o mapa; usar como checagem, não para forçar
  o mapa a bater.
