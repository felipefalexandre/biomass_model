# 27 — Glossário

## Biomassa e carbono

| Termo | Definição |
|---|---|
| AGB | biomassa acima do solo (*aboveground biomass*), Mg de matéria seca |
| AGBD | densidade de AGB, Mg ha⁻¹ |
| BGB | biomassa abaixo do solo (*belowground biomass*), raízes |
| TB | biomassa total = AGB + BGB |
| necromassa | madeira morta (em pé ou caída); fora do escopo |
| serapilheira | material orgânico morto sobre o solo; fora do escopo |
| f_C | fração de carbono da matéria seca (padrão ~0,47, a confirmar) |
| CO₂e | equivalente de CO₂; neste projeto, apenas CO₂ |
| estoque | quantidade em um instante (Mg, Mg C) |
| fluxo | variação por tempo (Mg ano⁻¹) |

## Sensoriamento remoto

| Termo | Definição |
|---|---|
| footprint | área iluminada por um pulso LiDAR (GEDI ~25 m) |
| RH | *relative height*; percentil de altura do waveform |
| saturação | perda de sensibilidade do sinal em biomassa alta |
| speckle | ruído granular em radar |
| coerência | correlação entre aquisições SAR |
| composição sazonal | agregação de cenas por estação (mediana/percentis) |
| COG | *Cloud Optimized GeoTIFF* |
| AOA | *area of applicability*; região onde o modelo tem análogo no treino |

## Estatística e inferência

| Termo | Definição |
|---|---|
| estimando | quantidade populacional a estimar |
| design-based | inferência baseada no desenho amostral |
| model-based | inferência baseada no modelo |
| híbrida | combinação de modelo e amostra |
| quasi-design | inferência quando a amostra não é probabilística |
| CV | validação cruzada |
| blocos espaciais | partição do espaço para CV que respeita autocorrelação |
| LORO | *leave-one-region-out* |
| NNDM-LOO | CV que iguala distâncias treino–teste e predição–treino |
| bootstrap | reamostragem para estimar variabilidade |
| viés | erro sistemático (média dos resíduos) |
| RMSE | raiz do erro quadrático médio |
| MAE | erro absoluto médio |
| IC | intervalo de confiança |
| cobertura do IC | fração empírica de vezes que o IC contém o valor verdadeiro |

## Domínio e dados

| Termo | Definição |
|---|---|
| classe MapBiomas | classe de uso/cobertura da coleção |
| máscara de elegibilidade | pixels com classe 3/4 em todos os anos 2007–2016 |
| domínio | conjunto de pixels/áreas sobre o qual se estima |
| estrato | subdivisão do domínio com característica comum |
| warm-up | anos iniciais de uma série usados para inicializar estado |
| transição | mudança de classe entre anos |
| fitofisionomia | tipo de vegetação (ex.: cerrado *sensu stricto*) |

## Unidades

| Símbolo | Nome | Equivalência |
|---|---|---|
| Mg | megagrama | 1 t = 10³ kg |
| ha | hectare | 10⁴ m² |
| Mg ha⁻¹ | megagrama por hectare | 100 g m⁻² |
| Mg C | megagrama de carbono | — |
| Mg CO₂e | megagrama de CO₂ equivalente | C × 44/12 |

## Siglas

| Sigla | Significado |
|---|---|
| AGB/BGB | acima/abaixo do solo |
| GEDI | Global Ecosystem Dynamics Investigation |
| ICESat-2 | Ice, Cloud and land Elevation Satellite-2 |
| IFN | Inventário Florestal Nacional |
| SFB | Serviço Florestal Brasileiro |
| PRODES | Projeto de Monitoramento do Desmatamento na Amazônia Legal |
| MapBiomas | rede de mapeamento anual do uso da terra |
| CCI | Climate Change Initiative (ESA) |
| DEM | modelo digital de elevação |
| GLCM | *gray-level co-occurrence matrix* (textura) |
| GEE | Google Earth Engine |
| MRV | monitoramento, relato e verificação |
