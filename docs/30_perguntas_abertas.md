# 30 — Perguntas abertas

Pendências que **exigem decisão do usuário** ou verificação externa. Nenhuma foi respondida por
suposição. Cada item indica por que importa e qual é o padrão provisório adotado até a resposta.

## 1. Escopo e produto

**Q1. Dados pagos são permitidos?**
- Importa: define se imagens comerciais, LiDAR dedicado e bases privadas entram no escopo.
- Padrão provisório: **não**; apenas dados abertos (redflag RF01/RF02).
- Impacto: alto.

**Q2. Existe acesso a inventários de campo (IFN, empresas, ONGs, universidades)?**
- Importa: sem campo independente, a validação é condicional a GEDI.
- Padrão provisório: usar compilação pública de artigos/teses; declarar limitação.
- Impacto: alto.

**Q3. Quais anos-alvo e qual cadência?**
- Importa: define volume, série e custo. A série de desmatamento é recomendada de 2016 em diante.
- Padrão provisório: 2016–2025, anual.
- Impacto: alto.

**Q4. "Biomassa" inclui BGB por padrão?**
- Importa: BGB aumenta o total e a incerteza de forma material.
- Padrão provisório: AGB como produto principal; BGB como módulo com cenários.
- Impacto: alto.

**Q5. GEDI L4A (produto de modelo) é aceitável como referência principal?**
- Importa: define a viabilidade de escala nacional.
- Padrão provisório: sim, com filtros, AOA e validação independente; declaração explícita.
- Impacto: alto.

**Q6. Quais limites de acurácia são aceitáveis?**
- Importa: define aprovação/reprovação (`docs/25`).
- Padrão provisório: viés ≤10%; RMSE ≤30% (Amazônia) / ≤40% (Cerrado); cobertura IC90 80–95%.
- Impacto: alto.

## 2. Ambiente e governança

**Q7. Google Earth Engine pode ser usado?**
- Importa: termos podem restringir uso comercial/redistribuição; cria dependência.
- Padrão provisório: não na trilha principal (ADR-0001).
- Impacto: médio.

**Q8. Qual licença para os produtos (mapas, tabelas, pesos)?**
- Importa: restrições de fontes (ex.: share-alike do MapBiomas) condicionam a escolha.
- Padrão provisório: CC BY 4.0, sujeito a revisão de compatibilidade.
- Impacto: médio.

**Q9. Ambiente de execução: local, HPC ou nuvem?**
- Importa: define tempo, custo e arquitetura.
- Padrão provisório: local com processamento por janelas; HPC opcional.
- Impacto: médio.

## 3. Unidade de relato e uso

**Q10. O relato é por bioma, por classe, por município/UC/TI ou por polígono?**
- Importa: define o estimador e o produto final.
- Padrão provisório: bioma × classe × ano, com consulta por polígono.
- Impacto: alto.

**Q11. A mudança temporal (ΔAGB) é obrigatória?**
- Importa: dobra o esforço e a incerteza.
- Padrão provisório: fase 6 (opcional), após o produto de estoque.
- Impacto: médio.

**Q12. Há exigência de MRV (GHG Protocol, Verra, órgão regulador)?**
- Importa: MRV exige protocolos, auditoria e incerteza mais rígidos.
- Padrão provisório: padrão científico, não certificação.
- Impacto: alto.

**Q13. Qual é a unidade mínima de mapeamento e o tamanho mínimo de polígono?**
- Importa: define o que pode ser respondido sem estimativa instável.
- Padrão provisório: não estimar polígonos com < 10 pixels válidos; sinalizar.
- Impacto: médio.

**Q14. Quem aprova versões de modelo e produtos?**
- Importa: governança e responsabilização.
- Padrão provisório: revisão por par interno + registro em ADR.
- Impacto: baixo/médio.

## 4. Verificações externas pendentes

**Q15. Versão exata da coleção MapBiomas e data de acesso.**
- Necessário para citação e reprodutibilidade.

**Q16. Acesso e formato dos microdados do IFN.**
- Necessário para validação independente.

**Q17. Versões e licenças de WorldClim/CHELSA/CHIRPS/SoilGrids.**
- Necessário para conformidade.

**Q18. Versão do produto GEDI L4A e critérios de filtro recomendados.**
- Necessário para reprodutibilidade da referência.

**Q19. Status e política de NISAR/BIOMASS.**
- Não bloqueia; monitorar.

**Q20. Título/DOI completos de referências parciais (PLOS ONE 2018, STOTEN 2023, Roitman 2018).**
- Necessário antes de citar na bibliografia final.

## 5. Ordem recomendada de resolução

1. Q1, Q3, Q4, Q5, Q6 (definem a viabilidade e o aceite).
2. Q10, Q12 (definem o produto e o rigor).
3. Q2, Q15–Q18 (viabilizam referência e reprodução).
4. Q7, Q8, Q9 (ambiente e licença).
5. Q11, Q13, Q14, Q19, Q20 (refinamentos).

## 6. Regra

Enquanto uma pergunta não for respondida:

- o padrão provisório é usado **e declarado** em todo artefato;
- a decisão é registrada como provisória no ADR correspondente;
- nenhum resultado é apresentado como definitivo se depender da resposta.
