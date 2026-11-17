# 14 — Desenho amostral e dados de campo

## 1. Papel do campo

Dados de campo são a única referência **independente** de biomassa. GEDI é produto de modelo;
benchmarks globais são modelos. Sem campo, a validação é circular ou condicional.

Neste projeto, o campo tem três papéis:

1. **Calibração** de allometria e de BGB.
2. **Validação independente** do mapa e das estimativas.
3. **Treino alternativo** em estratos onde GEDI é fraco (Cerrado baixo, secundárias).

## 2. Desenho recomendado

### 2.1 Amostragem

- **Estratificada aleatória** por bioma × fisionomia × faixa de acessibilidade.
- Probabilidades de inclusão conhecidas (para inferência design-based).
- **Clusters** (ex.: conglomerados de parcelas) para reduzir custo de deslocamento, com
  variância calculada no nível do cluster.
- **Não** usar amostragem de conveniência como se fosse probabilística; se usada, declarar e
  tratar como modelo-based.

### 2.2 Parcelas

| Parâmetro | Recomendação | Observação |
|---|---|---|
| Forma | circular ou retangular | consistência é mais importante que forma |
| Tamanho | 0,25–1 ha (floresta); 0,1–0,5 ha (Cerrado) | depende da densidade |
| Subparcelas | sim, para regeneração | documentar |
| DAP mínimo | 5 cm (padrão em estudos de Cerrado) ou 10 cm (floresta) | **fixar e documentar** |
| Altura | medir ou estimar com equipamento | erro afeta allometria |
| Identificação | espécie/gênero/família | necessário para densidade da madeira |
| Posição | GNSS de precisão; registrar erro | erro > 10 m compromete pareamento |
| Data | registrar | pareamento temporal |
| Distúrbio | fogo, corte, inundação | estratificação |

### 2.3 Protocolo de biomassa

1. Medir DAP (e altura) de todos os indivíduos acima do mínimo.
2. Identificar táxon; obter densidade da madeira (GWDD).
3. Aplicar equação alométrica apropriada (Chave 2005/2014 para floresta; Ribeiro 2011/Miranda
   2014 para Cerrado), registrando a escolha.
4. Somar componentes conforme protocolo (fuste, galhos, folhas).
5. Para BGB: escavação/subsampling em subamostra; ou razão/equação documentada.
6. Registrar incerteza de medição e de equação.

## 3. Harmonização de dados existentes

Ao compilar parcelas de literatura/IFN:

| Campo | Harmonização |
|---|---|
| DAP mínimo | filtrar/reponderar para um mínimo comum |
| Unidade de massa | converter para Mg de matéria seca |
| Equação usada | registrar; se possível, recalcular com equação comum |
| Componentes | separar AGB/BGB; não somar o que não é comparável |
| Posição | verificar datum/CRS; descartar se erro alto |
| Data | associar ao ano de imageamento mais próximo |
| Espécie | padronizar nomes (taxonomia) |

## 4. Análise de poder

Antes de planejar campo novo, estimar:

- variabilidade esperada de AGBD por estrato (da literatura);
- erro aceitável (ex.: 10% relativo);
- número de clusters/parcelas necessários para atingir esse erro com IC 90%;
- custo por parcela.

Sem essa análise, o número de parcelas é arbitrário.

## 5. IFN e acesso

- O IFN é a maior fonte potencial, mas o acesso a microdados e coordenadas pode ser restrito.
- **Redflag registrada** (`docs/22`): se os dados não forem acessíveis, o plano deve prever
  compilação alternativa (teses, artigos com dados suplementares, redes de parcelas).
- Pergunta aberta: existe acordo/parceria que viabilize acesso? (`docs/30`, Q2).

## 6. Controle de qualidade de campo

- Dupla medição em 10% das parcelas.
- Verificação de DAP anômalo (curva de distribuição).
- Checagem de coordenadas contra imagem de alta resolução.
- Registro fotográfico e caderneta digital.
- Dataset com esquema fixo, versionado e validado por testes.

## 7. Ética e acesso

- Parcelas em UC/TI exigem autorização (SisGen, FUNAI/ICMBio conforme o caso).
- Dados de localização sensível podem ser generalizados; registrar a política.
- Consentimento e repartição de benefícios quando aplicável.

## 8. Entregáveis de campo

1. Protocolo de campo versionado.
2. Modelo de dados (esquema de tabelas).
3. Plano de amostragem com mapa e justificativa.
4. Análise de poder.
5. Relatório de QA das medições.
