# 23 — Riscos e mitigação

## 1. Registro de riscos

Escala de probabilidade (P) e impacto (I): 1 baixo, 3 médio, 5 alto. Risco = P × I.

| ID | Risco | P | I | Risco | Mitigação | Responsável |
|---|---|---|---|---|---|---|
| R01 | Referência (GEDI) enviesada no Cerrado | 4 | 4 | 16 | campo independente; estratificação; AOA | ciência |
| R02 | Saturação óptica na Amazônia densa | 5 | 3 | 15 | S1/textura; declarar limite; transformação | modelagem |
| R03 | Falta de campo independente | 4 | 4 | 16 | compilação; parcerias; declarar limitação | dados |
| R04 | Erro de grade/CRS | 3 | 5 | 15 | testes de contrato; validação prévia | engenharia |
| R05 | Viés de área por classificação | 3 | 4 | 12 | validação de máscara; matriz de confusão | dados |
| R06 | Custo computacional subestimado | 3 | 3 | 9 | piloto; medição; janelas | engenharia |
| R07 | Inconsistência temporal entre sensores | 4 | 3 | 12 | harmonização; agregação | features |
| R08 | Extrapolação para regiões sem análogo | 4 | 4 | 16 | AOA; restrição de domínio | modelagem |
| R09 | BGB tratada como medida | 3 | 4 | 12 | cenários + transparência | ciência |
| R10 | Circularidade treino/validação | 3 | 5 | 15 | separação rígida; validação externa | validação |
| R11 | Licença incompatível descoberta tarde | 2 | 4 | 8 | catálogo preenchido antes | governança |
| R12 | Perda de dados/artefatos | 2 | 4 | 8 | hash, backup, versionamento | engenharia |
| R13 | Escopo muda no meio | 3 | 3 | 9 | ADRs; perguntas abertas | gestão |
| R14 | Resultado não reprodutível | 2 | 5 | 10 | manifesto; ambiente fixo | engenharia |
| R15 | Divergência grande com benchmarks não explicada | 4 | 3 | 12 | análise de diferenças; documentar | ciência |
| R16 | Fogo/degradacão confundidos com mudança de biomassa | 4 | 3 | 12 | features; rotular exploratório | ciência |

## 2. Riscos de alto valor (≥15)

### R01 — Referência enviesada no Cerrado

- **Sinal:** resíduos sistemáticos por faixa de AGBD; desempenho pior em G1/G2.
- **Ação:** priorizar campo no Cerrado; usar GEDI apenas onde há cobertura; reportar erro por
  grupo; considerar modelo de duas etapas.

### R02 — Saturação óptica

- **Sinal:** resíduos negativos em AGBD alta; pouca variação predita no topo da distribuição.
- **Ação:** incluir S1 e altura; transformar alvo; limitar afirmações acima do limiar de
  saturação; comparar com produtos que usam LiDAR.

### R03 — Falta de campo

- **Sinal:** impossibilidade de validar fora de GEDI.
- **Ação:** compilar dados abertos; buscar parcerias; declarar que a validação é condicional.

### R08 — Extrapolação

- **Sinal:** muitas predições fora da AOA; features extremas.
- **Ação:** AOA obrigatória; restringir domínio; não estimar onde não há análogo.

### R10 — Circularidade

- **Sinal:** métricas boas demais; mesma fonte em treino e teste.
- **Ação:** separar por bloco/região/tempo; validar com campo.

## 3. Riscos de governança

- Licença share-alike (MapBiomas) pode "contaminar" derivados.
- Dados restritos (IFN) impedem redistribuição.
- Uso de GEE pode criar dependência e restringir redistribuição.
- **Ação:** decisão de licença antes da publicação; revisão jurídica se necessário.

## 4. Plano de contingência

| Cenário | Resposta |
|---|---|
| GEDI indisponível ou inadequado | usar campo + benchmarks; declarar mudança de método |
| Campo não obtido | estimativa model-based com limitação explícita |
| Recursos computacionais insuficientes | reduzir domínio/anos; priorizar Amazônia ou Cerrado |
| Prazo curto | entregar produto por domínio prioritário, não nacional |
| Divergência com benchmark | publicar comparação e hipótese, não esconder |

## 5. Monitoramento

- Revisão de riscos a cada fase (`docs/24`).
- Registrar riscos materializados no `docs/19` (manifesto) e no relatório.
- Atualizar este documento; não apagar riscos resolvidos (marcar como resolvidos).

## 6. Riscos aceitos (com justificativa)

| Risco | Justificativa da aceitação |
|---|---|
| BGB incerta | não há alternativa aberta viável; cenários tornam a incerteza visível |
| Cobertura GEDI amostral | é a melhor referência aberta disponível |
| Sem necromassa/solo | fora do escopo declarado |
