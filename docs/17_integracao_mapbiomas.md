# 17 — Integração com MapBiomas e consultas por polígono

## 1. Por que MapBiomas é central

- Fornece uso e cobertura da terra anual, 30 m, série longa (1985–2024/2025 na coleção em uso).
- Permite estratificar, mascarar e definir o domínio de vegetação.
- Permite relatar biomassa por classe, bioma, município, UC, TI e imóvel.

## 2. Classes e domínio (Coleção 11)

| Grupo | Classes brutas | Uso |
|---|---|---|
| Floresta | **3 — Formação Florestal** | modelo Amazônia; estrato florestal do Cerrado |
| Savana | **4 — Formação Savânica** | modelo Cerrado |
| Fora da v1 | 5 (mangue), 6 (floresta alagável), 11/12 (campestres) | exclusão declarada |
| Antrópico | 9, 15, 18, 19, 20, 21, 24, 25, 30, 33... | máscara |
| Água | 26 | máscara |
| Não vegetação | 22, 23, 27, 29, 31, 32... | máscara |

**Regra de domínio (ADR-0010):**

```
dominio(t) = (classe_mapbiomas(t) == 3) | (classe_mapbiomas(t) == 4)
```

O domínio é recalculado **a cada ano**; a máscara de vegetação estável 2007–2016 da etapa anterior
não é o domínio, e sim um **estrato opcional** para comparação. Ver `docs/22` (RE01).

**Atenção:** os códigos 3/4 são os **códigos brutos** da legenda. O `ClassCode` do pipeline de
desmatamento (`rules.py`: 1 antrópico, 2 vegetação primária, 3 secundária, 4 supressão de
primária, 5 recuperação, 6 supressão de secundária, 7 outro) é uma camada **derivada** e não deve
ser confundido com a legenda bruta. A conversão precisa ser explícita e testada.

### 2.1 Pilotos selecionados

Seleção por cobertura do IFN (Painel de Biomassa e Carbono) e fração de classes 3/4:

| Bioma | Nome | lon | lat | janela | f3 | f4 | f3+4 | UAs IFN |
|---|---|---|---|---|---|---|---|---|
| Amazônia | piloto_amazonas_sul | −60,45 | −6,90 | 512 px | 0,933 | 0,000 | 0,933 | 511 |
| Cerrado | piloto_chapada_veadeiros | −47,70 | −13,95 | 512 px | 0,256 | 0,536 | 0,791 | 605 |

Arquivo: `data/reference/pilotos_selecionados.csv`; ferramenta:
`tools/suggest_pilots_from_ifn.py`.

## 3. Máscaras

| Máscara | Definição | Efeito |
|---|---|---|
| Domínio de vegetação | classes 3/4 no ano | define o que é estimado |
| Estrato estável (etapa anterior) | classe 3/4 em 2007–2016 | comparação com produtos anteriores; não é o domínio |
| Água/urbano/rocha | exclusão | evita AGBD espúria |
| Transição no ano | exclui pixel que mudou | evita mistura temporal |
| AOA | dissimilaridade de features | evita extrapolação |

Declarar sempre **qual** máscara foi aplicada; totais mudam materialmente com a máscara.

## 4. Consulta por polígono

### 4.1 Entrada

- Geometria (GeoJSON/GPKG), CRS declarado, validade topológica.
- Ano(s) de interesse.
- Tipo de saída: média de AGBD, total de AGB, total de C, CO₂e, distribuição.

### 4.2 Processamento

1. Reprojetar para a grade do mapa (ou usar estatística zonal com máscara).
2. Recortar por janela (bounding box) para eficiência.
3. Calcular:
   - `n_pixels` válidos, `area_ha`;
   - `agbd_media` ponderada por área de pixel;
   - `agb_total` = Σ AGBD × área_pixel;
   - IC propagado (não apenas erro do pixel médio).
4. Reportar fração dentro da AOA e fração mascarada.

### 4.3 Armadilhas

| Armadilha | Correção |
|---|---|
| média simples de pixels em EPSG:4326 | ponderar por área de pixel (latitude) |
| ignorar pixels nodata | reportar n e fração válida |
| polígono cruza bioma | relatar por bioma separadamente |
| polígono pequeno (< alguns pixels) | não estimar; sinalizar |
| borda do polígono | decidir regra (centro do pixel) e documentar |
| sobreposição de polígonos | não somar; unir ou deduplicar |
| ano sem cobertura | não interpolar silenciosamente |

## 5. Relato por domínio

Tabela padrão:

| domínio | área_ha | área_válida_ha | AGBD média (Mg ha⁻¹) | EP | IC90 | AGB total (Mg) | C (Mg C) | CO₂e (Mg) | % AOA |
|---|---|---|---|---|---|---|---|---|---|

Sempre incluir `% AOA`; uma estimativa com 40% fora da AOA não é comparável a uma com 98%.

## 6. Integração com os produtos de desmatamento

- A máscara de elegibilidade é um **estrato**, não o denominador universal; usá-la apenas quando
  a comparação com a etapa anterior for explícita.
- Para emissões, usar AGBD do ano anterior ao desmatamento.
- Não usar o mapa de biomassa para "corrigir" a área desmatada; são produtos independentes.

## 7. Critérios de aceite

- Consulta reprodutível (mesma geometria + versão ⇒ mesmo resultado).
- Unidade e máscara declaradas na saída.
- IC propagado corretamente.
- Fração fora da AOA explicitada.
- Testes de contrato com polígonos sintéticos (quadrado, borda, furo, multipolígono).
