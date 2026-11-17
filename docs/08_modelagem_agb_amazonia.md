# 08 — Modelagem de AGB na Amazônia

## 1. Por que a Amazônia exige tratamento próprio

- Faixa de AGBD muito alta: de ~30 Mg ha⁻¹ (campinarana/campo) a >300 Mg ha⁻¹ em florestas de
  terra firme densas.
- Forte **saturação** de índices ópticos e de radar C-band nas faixas altas.
- **Nuvem** persistente: composições sazonais e radar são indispensáveis.
- Heterogeneidade edáfica e topográfica: solos pobres em areia (campinarana) vs argilosos;
  relevo do escudo das Guianas vs planícies.
- Presença de **várzea/igapó** (inundação sazonal), que altera reflectância e estrutura.
- **Florestas secundárias** em regeneração, com trajetória rápida e composição distinta.
- **Degradação** por fogo e extração seletiva, sutil no óptico.

## 2. Estratégia

### 2.1 Unidades de modelagem

Modelo principal por **sub-região ecológica** (não por estado), com agrupamento mínimo:

1. Escudo das Guianas / norte (Roraima, Amapá, norte do Pará/Amazonas).
2. Amazônia central e ocidental (terra firme).
3. Arco do desmatamento (sul/sudeste: Mato Grosso, Rondônia, sul do Pará).
4. Áreas inundáveis (várzea/igapó) — tratar como estrato separado ou excluir do modelo principal.
5. Campinarana/campo — estrato de baixa biomassa.

Se os dados não sustentarem 5 estratos, reduzir para 2–3 e declarar.

### 2.2 Features prioritárias

| Grupo | Features | Racional |
|---|---|---|
| Óptico S2 | medianas sazonais das bandas, NDVI, EVI, NDII, NBR, SAVI, textura GLCM | estrutura e composição |
| Landsat | série histórica harmonizada, índices, tendências | consistência temporal |
| Radar S1 | VV, VH, VH/VV, estatísticas temporais, coerência | estrutura, independente de nuvem |
| Topografia | elevação, declividade, posição topográfica | gradientes edáficos/hídricos |
| Clima | precipitação, déficit hídrico, temperatura | produtividade |
| Altura (opcional) | GEDI/ICESat-2 derivados, produto global de altura | estrutura vertical |

### 2.3 Tratamento da saturação

- Não confiar em um único índice; usar combinações e textura.
- Incluir S1 (VH) e, se possível, L-band histórico para as faixas altas.
- Modelar em **log(AGBD)** ou usar transformação de raiz (Chave 2014 usa raiz para AGBD),
  verificando o efeito na variância e nos resíduos.
- Reportar explicitamente que acima de determinado limiar (a estimar) a sensibilidade é baixa.

### 2.4 Várzea, igapó e campinarana

- Várzea/igapó: sazonalidade de inundação muda reflectância e radar; se o objetivo é "floresta
  de terra firme", **excluir** e declarar; se incluir, criar estrato e features de inundação.
- Campinarana: estrutura baixa e esparsa; tratar com o modelo de baixa biomassa (ver Cerrado),
  não com o modelo de terra firme densa.

### 2.5 Florestas secundárias e degradação

- Se a máscara de domínio exclui regeneração (como a máscara 2007–2016 da etapa anterior), o
  resultado é **estoque de vegetação nativa estável**, não "toda a cobertura lenhosa". Declarar.
- Degradação: sem dados de campo específicos, não prometer. Tratar como fase futura e limitar
  afirmações (`docs/16`).

## 3. Referência

- **GEDI L4A** filtrado por qualidade, restrito a footprints com baixa inclinação e boa
  sensitividade; pareamento com features por centroide e buffer.
- **Parcelas** (IFN/literatura) como validação independente e, se suficientes, como referência
  alternativa no estrato de baixa biomassa.
- **Cuidado com circularidade:** se GEDI treina e GEDI valida, o erro é subestimado. Validação
  final: parcelas independentes ou partição espacial/temporal rígida.

## 4. Incerteza específica da Amazônia

Componentes dominantes esperados:

1. **Erro de referência GEDI** em AGB alta (maior que em florestas temperadas).
2. **Viés de amostragem** das trilhas (não aleatórias).
3. **Erro de modelo** por extrapolação em regiões sem análogo (interflúvios remotos).
4. **Erro de área** por classificação/transição.

A decomposição é feita em `docs/12`; o relato deve sempre separar "erro do mapa" de "erro da
estimativa de área/total".

## 5. Critérios de aceite para a Amazônia

- Viés relativo da AGBD média dentro do limite acordado em validação por blocos (`docs/25`).
- Cobertura do IC de 90% próxima do nominal em validação.
- Nenhuma predição fora da AOA sem sinalização.
- Comparação com CCI Biomass/Spawn explicada (não necessariamente concordante; divergência
  documentada com hipótese).

## 6. Riscos dominantes

| Risco | Mitigação |
|---|---|
| Saturação em floresta densa | S1 + textura + transformação; declarar limite |
| Nuvem | composições sazonais + radar |
| GEDI enviesado | filtros + validação independente + AOA |
| Extrapolação remota | AOA + restrição de domínio |
| Mistura com várzea | estratificação/exclusão |
