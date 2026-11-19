# 35 — Auditoria científica e diagnóstico (pré-implementação)

**Data:** 2026-11-18 · **Escopo:** auditoria do sistema atual, sem alterar modelos ou resultados.
**Pergunta-guia:** o sistema atual consegue estimar o estoque de biomassa de **um ano** a partir de
dados de satélite desse ano, atualizar o estoque e reagir a mudanças reais — sem depender de GEDI
ou de outro mapa no momento da estimativa?

**Resposta curta:** não. O sistema atual é um espacializador estático de GEDI (compósito
2020–2024), adequado como prova de conceito, mas incapaz de representar a dinâmica anual. A
arquitetura precisa de uma camada temporal explícita.

## 1. O que o código faz hoje

| Item | Implementação atual | Evidência |
|---|---|---|
| Alvo | `agbd` do GEDI L4A V2.1 (Mg ha⁻¹), por footprint de 25 m | `datasets/gedi.py`, `features.py` |
| Filtro GEDI | `l2=1`, `l4=1`, `agbd≥0`, `0,9≤sensibilidade≤1,01`; `degrade_flag` mantido, não filtrado | ADR-0012 |
| Incerteza GEDI | `agbd_se`, `agbd_pi_lower/upper` são baixados e mantidos na tabela, mas **não usados** em peso, métrica ou intervalo | `features.py` |
| Covariáveis | S2 (6 bandas + NDVI/NDMI/NIRv), DEM, ERA5, histórico MapBiomas 2004–2018; S1 opcional | `features.py` |
| Janela temporal S2 | **um compósito único 2020–2024** (mediana de até 25 datas) para todos os footprints, inclusive de 2019 | `s2-composite`; ver §3 |
| Classe MapBiomas | classe do **ano do footprint** (correto) | `build_training_table` |
| Agregação | 1 km = média de features e do alvo (≥3 footprints) | `modeling.aggregate_cells` |
| Validação espacial | leave-one-box-out (4–5 boxes Amazônia; 6 Cerrado) | ADR-0016 |
| Calibração | 10% das células do box retido entram no treino; teste no restante | ADR-0017 |
| Incerteza | split conformal (10% calibração, 10% conformal) | `run_region_conformal` |
| AOA | distância em features padronizadas; limiar q95 da distância LOO do treino | ADR-0019 |
| Produto | nenhum mapa anual; apenas métricas por célula de boxes | `docs/33` |

## 2. Independência entre treino, calibração e avaliação

- **Treino × teste (espacial):** correto. O box retido não entra no ajuste, exceto pela amostra
  de calibração, que é explicitamente separada do teste (`run_region_cv` usa `shuffled[:k]` para
  calibração e `shuffled[k:]` para teste).
- **Conformal:** correto. Calibração, conjunto conformal e teste são disjuntos
  (`run_region_conformal`).
- **AOA:** o limiar vem de distâncias LOO do treino; a calibração local entra no treino e,
  portanto, na distribuição de referência. Isso é aceitável, mas deve ser declarado.
- **Limite conceitual:** calibração e teste usam a **mesma referência GEDI**. Não é validação
  independente; é transferência dentro do produto GEDI. A única referência de campo (PLOS 2018)
  não foi usada no treino, mas é antiga e cobre só o Cerrado.

## 3. Achados que limitam o objetivo anual

1. **Compósito multi-ano estático.** As features S2 são uma mediana de 2020–2024. Um footprint de
   2019 e outro de 2023 recebem a mesma reflectância (ou quase), apagando mudanças anuais. O
   modelo não pode, por construção, reagir a desmatamento, fogo ou regeneração de um ano
   específico.
2. **Alvo não anualizado.** GEDI L4A existe de 2019 a 2023/2024, com cobertura orbital desigual.
   Não há como treinar um modelo anual para anos sem GEDI usando apenas GEDI; será preciso
   campo e/ou pseudo-invariância.
