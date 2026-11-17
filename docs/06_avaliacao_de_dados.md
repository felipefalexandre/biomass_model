# 06 — Avaliação de dados e qualidade

Objetivo: identificar, antes de qualquer modelagem, os **vieses e erros estruturais** de cada
fonte que possam contaminar a estimativa. A avaliação é feita por fonte e por tipo de erro.

## 1. Dimensões de qualidade

| Dimensão | Pergunta | Consequência se falhar |
|---|---|---|
| Acurácia posicional | o pixel/ponto está onde diz estar? | pareamento errado com referência |
| Acurácia temática | a classe está correta? | máscara/estratificação errada |
| Acurácia numérica | o valor (AGB, altura) é correto? | viés direto na estimativa |
| Consistência temporal | a série é comparável entre anos? | mudança espúria |
| Completude | há lacunas? | cobertura desigual, viés regional |
| Representatividade | a amostra cobre o domínio? | extrapolação silenciosa |
| Documentação | metadados bastam para reproduzir? | irreprodutibilidade |

## 2. Avaliação por fonte

### 2.1 GEDI L4A / L4B

- **Natureza:** AGBD é **produto de modelo** (OLS sobre métricas de waveform), não medição
  direta. O erro reportado é do modelo, não inclui erro de campo usado no ajuste.
- **Cobertura:** amostral em trilhas; densidade varia com latitude e com o período da missão.
  Não é wall-to-wall. Áreas sem trilhas ficam sem referência.
- **Erro conhecido:** maior em AGB alta e onde o treino é escasso (Duncanson et al. 2022);
  sensível a inclinação, cobertura de dossel e qualidade do waveform.
- **Geolocalização:** erro de posição pode deslocar o footprint em relação à feição no óptico;
  pareamento deve usar buffer e checagem de consistência.
- **Filtros de qualidade:** aplicar `quality_flag`, `degrade_flag`, `sensitivity`,
  `solar_elevation`, `l4_quality_flag` conforme documentação do produto (valores exatos a
  confirmar na versão usada).
- **Risco de circularidade:** usar GEDI para treinar e GEDI para validar é circular. Validação
  final deve usar campo independente ou partição espacial/temporal rígida.

### 2.2 ICESat-2 ATL08

- Fornece altura e métricas de dossel, não AGB diretamente; exige conversão (alométrica ou
  modelo). Beam pattern e ruído de fótons exigem filtragem. Usar como feature/validação de
  altura, não como AGB "verdadeira".

### 2.3 Dados de campo (IFN, parcelas)

- **Representatividade:** parcelas tendem a se concentrar em áreas acessíveis; em Amazônia isso
  subrepresenta interflúvios e áreas remotas.
- **Padronização:** diâmetro mínimo, altura, inclusão de palmeiras, equações e datas variam.
- **Posição:** coordenadas podem ser degradadas por sigilo ou erro de GPS.
- **Tempo:** a parcela mede um instante; a imagem pode ser de outro ano.
- **Correção necessária:** harmonizar DAP mínimo, unidades, componentes e convenção de massa seca;
  registrar incerteza de medição.

### 2.4 Sentinel-2 / Landsat

- **Nuvem e sombra:** crítico na Amazônia; composições (medianas sazonais) reduzem o problema,
  mas introduzem mistura temporal.
- **Bidirecionalidade:** ângulos de visada/sol variam; séries multi-sensor exigem harmonização.
- **Saturação:** em AGB alta, índices saturam; não esperar sensibilidade acima de ~150–200 Mg ha⁻¹.
- **Mudança de sensor:** Landsat 8 → 9 e S2A → S2B exigem checagem de calibração.

### 2.5 Sentinel-1

- **Speckle:** requer filtragem (ex.: Refined Lee) e/ou estatísticas multitemporais.
- **Geometria:** órbitas ascendente/descendente e ângulos diferentes geram respostas distintas.
- **Saturação:** C-band satura cedo; útil para estrutura média, fraco para dossel alto.
- **Topografia:** sombreamento/layover em relevo; corrigir com DEM.

### 2.6 Topografia e clima

- SRTM tem ruído e vieses em relevo íngreme e dossel; Copernicus DEM é alternativa.
- ERA5-Land é reanálise (~9 km), não medição local: usar como contexto regional, não como
  gradiente fino.
- Clima estático (WorldClim/CHELSA) não captura anos específicos; combinar com ERA5-Land/CHIRPS
  quando a variação interanual importar.

### 2.7 MapBiomas e máscaras

- A classe é o insumo da estratificação; erro de classificação propaga viés de área.
- A máscara de elegibilidade da etapa anterior usa classes 3/4 em 2007–2016; isso define o
  **domínio de vegetação nativa estável** e deve ser declarado como tal (não é "toda a vegetação").
- Áreas de transição e regeneração ficam de fora por construção; isso subestima o estoque se o
  objetivo for "toda a vegetação".

## 3. Compatibilização

### 3.1 Grade

- Grade de referência única, definida uma vez (30 m, alinhada a um sistema projetado ou ao grid
  MapBiomas), com contrato de alinhamento verificado (`assert_compatible`) antes de empilhar.
- Reprojeção **só** com método declarado (bilinear para contínuos; vizinho mais próximo para
  categóricos) e registro do método.

### 3.2 Tempo

- Definir janela temporal por ano (ex.: composição de estação seca) e documentar.
- Referência e features devem estar no mesmo ano ou em janela declarada.
- Mudança de uso no intervalo é fonte de erro; excluir pixels com transição no ano.

### 3.3 Espaço

- Footprint GEDI (~25 m) vs pixel (30 m): pareamento por centroide com buffer e checagem de
  homogeneidade da vizinhança; descartar footprints em bordas de classe.
- Parcelas: usar raio de influência documentado; não parear com pixel único sem análise de
  sensibilidade.

### 3.4 Unidades

- AGBD: Mg ha⁻¹ (matéria seca). Converter kg ha⁻¹, t ha⁻¹, g m⁻² explicitamente.
- Carbono: Mg C; CO₂e: Mg CO₂e. Nunca misturar.
- Área: ha; calcular área de pixel por latitude quando em EPSG:4326.

## 4. Análise de representatividade (obrigatória antes do treino)

1. Distribuição espacial da referência vs domínio (densidade por bloco, distância à estrada,
   classe MapBiomas, faixa de AGBD).
2. Distribuição de AGBD da referência vs benchmarks globais.
3. Cobertura de features (nuvens, falhas S1, sombreamento).
4. Identificação de **regiões sem análogo no treino** → excluir da predição ou sinalizar fora da
   AOA.

## 5. Critérios de rejeição de dados

Rejeitar (ou tratar explicitamente) quando:

- metadados de CRS/unidade ausentes e não inferíveis;
- licença incompatível;
- sobreposição temporal inaceitável;
- referência com erro de posição maior que o suporte;
- duplicidade não resolvida;
- valores fora de faixa física plausível (ex.: AGBD negativa, > 700 Mg ha⁻¹ sem justificativa).
