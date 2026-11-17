# 21 — Governança de dados e licenças

## 1. Princípio

Dados abertos não significa "sem regras". Cada fonte tem licença, termos de uso, exigência de
citação e, às vezes, restrição de redistribuição. O sistema deve ser **legalmente utilizável** e
**cientificamente citável**.

## 2. Matriz de obrigações (resumo)

| Fonte | Licença/termos (a confirmar) | Citação | Redistribuição |
|---|---|---|---|
| Copernicus Sentinel-1/2 | Copernicus data policy (livre) | obrigatória | permitida com atribuição |
| Landsat 8/9 | domínio público (USGS) | recomendada | permitida |
| SRTM | domínio público (USGS) | recomendada | permitida |
| GEDI L4A/L4B | NASA, aberto | obrigatória (DOI) | verificar termos |
| ERA5-Land | Copernicus C3S (licença) | obrigatória | verificar |
| CHIRPS | aberto (a confirmar) | obrigatória | verificar |
| WorldClim/CHELSA | aberto (a confirmar) | obrigatória | verificar |
| SoilGrids | CC BY (a confirmar) | obrigatória | permitida com atribuição |
| MapBiomas | CC BY-SA 4.0 (a confirmar no site) | obrigatória | **share-alike só para obras derivadas** do dado; usar para mascarar/estratificar e distribuir um produto novo não torna automaticamente o produto share-alike — mas redistribuir a camada MapBiomas adaptada, sim |
| PRODES/TerraBrasilis | aberto (a confirmar) | obrigatória | verificar |
| IBGE (biomas, municipal) | aberto | recomendada | permitida |
| IFN/SFB — Painel de Biomassa e Carbono | **CC BY** (verificado no portal de dados) | obrigatória | permitida com atribuição; microdados botânicos têm termos próprios |
| GWDD (Dryad/Zenodo) | aberto (CC0/CC BY — confirmar) | obrigatória | verificar |
| Google Earth Engine | termos de serviço | conforme | não redistribuir dados do GEE |

**Regra:** antes de incorporar uma fonte, preencher a linha no `data/catalogo_dados.csv` com
licença, URL dos termos e decisão (usar/não usar/como).

## 3. Citação e atribuição

- Toda saída publicada deve ter seção de **fontes de dados** e **softwares**.
- DOI das fontes quando existirem.
- Agradecimentos a programas (Copernicus, NASA, USGS, MapBiomas, INPE).
- Citar a versão exata (ex.: MapBiomas Coleção 11, data de acesso).

## 4. Redistribuição de produtos derivados

Produtos derivados (mapas de AGB, tabelas) podem ser distribuídos sob:

- licença própria escolhida (ex.: CC BY 4.0) **se** todas as fontes permitirem;
- se houver fonte com share-alike (ex.: MapBiomas CC BY-SA), avaliar se o derivado é
  "obra derivada" e ajustar a licença;
- se houver fonte restrita (IFN), não redistribuir os dados-fonte; redistribuir apenas agregados
  quando permitido.

**Decisão atual (2026-11-17):**

- **Código:** MIT (já no repositório).
- **Documentação:** CC BY 4.0.
- **Produtos de dados (mapas, tabelas, pesos):** a definir; candidato CC BY 4.0, com NOTICE de
  atribuição. Enquanto houver dependência do MapBiomas, avaliar caso a caso se o produto é obra
  derivada; a alternativa segura é distribuir apenas os produtos próprios (AGB/BGB) e não as
  camadas MapBiomas reprojetadas/reclassificadas.
- **Share-alike não é contagioso por uso:** usar o MapBiomas como insumo não obriga a licenciar
  o mapa de biomassa sob CC BY-SA; a obrigação recai sobre cópias/adaptações do dado MapBiomas.

## 5. Dados sensíveis

- Coordenadas de parcelas em UC/TI, espécies ameaçadas, áreas protegidas: avaliar risco.
- Política sugerida: generalizar coordenadas em publicações; manter precisão apenas internamente.
- Conformidade com LGPD se houver dados pessoais (proprietários rurais, por exemplo).

## 6. Segurança

- Não versionar credenciais (tokens, senhas, chaves) em repositório.
- Usar variáveis de ambiente/arquivos locais ignorados pelo git.
- Acessos a serviços (ex.: GEE) via conta institucional, se aplicável.

## 7. Proveniência

Cada artefato tem:

- fonte(s) e versão(ões);
- data de acesso;
- transformação aplicada;
- licença;
- responsável.

Isso é registrado no manifesto (`docs/19`) e no catálogo (`docs/05`).

## 8. Conformidade com políticas institucionais

Se o trabalho for publicado por instituição (universidade, órgão), verificar:

- política de dados abertos;
- exigência de depósito em repositório institucional;
- revisão jurídica para licenças share-alike.

## 9. Entregáveis de governança

1. `data/catalogo_dados.csv` preenchido com licenças.
2. Seção de fontes em todo relatório.
3. Licença dos produtos definida.
4. Política de dados sensíveis.
5. Registro de aprovações (se houver).
