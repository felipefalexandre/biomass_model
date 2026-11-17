# 01 — Escopo e estimandos

## 1. Definição formal

Um **estimando** (estimand) é a quantidade populacional que se deseja estimar, definida antes de
qualquer modelagem. Sem essa definição, não é possível escolher estimador, calcular variância nem
validar.

### 1.1 População

- **Domínio geográfico:** biomas Amazônia e Cerrado, conforme limites oficiais do IBGE
  (`lm_bioma_250`, EPSG:4674).
- **Domínio ecológico:** formações vegetais lenhosas — floresta ombrófila, floresta estacional,
  campinarana, savana (Cerrado *sensu lato*), savana arborizada, campo sujo com componente
  lenhoso. Exclui: água, área urbana, agricultura, pastagem, solo exposto, mineração, rocha.
- **Unidade amostral elementar:** pixel de 30 m (grade de referência comum, EPSG:4326 ou
  projeção métrica de área igual).
- **Unidade de relato:** polígono (imóvel, município, UC, TI, bioma) ou célula de grade.
- **Referência temporal:** ano civil; estado da vegetação em 31/12 (ou data de imageamento
  declarada, conforme disponibilidade).

### 1.2 Quantidades

| Símbolo | Nome | Unidade | Definição |
|---|---|---|---|
| AGBD | densidade de biomassa acima do solo | Mg ha⁻¹ (matéria seca) | massa seca de toda a vegetação lenhosa viva acima do solo por hectare |
| AGB | biomassa acima do solo total | Mg | ∫ AGBD dA no domínio |
| BGBD | densidade de biomassa abaixo do solo | Mg ha⁻¹ | massa seca de raízes (diâmetro ≥ 2 mm, conforme protocolo) |
| BGB | biomassa abaixo do solo total | Mg | ∫ BGBD dA |
| TB | biomassa total | Mg | AGB + BGB |
| C | carbono | Mg C | f_C × TB |
| CO₂e | equivalente de CO₂ | Mg CO₂e | C × 44/12 |

**Não confundir:** Mg de biomassa ≠ Mg C ≠ Mg CO₂e. Ver `docs/11`.

### 1.3 Estimandos primários

Para cada combinação (bioma b, ano t, classe de vegetação c):

1. **AGBD média** μ(b, t, c) em Mg ha⁻¹.
2. **AGB total** T(b, t, c) em Mg.
3. **TB total** em Mg.
4. **C total** em Mg C.
5. **CO₂e total** em Mg CO₂e.

### 1.4 Estimandos secundários

6. Mudança ΔAGB entre anos (estoque e fluxo).
7. Biomassa removida/emitida por desmatamento (integração com a série 2014–2025 já produzida).
8. AGBD por polígono de interesse (consulta), com incerteza.
9. Distribuição (não só média): quantis de AGBD por domínio.

### 1.5 Suporte e mudança de suporte

O modelo prediz em suporte de pixel (30 m). A estimativa de área usa **mudança de suporte**
explícita:

- média de pixel → média de célula → média de domínio;
- a variância de uma média de área **não** é a média das variâncias de pixel; requer covariância
  espacial (ver `docs/12`).

## 2. Fronteiras explícitas

### 2.1 Incluído

- vegetação lenhosa viva acima e abaixo do solo;
- árvores mortas em pé apenas se o protocolo de referência as incluir (GEDI L4A não as separa
  explicitamente → registrar limitação);
- palmeiras e bambus conforme equações de referência.

### 2.2 Excluído (e por quê)

| Excluído | Motivo |
|---|---|
| necromassa caída | não observável pelas features previstas; exige campo |
| serapilheira | idem |
| carbono do solo (SOC) | domínio distinto; exige modelo próprio (SoilGrids é opção, mas fora do escopo) |
| vegetação herbácea | não é o alvo; AGBD de sensoriamento é dominada por lenhosas |
| biomassa de raízes finas < 2 mm | protocolo; incerteza alta |

### 2.3 Ambiguidades a resolver com o usuário

- ano-base e cadência (ver `docs/30`, Q3);
- se "biomassa" inclui BGB por padrão ou é opcional (Q4);
- se o relato é por bioma, por classe MapBiomas ou por polígono (Q9, Q10);
- se mudança temporal é obrigatória (Q11).

## 3. Unidades e convenções

- Massa em **Mg** (megagrama = tonelada), sempre matéria seca a 65 °C quando derivada de campo;
  produtos de sensoriamento declaram a convenção da fonte.
- Área em **ha**; área de pixel calculada por latitude (`row_pixel_area_m2`, já implementado no
  repositório de desmatamento) para evitar distorção em EPSG:4326.
- Carbono: fração f_C explícita (padrão IPCC 0,47, a confirmar por estrato — `docs/11`).
- CO₂e: apenas CO₂ (não incluir CH₄/N₂O salvo pedido explícito).
- Incerteza: intervalo de 90% por padrão; reportar também erro padrão.

## 4. Critério de "conclusão" de uma estimativa

Uma estimativa só é publicável se:

1. o estimando estiver definido (esta seção);
2. o estimador e sua variância estiverem especificados (`docs/12`);
3. houver validação independente (`docs/13`);
4. a proveniência dos dados estiver registrada (`docs/19`);
5. as limitações estiverem declaradas (`docs/22`).
