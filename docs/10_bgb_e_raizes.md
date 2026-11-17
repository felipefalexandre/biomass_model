# 10 — BGB e raízes

## 1. Por que BGB é um problema separado

Biomassa abaixo do solo **não é observável por sensoriamento remoto**. Qualquer BGB produzida
por um sistema desse tipo é **derivada** de AGB por equação, razão ou modelo de solo/clima.
Isso tem três consequências:

1. A incerteza de BGB é **maior** que a de AGB e não é independente dela.
2. A relação AGB–BGB varia com bioma, fisionomia, solo, fogo e idade.
3. Reportar BGB como se fosse "medida" é erro metodológico.

## 2. Decisão de arquitetura (ADR-0011)

BGB é um **modelo próprio**, não uma derivação da AGB. O modelo central usa dados de raiz
(escavações/monolitos) e preditores de solo (SoilGrids), clima (ERA5-Land), fisionomia
(classes 3/4 e tipologia) e, opcionalmente, estrutura (altura/AGB como covariável). AGB e BGB
compartilham grade, máscara e módulo de incerteza, mas são estimados separadamente.

A razão R:S derivada da AGB permanece apenas como linha de base, cenário de sensibilidade ou
preenchimento rotulado onde não há modelo aplicável.

## 3. Métodos disponíveis

### 3.1 Razão raiz/parte aérea (R:S)

- BGB = R:S × AGB.
- Vantagem: simples, transparente, aplicável em escala.
- Desvantagem: assume proporcionalidade constante; ignora variação com tamanho, solo e fogo.
- Uso: cenário central, com R:S específico por bioma/fisionomia quando houver fonte; caso
  contrário, usar *defaults* de diretrizes IPCC (valores exatos a extrair das tabelas oficiais —
  não presumir).

### 3.2 Equações alométricas de raiz

- BGB = f(D, H, ρ, ...) ajustada em escavações.
- Mais realista, mas exige dados destrutivos de raiz, raros.
- No Cerrado, Ribeiro et al. (2011) mediram BGB por subsampled em 10 parcelas, com SE ~23%.

### 3.3 Modelos de partição (alocação)

- Alocação de carbono entre parte aérea e raízes em função de clima, solo e estágio sucessional.
- Mais complexo; exige parametrização local; não recomendado como primeira opção.

## 4. Evidência disponível para o Brasil

| Fonte | Achado | Uso |
|---|---|---|
| Ribeiro et al. 2011 (DOI 10.1016/j.foreco.2011.04.017) | cerrado s.s.: AGB 62.965,5 kg ha⁻¹ (SE 14,6%); BGB 37.501,8 kg ha⁻¹ (SE 23%); razão dentro da faixa de savanas | cenário de referência para Cerrado |
| Miranda et al. 2014 (DOI 10.1111/btp.12095) | revisão de biomassa por fisionomia, incluindo BGB; destaca que BGB não pode ser avaliada remotamente | estratificação e alerta |
| Oliveira et al. 2019 (DOI 10.1186/s13021-019-0121-0) | savana aberta em solos arenosos: AGB total 12,88 Mg ha⁻¹ | limite inferior do gradiente |

Observação: esses valores são de sítios específicos e **não** devem ser extrapolados como média
do bioma. Servem para ancorar faixas e checar plausibilidade.

## 5. Estratégia proposta

1. **Modelo de BGB separado** (ADR-0011), com features de solo, clima, fisionomia e estrutura;
   entrada AGB apenas como covariável opcional.
2. **Cenários explícitos:**
   - **C1 (mínimo):** R:S conservador, baseado no limite inferior da literatura (linha de base).
   - **C2 (central):** modelo de solo/clima/fisionomia — método principal.
   - **C3 (máximo):** limite superior da literatura / sensibilidade.
3. **Propagação:** a variância de BGB inclui (i) erro do modelo de BGB, (ii) erro dos dados de
   raiz, (iii) covariância com AGB quando a covariável for usada (declarada).
4. **Transparência:** nunca publicar BGB sem o método, o cenário e a fonte do parâmetro.

## 6. Casos especiais

### 6.1 Cerrado e fogo

- Fogo recorrente pode aumentar a fração de raízes (rebrota) e alterar R:S.
- Sem dados longitudinais, tratar como incerteza adicional, não como ajuste fino.

### 6.2 Várzea/igapó

- Raízes adaptadas a inundação; R:S pode diferir. Se o estrato for incluído, usar cenário
  próprio ou excluir e declarar.

### 6.3 Florestas secundárias

- R:S muda com a idade; usar relação dependente de idade se houver fonte; caso contrário,
  declarar que a BGB de secundárias é a menos confiável.

## 7. Raízes finas e necromassa

- Raízes finas (<2 mm) são excluídas por convenção; se incluídas, exigem protocolo próprio.
- Necromassa (madeira morta) e serapilheira **não** fazem parte deste módulo; se o objetivo for
  estoque total do ecossistema, são pools adicionais a planejar separadamente.

## 8. Critérios de aceite

- BGB reportada com cenário e fonte do parâmetro.
- Incerteza de BGB ≥ incerteza de AGB (nunca menor, por construção).
- Nenhuma afirmação de "BGB medida por satélite".
- Análise de sensibilidade mostrando o efeito da escolha de R:S no total.
