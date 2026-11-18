# 22 — Redflags e restrições

Registro explícito de tudo que **não** é gratuito/aberto ou que impõe risco de dependência.
Redflag não interrompe o trabalho; é documentada e contornada ou aceita com justificativa.

## 1. Dados e serviços com restrição

| ID | Item | Restrição | Impacto | Contorno |
|---|---|---|---|---|
| RF01 | Imagens comerciais de alta resolução (Planet, Maxar, ICEYE, Capella) | pagas | não usadas na trilha principal | usar S2/Landsat/S1; registrar se o usuário tiver acesso |
| RF02 | LiDAR aerotransportado dedicado (voos próprios) | custo alto | não disponível | GEDI/ICESat-2; campo |
| RF03 | RAINFOR / ForestPlots.net | acesso por solicitação/afiliação | possível falta de parcelas | compilação de artigos/teses; parceria |
| RF04 | Microdados do IFN (SFB) | parcialmente aberto: o Painel de Biomassa e Carbono publica AGB por UA (coordenadas ~0,1°), mas não o inventário árvore-a-árvore completo | pareamento fino limitado | usar o painel para validação regional; dados botânicos via SNIF, se disponíveis |
| RF05 | Google Earth Engine | gratuito para pesquisa, termos comerciais podem restringir uso/redistribuição | dependência de plataforma | trilha local; se usar, documentar e não redistribuir dados do GEE |
| RF06 | Produtos GEDI L4A/L4B | são **produtos de modelo**, não observação direta de biomassa | erro próprio e circularidade | tratar como referência imperfeita; validar com campo |
| RF07 | NISAR / BIOMASS (ESA) | status, disponibilidade e política de acesso a confirmar | incerteza sobre radar L/P-band futuro | não depender; monitorar |
| RF08 | Dados de carbono do solo de alta resolução | muitos são pagos | fora do escopo | SoilGrids (250 m) se necessário |
| RF09 | Mapas nacionais privados de biomassa | pagos | não usados | benchmarks abertos (CCI, Spawn) |
| RF10 | Imagens de drone | custo operacional | não escala | usar em validação local, se houver |

## 2. Restrições científicas (não são "pagas", mas limitam)

| ID | Restrição | Consequência | Tratamento |
|---|---|---|---|
| RC01 | Saturação óptica em AGB alta | subestimação na Amazônia densa | S1, textura, declarar limite |
| RC02 | GEDI sem cobertura wall-to-wall | extrapolação | modelo + AOA |
| RC03 | GEDI com desempenho fraco em savana | viés no Cerrado | campo, estratificação |
| RC04 | Ausência de BGB observável | incerteza alta | cenários, literatura |
| RC05 | Escassez de campo independente | validação limitada | compilação; declarar |
| RC06 | Fogo e degradação | não estacionariedade | features; fase futura |
| RC07 | Mudança de sensores ao longo do tempo | séries inconsistentes | harmonização; agregação |
| RC08 | Coordenadas de parcelas imprecisas | pareamento errado | buffers; descarte |
| RC09 | Escala do footprint vs pixel | erro de representação | análise de sensibilidade |
| RC10 | Viés de acessibilidade das parcelas | subrepresentação de áreas remotas | ponderação; AOA |
| RC11 | L4A subestima savana aberta | viés grave no Cerrado (piloto: mediana 6,2 contra 19,4 Mg ha⁻¹ do IFN; 59,6% < 10) | campo como referência primária; L4A só auxiliar (ADR-0015) |

## 3. Restrições de escopo herdadas

| ID | Restrição | Efeito |
|---|---|---|
| RE01 | O domínio é a classe 3/4 do MapBiomas **no ano-alvo** (ADR-0010); a máscara estável 2007–2016 é apenas estrato opcional | totais anuais mudam com o denominador; comparabilidade com a etapa anterior exige o estrato estável explícito |
| RE02 | Série de desmatamento só é recomendada a partir de 2016 (warm-up 2014–2015) | análises de emissão começam em 2016 |
| RE03 | Somente Amazônia e Cerrado | não cobre outros biomas |
| RE04 | Sem necromassa, serapilheira, solo | estoque não é "total do ecossistema" |
| RE05 | Dados de raiz (escavações) são escassos | modelo independente de BGB (ADR-0011) pode ser rebaixado a cenário onde faltar dado |

## 4. Sinais de alerta em propostas/fornecedores

- Promessa de "biomassa exata" sem incerteza.
- Produto de AGB sem documentação de validação independente.
- Modelo treinado e validado no mesmo dado.
- "IA" usada como argumento de autoridade.
- Dados "abertos" sem licença clara.
- Custo zero que na prática exige infraestrutura paga.

## 5. Regra de registro

Toda redflag deve aparecer:

1. aqui;
2. no `data/catalogo_dados.csv` (quando for fonte);
3. no relatório final, em seção própria;
4. na resposta ao usuário, quando bloquear uma escolha.

## 6. Itens que exigem decisão do usuário

- Aceitar ou não dados pagos (Q1).
- Aceitar GEE como dependência (Q7).
- Aceitar produto de modelo (GEDI) como referência principal (Q5).
