# 30 — Perguntas abertas

Pendências que **exigem decisão do usuário** ou verificação externa. Nenhuma foi respondida por
suposição. Cada item indica por que importa e qual é o padrão provisório adotado até a resposta.

## 0. Respostas recebidas em 2026-11-17

| Pergunta | Resposta | Registro |
|---|---|---|
| Q1 (dados pagos) | Não; apenas dados abertos e ferramentas gratuitas | ADR-0001 |
| Q2 (inventários) | Usuário não tem base própria; buscar dados abertos | `data/reference/inventarios_abertos.md` |
| Q3 (anos) | Intervalo de anos, preferencialmente recentes | piloto 2018–2025 |
| Q4 (BGB) | AGB primeiro; BGB como modelo separado focado em solo, acoplado | ADR-0011 |
| Q5 (GEDI) | Aceito como referência principal, com ressalvas | ADR-0003 |
| Q6 (acurácia) | Adotar limites da literatura: viés ≤10%; RMSE ≤30% (Amazônia) / ≤40% (Cerrado); IC90 80–95% | `docs/25` |
| Q7 (GEE) | Não na trilha principal | ADR-0001 |
| Q8 (licença) | Código MIT; documentação CC BY 4.0; produtos a definir | `docs/21` |
| Q10 (unidade de relato) | Bioma e classe 3/4; estratificação por vegetação | ADR-0010 |
| Q15 (coleção MapBiomas) | Coleção 11, arquivos anuais 2004–2025 | `docs/05` |
| Q16 (IFN) | Painel de Biomassa e Carbono é aberto (CSV) | `docs/05` |
| Q20 (referências parciais) | PLOS ONE 2018 = 10.1371/journal.pone.0196742 | `docs/29` |

Perguntas ainda abertas: Q9, Q11–Q14, Q17–Q19 e o desenho temporal fino do piloto.

## 1. Escopo e produto

**Q1. Dados pagos são permitidos?** — **Respondida: não.**
- Importa: define se imagens comerciais, LiDAR dedicado e bases privadas entram no escopo.
- Decisão: apenas dados abertos e ferramentas gratuitas; dados pagos viram redflag e não entram.
- Impacto: alto.

**Q2. Existe acesso a inventários de campo (IFN, empresas, ONGs, universidades)?** — **Respondida:
não há base própria; usar dados abertos.**
- Importa: sem campo independente, a validação é condicional a GEDI.
- Decisão: compilar painel do SFB, PLOS 2018, ORNL, CEDA, EIDC, Mendeley; declarar limitações.
- Impacto: alto.

**Q3. Quais anos-alvo e qual cadência?** — **Respondida: intervalo de anos, preferencialmente
recentes, para comparar com inventários/artigos.**
- Importa: define volume, série e custo.
- Decisão: piloto 2018–2025, anual; produto principal no último ano disponível.
- Impacto: alto.

**Q4. "Biomassa" inclui BGB por padrão?** — **Respondida: AGB primeiro; BGB como modelo
separado.**
- Importa: BGB aumenta o total e a incerteza de forma material.
- Decisão: AGB é o produto v1; BGB é modelo independente de solo/clima/estrutura (ADR-0011).
- Impacto: alto.

**Q5. GEDI L4A (produto de modelo) é aceitável como referência principal?**
- Importa: define a viabilidade de escala nacional.
- Padrão provisório: sim, com filtros, AOA e validação independente; declaração explícita.
- Impacto: alto.

**Q6. Quais limites de acurácia são aceitáveis?** — **Respondida: limites da literatura.**
- Importa: define aprovação/reprovação (`docs/25`).
- Decisão: adotar viés ≤ 10%; RMSE ≤ 30% (Amazônia) / ≤ 40% (Cerrado) da média observada;
  cobertura do IC90 entre 80% e 95%; nenhum estrato com viés sistemático > 15%.
- Justificativa: são as faixas usuais em validação de AGB tropical — erro relativo da ordem de
  30% em produtos de AGB (Avitabile et al. 2016; Santoro et al. 2021) e 30–40% no GEDI L4A
  (Duncanson et al. 2022, DOI 10.1016/j.rse.2021.112845). O Cerrado recebe limite mais frouxo
  por maior heterogeneidade e referência de campo mais escassa.
- Impacto: alto.

## 2. Ambiente e governança

**Q7. Google Earth Engine pode ser usado?**
- Importa: termos podem restringir uso comercial/redistribuição; cria dependência.
- Padrão provisório: não na trilha principal (ADR-0001).
- Impacto: médio.

**Q8. Qual licença para os produtos (mapas, tabelas, pesos)?** — **Respondida parcialmente: código
MIT; documentação CC BY 4.0; produtos a definir.**
- Importa: restrições de fontes (ex.: share-alike do MapBiomas) condicionam a escolha.
- Decisão: código MIT; docs CC BY 4.0; produto candidato CC BY 4.0, com NOTICE e revisão caso a
  caso de eventual obra derivada do MapBiomas.
- Impacto: médio.

**Q9. Ambiente de execução: local, HPC ou nuvem?**
- Importa: define tempo, custo e arquitetura.
- Padrão provisório: local com processamento por janelas; HPC opcional.
- Impacto: médio.

## 3. Unidade de relato e uso

**Q10. O relato é por bioma, por classe, por município/UC/TI ou por polígono?** — **Respondida:
bioma × classe 3/4, com estratificação por tipo de vegetação.**
- Importa: define o estimador e o produto final.
- Decisão: strata bioma × classe × tipologia; consulta por polígono como recurso secundário.
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

**Q15. Versão exata da coleção MapBiomas e data de acesso.** — **Respondida:** Coleção 11,
arquivos anuais 2004–2025 em `E:\Mapbiomas\mapbiomas_col11_*.tif`; legenda oficial baixada em
`data/reference/mapbiomas/`.

**Q16. Acesso e formato dos microdados do IFN.** — **Respondida parcialmente:** o Painel de
Biomassa e Carbono é aberto (CSV, 439.970 registros, AGB por UA); dados árvore-a-árvore via SNIF,
a confirmar.

**Q17. Versões e licenças de WorldClim/CHELSA/CHIRPS/SoilGrids.**
- Necessário para conformidade.

**Q18. Versão do produto GEDI L4A e critérios de filtro recomendados.**
- Necessário para reprodutibilidade da referência.

**Q19. Status e política de NISAR/BIOMASS.**
- Não bloqueia; monitorar.

**Q20. Título/DOI completos de referências parciais (PLOS ONE 2018, STOTEN 2023, Roitman 2018).**
— **Respondida parcialmente:** PLOS ONE 2018 = `10.1371/journal.pone.0196742`; Duncanson 2022 =
`10.1016/j.rse.2021.112845`; Ribeiro 2011 = `10.1016/j.foreco.2011.04.017`. Demais seguem em
`docs/28`.

## 5. Ordem recomendada de resolução

1. Q6 (limites de acurácia) — bloqueia o aceite.
2. Q17–Q19 (versões/licenças e NISAR) — conformidade e reprodutibilidade.
3. Q9, Q11–Q14 (ambiente, temporal, MRV, unidade mínima, governança) — refinamentos.
4. Desenho temporal fino do piloto (anos de referência GEDI × mapas anuais).

## 6. Regra

Enquanto uma pergunta não for respondida:

- o padrão provisório é usado **e declarado** em todo artefato;
- a decisão é registrada como provisória no ADR correspondente;
- nenhum resultado é apresentado como definitivo se depender da resposta.
