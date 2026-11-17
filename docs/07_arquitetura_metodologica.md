# 07 — Arquitetura metodológica

## 1. Princípios

1. **Separação entre mapa e estimativa.** O mapa é um meio; a estimativa com incerteza é o fim.
2. **Contratos explícitos entre camadas.** Cada artefato tem esquema, grade, unidade e versão.
3. **Simplicidade primeiro.** Baseline interpretável antes de qualquer modelo complexo.
4. **Validação espacial obrigatória.** Nenhum resultado entra sem CV por blocos e AOA.
5. **Rastreabilidade total.** Dado → feature → modelo → predição → estimativa → relatório.
6. **Falha alto e cedo.** Verificações de grade, CRS, unidades e cobertura antes do processamento.

## 2. Camadas

```
┌──────────────────────────────────────────────────────────────────┐
│ L6. Produtos e relatórios                                        │
│   mapas COG, tabelas por domínio, IC 90%, laudos, metadados      │
├──────────────────────────────────────────────────────────────────┤
│ L5. Inferência e incerteza                                       │
│   estimadores design/híbridos, bootstrap, decomposição de variância│
├──────────────────────────────────────────────────────────────────┤
│ L4. Modelagem                                                    │
│   baseline → RF/XGBoost por bioma; calibração; AOA; seleção      │
├──────────────────────────────────────────────────────────────────┤
│ L3. Referência                                                   │
│   GEDI L4A filtrado, parcelas harmonizadas, pseudo-referência     │
├──────────────────────────────────────────────────────────────────┤
│ L2. Features                                                     │
│   S2, Landsat, S1, DEM, clima; estatísticas sazonais; textura    │
├──────────────────────────────────────────────────────────────────┤
│ L1. Dados e domínio                                              │
│   catálogo, máscaras, biomas, grade de referência, metadados     │
└──────────────────────────────────────────────────────────────────┘
```

## 3. Fluxo ponta a ponta

1. **Definir domínio** (bioma, ano, classe, máscara) → vetor/raster de domínio.
2. **Construir a grade** de referência e validar alinhamento.
3. **Adquirir dados** conforme catálogo; registrar origem e hash.
4. **Pré-processar** (nuvem, harmonização, índices, textura, agregações).
5. **Extrair referência** (GEDI/parcelas) e parear com features.
6. **Análise de representatividade e AOA preliminar.**
7. **Treinar baseline** (GLM/regressão) e modelos candidatos.
8. **Validar** (blocos espaciais, LORO, NNDM-LOO) e selecionar.
9. **Prever** wall-to-wall por domínio, em janelas.
10. **Estimar** totais e médias com IC, por estrato e domínio.
11. **Propagar incerteza** (amostragem + modelo + referência).
12. **Pós-processar** (máscara, unidades, COG, metadados).
13. **Comparar** com benchmarks e registrar divergências.
14. **Publicar** com relatório de limitações.

## 4. Escada de modelos (model ladder)

| Nível | Modelo | Papel | Critério para subir |
|---|---|---|---|
| M0 | média/estratificado por classe | piso de referência | sempre |
| M1 | regressão linear/GLM com features-chave | interpretável | M1 > M0 em CV espacial |
| M2 | Random Forest | não linear, robusto | ganho material e estável |
| M3 | Gradient boosting (XGBoost/LightGBM) | desempenho | ganho > incerteza da métrica |
| M4 | Ensemble/stacking | robustez | ganho consistente entre regiões |
| M5 | Deep learning | experimental | só se M2–M4 falharem em padrão claro |

**Regra:** subir de nível só se o ganho for maior que a variabilidade entre folds e se o modelo
continuar interpretável o suficiente para auditoria. Complexidade sem ganho é rejeitada (ADR-0002
e `docs/25`).

## 5. Estratificação

Estratificação mínima:

- **bioma** (Amazônia, Cerrado);
- **classe de vegetação MapBiomas** agrupada (florestal, savânica, campestre lenhosa);
- **faixa de AGBD** para diagnóstico (não para treino, para evitar circularidade);
- **região geográfica** para validação (blocos).

Estratificação adicional sugerida (se dados permitirem): sub-regiões Amazônicas (escudo das
Guianas, Amazônia central, arco do desmatamento, várzea/igapó) e fitofisionomias do Cerrado.

## 6. Interface entre mapa e estimativa

O mapa entrega, por pixel:

```
agbd_mg_ha      float32
agbd_sd         float32   (desvio do modelo)
aoa             uint8     (1 dentro, 0 fora)
quality_mask    uint8     (bits: nuvem, água, urbano, transição)
```

A camada de estimativa consome o mapa **e** a amostra de referência, nunca apenas o mapa. Isso é
o que permite separar erro de modelo de erro de amostragem.

## 7. Decisões de arquitetura

| Decisão | Alternativa descartada | Motivo |
|---|---|---|
| Dois modelos por bioma | modelo único pantropical | evidência de degradação no Cerrado |
| COG como formato de saída | GeoTIFF clássico | leitura por janela, nuvem, compressão |
| Processamento por janelas | ler raster inteiro | memória (raster nacional > 20 GB) |
| Configuração versionada em arquivo | parâmetros no código | reprodutibilidade |
| Testes de contrato de grade | confiança manual | erros silenciosos de alinhamento |

## 8. O que a arquitetura deliberadamente não faz

- Não unifica AGB e BGB no mesmo modelo (BGB é derivada).
- Não usa GEDI como validação final (circularidade).
- Não promete "biomassa verdadeira": entrega estimativa com incerteza e domínio de validade.
- Não usa dados pagos na trilha principal.
