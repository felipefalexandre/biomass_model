# 16 — Mudança temporal

## 1. Três tipos de mudança

| Tipo | Exemplo | Detectabilidade | Tratamento |
|---|---|---|---|
| conversão | floresta → pastagem | alta | integrar com desmatamento |
| degradação | fogo, extração seletiva, borda | baixa/média | fase futura, com ressalvas |
| recuperação | regeneração secundária | média | estrato próprio |

Não misturar os três em um único "Δbiomassa" sem separá-los.

## 2. Série já disponível

A etapa anterior produziu, em `E:\Mapbiomas\outputs_eligibilidade`:

- máscara de elegibilidade (classe 3/4 em 2007–2016);
- desmatamento anual 2014–2025 (warm-up 2014–2015; uso recomendado a partir de 2016);
- área de estudo 622.532.566,8 ha; elegível 386.714.878,6 ha (62,12%);
- Amazônia: 297.014.653,96 ha elegíveis; Cerrado: 89.700.224,66 ha elegíveis.

Esses produtos permitem calcular **fluxo por conversão**:

```
Emissão_AGB(t) = Σ_{pixels desmatados em t} AGBD(pixel, t−1) × área_pixel
```

com cenários de destino da biomassa (queima imediata, decomposição lenta, remoção de madeira).
O destino **não** é observável: reportar como cenário, não como fato.

## 3. Consistência radiométrica

Sem harmonização, mudanças entre sensores/anos podem ser confundidas com mudança de biomassa.

- Harmonizar Landsat 8/9 e Sentinel-2 (coeficientes ou calibração empírica documentada).
- Usar composições na mesma estação fenológica.
- Verificar tendências em áreas de referência estáveis (controle).
- Se a incerteza da harmonização for grande, agregar anos (ex.: médias trienais).

## 4. Detecção de mudança

### 4.1 Abordagem direta (recomendada para conversão)

- Usar a série de desmatamento já produzida (alta confiança para conversão).
- Estimar estoque antes/depois; calcular diferença.
- Não re-detectar desmatamento com um modelo de biomassa (baixa sensibilidade).

### 4.2 Abordagem indireta (ΔAGBD)

- ΔAGBD = AGBD(t2) − AGBD(t1), com IC da diferença.
- **Problema:** a variância da diferença inclui covariância entre anos; se os erros forem
  correlacionados, a diferença é mais precisa que a diferença de marginais; se independentes, é
  menos. Estimar a covariância por dados pareados (mesmos pixels/parcelas), não assumir zero.
- Limiar mínimo detectável: calcular a partir da variância da diferença; mudanças menores não
  devem ser reportadas como reais.

### 4.3 Poder de detecção

Simular:

- variabilidade de AGBD por pixel e sua autocorrelação;
- erro do modelo;
- tamanho de área;
- número de anos agregados.

Resultado esperado: conversões grandes detectáveis anualmente; ganhos/perdas incrementais só em
janelas plurianuais e/ou áreas grandes.

## 5. Degradação

- Fogo: usar cicatriz de queimada (feature) e NBR/dNBR; relacionar com perda de AGBD.
- Extração seletiva: difícil; exige LiDAR ou campo; não prometer.
- Borda: efeito documentado, mas magnitude incerta; tratar como camada de contexto.
- **Regra:** se não houver validação específica, degradação é **análise exploratória**, não
  estimativa oficial.

## 6. Regeneração

- Florestas secundárias têm AGBD crescente e composição distinta.
- Se o modelo foi treinado em primária, aplicá-lo a secundárias enviesa.
- Estratégia: classe própria + modelo/curva de crescimento (se houver dados) ou exclusão com
  declaração.
- A máscara 2007–2016 da etapa anterior **exclui** regeneração por construção; isso é uma
  limitação de escopo, não um erro.

## 7. Produto temporal

Para cada ano:

```
agbd_mg_ha(t), agbd_sd(t), aoa(t), quality_mask(t)
```

Para a mudança:

```
d_agbd(t1,t2), d_agbd_sd, flag_significancia
```

Metadados: datas de imageamento, sensores, composição, versão do modelo.

## 8. Critérios de aceite

- Mudança reportada apenas quando |Δ| > limiar de detecção calculado.
- Conversão validada contra desmatamento/PRODES com matriz de confusão de área.
- Degradação claramente rotulada como exploratória.
- Nenhuma série temporal publicada sem teste de consistência radiométrica.