3. **Incerteza GEDI ignorada.** O erro de modelo do L4A (mediana de `agbd_se` ≈ 13 Mg ha⁻¹;
   ~3 em savana baixa) não entra na estimativa nem nos intervalos. A incerteza reportada
   subestima a incerteza total.
4. **Pseudo-replicação espacial.** Cada box tem 4,4–31,7 mil footprints, mas apenas 16–25 blocos
   de 5 km. O número efetivo de observações independentes é ordens de magnitude menor.
5. **Representatividade desigual.** A fração de área fora do domínio 3/4 chega a 56% (Acre) e
   90% (Cerrado sul); os footprints, porém, são quase todos 3/4. Ou seja, a amostra é de
   remanescentes, não da paisagem. Isso afeta a extrapolação para mosaicos agropecuários.
6. **Domínio anual mutável.** Usar a classe 3/4 do ano como máscara faz áreas desmatadas
   “desaparecerem” do mapa, em vez de aparecerem como perda de estoque. Para contabilidade de
   estoque, é preciso um módulo de transições (perda/ganho), não apenas máscara.
7. **Falta de validação temporal.** Nenhum experimento atual mede se o modelo responde
   corretamente a uma mudança conhecida (PRODES, MapBiomas, fogo) ou se permanece estável em
   áreas sem mudança.
8. **Uso de GEDI no inference.** Hoje o GEDI é alvo, não feature; isso é compatível com “não
   depender de GEDI para estimar”. Mas o produto atual **é** uma espacialização de GEDI e não um
   estimador autônomo; a diferença precisa ser explicitada no model card e nos critérios.

## 4. Matriz dos 11 boxes (dados reais)

Fonte: `data/reference/matriz_boxes.csv` (gerado nesta auditoria).

| Box | n fp | Mediana AGB | Q10–Q90 | % área 3/4 | Blocos 5 km | Datas | AOA |
|---|---|---|---|---|---|---|---|
| Amazônia central | 19.879 | 195,8 | 84,9–319,3 | 87,7% | 25 | 42 | 0,96 |
| Amazônia leste | 14.618 | 145,9 | 36,6–327,6 | 60,1% | 20 | 22 | 0,57 |
| Amazônia oeste | 6.101 | 175,0 | 60,8–331,3 | 43,7% | 20 | 17 | 0,72 |
| Amazônia norte | 24.847 | 177,5 | 61,7–303,5 | 97,0% | 25 | 19 | 0,99 |
| Amazônia sul | 20.690 | 106,9 | 56,4–160,0 | 77,8% | 20 | 30 | 0,99 |
| Cerrado central | 14.420 | 6,5 | 0,2–57,5 | 70,5% | 16 | 31 | 0,88 |
| Cerrado nordeste | 10.800 | 7,6 | 2,3–25,3 | 68,2% | 16 | 28 | 0,67 |
| Cerrado oeste | 6.182 | 83,0 | 21,5–134,1 | 21,7% | 20 | 27 | 0,85 |
| Cerrado sul | 4.404 | 52,6 | 2,7–179,8 | 10,2% | 16 | 28 | 0,83 |
| Cerrado noroeste | 4.913 | 2,8 | 0,0–12,0 | 21,7% | 16 | 23 | 0,81 |
| Cerrado floresta | 31.707 | 78,6 | 18,9–169,0 | 87,7% | 20 | 33 | 0,99 |

Leituras:
- A Amazônia não tem box abaixo de ~107 Mg ha⁻¹; a cauda baixa é extrapolação.
- O Cerrado tem dois regimes (2,8–7,6 e 52–83) com vazio entre ~25 e ~50.
- O Cerrado sul é 90% não-domínio na área, mas 99,6% dos footprints são classe 3: amostra de
  remanescentes.
- AOA < 0,75 em Amazônia leste (0,57) e Cerrado nordeste (0,67) indica combinações de features
  pouco representadas já **dentro** dos boxes.

## 5. Auditoria da referência de campo (PLOS 2018)

Fonte: `data/reference/plos2018_auditoria.csv`.

- 77 sítios no arquivo; 75 no bioma Cerrado (2 fora: Amazônia e Caatinga).
- 50 têm inventário entre 2004–2014 e janela Landsat; 42 caem no domínio 3/4.
- 25 sítios são anteriores a 2004 (MapBiomas local começa em 2004) — recuperáveis se obtivermos
  anos anteriores do MapBiomas.
- 8 sítios de 2004–2014 estão fora do domínio (formações campestres/antrópicas).
- **Viés de seleção:** os 42 usados têm mediana 24,2 Mg ha⁻¹ (Q10–Q90 12,9–37,0); os 33 não
  usados têm 18,8 (10,7–27,5). O domínio exclui a cauda baixa, justamente onde GEDI mais erra.
- O R² 0,29 (Landsat na data) é a única linha B existente e não foi usado para treinar.

## 6. Auditoria do ORNL Sustainable Landscapes Brazil (viabilidade)

- DOI 10.3334/ORNLDAAC/2007; 93 arquivos, 31 CSV de inventário; 2009–2018.
- Desenho: *diameter-dependent line sampling* com fator 10, 5 transectos de 500 m, árvores ≥5 cm
  (Hunter et al. 2013, DOI 10.5194/bg-10-8385-2013; Schreuder et al. 1987).
- **Teste de viabilidade (TAP_A01, 2009):** somando `AGB_i/(2·L·w_i)` com `w=DBH/10` e Chave 2005,
  obtive 386–396 Mg ha⁻¹ para 2009–2011. É alto para Tapajós e sugere que a convenção do fator
  ou o datum das coordenadas UTM está errado (SAD69 vs WGS84 desloca dezenas de metros).
- **Conclusão:** a recuperação é metodologicamente possível (estimador de Horvitz–Thompson para
  amostragem linear), mas **não está pronta**: faltam (i) confirmar a convenção exata do fator
  (largura de inclusão = DBH/10, DBH/20 ou outra), (ii) confirmar datum/zona dos UTM, (iii)
  tratar palmeiras, lianas e árvores mortas, (iv) usar alturas medidas ou equações locais.
- O LiDAR ORNL (DOI 10.3334/ORNLDAAC/1644, 117 GB) é uma referência estrutural independente em
  potencial, mas não substitui inventário para AGB.

## 7. Auditoria do GEDI como referência

- L4A é **modelo**, não medição; erro depende de PFT, região e estrutura. Em savanas, a
  literatura recente mostra subestimação (Li et al. 2024, DOI 10.1016/j.srs.2024.100161; no
  Cerrado, nossa mediana 6,2 vs 19,4 do IFN).
- O filtro de sensibilidade ≥0,9 pode excluir sistematicamente vegetação aberta; não foi testada
  a sensibilidade dos resultados a esse limiar.
- `degrade_flag` tem distribuição desigual por box (fração `degrade_zero` 0,62–0,90), mas não é
  usado como filtro nem como peso.
- A agregação para 1 km reduz ruído, mas também apaga gradientes locais e mudanças.

## 8. Conclusão da auditoria

O sistema é reproduzível, testado e honesto nos resultados, mas responde à pergunta errada para o
objetivo atual: ele **espacializa um compósito GEDI multi-ano**; não **estima o estoque de um
ano** nem **atualiza** o estoque. As mudanças necessárias são de desenho, não de hiperparâmetro:

1. features e máscaras **por ano**;
2. modelo com **estado temporal** (estoque e mudança), não um único ajuste estático;
3. validação **temporal e de mudança**, além da espacial;
4. referência GEDI usada **somente para calibrar**, com auditoria de independência no inference;
5. contabilidade explícita de transições (perda/ganho), não apenas máscara 3/4.

Esses pontos estruturam o plano em `docs/37`.
