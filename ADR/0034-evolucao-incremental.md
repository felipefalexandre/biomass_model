# ADR-0034 — Evolução incremental do repositório (sem reestruturação integral)

- **Data:** 2026-11-27
- **Status:** aceito
- **Relaciona-se a:** ADR-0027, ADR-0030, ADR-0032, ADR-0033; `docs/46` §8

## Contexto

O plano de target observado e features (`docs/61`, `docs/62`) adiciona duas etapas
que ainda não tinham módulo próprio: a consolidação de **um target por UA** e o
**catálogo executável de features**. Isso abriu a discussão entre (a) seguir com
essas etapas e (b) reestruturar o repositório inteiro para o novo plano.

A auditoria de escopo (`docs/46` §8.1) já havia decidido o princípio:

> “Não fazer uma reconstrução integral. Preservar o que funciona e evoluir por
> contratos. A estrutura abaixo é conceitual; a organização física pode ser
> incremental.”

O estado atual confirma o custo de uma reconstrução: mais de 20 módulos em
`src/biomass_model/`, **44 comandos** no CLI, **23 arquivos de teste** e uma suíte
verde. Os fluxos já validados (`polygon`, `annual-map`, `mrv-check`,
`train-field`, `inventory-store`) dependem dos caminhos e assinaturas atuais.
Mover módulos agora quebraria imports, testes, comandos, documentação e
artefatos sem ganho científico.

## Decisão

1. **Não fazer reestruturação integral.** O repositório evolui por módulos
   aditivos e contratos estáveis.
2. Novas capacidades entram como arquivos/pacotes novos, sem mover nem renomear
   o que já existe:
   - `targets.py`: consolida o target observado (1 linha por UA, Tier A/B,
     min/mediana/max, suporte e flags) e exporta CSV/GeoPackage/manifesto;
   - `feature_catalog.py`: valida `data/reference/features_biomassa.csv`,
     seleciona conjuntos por grupo/prioridade e calcula `feature_set_hash`.
3. **Contratos preservados:** nomes de pacotes e módulos, comandos do CLI,
   esquema canônico de observações (`inventory/schema.py`), caminhos de
   artefatos documentados e o formato dos produtos existentes.
4. **Regras científicas do target** ficam no código, não só no documento:
   1 target por UA; Tier A (pixel 30 m) tem precedência sobre Tier B (célula
   ~1,1 km); pixels-irmãos contam como `n_repeticoes`, não como amostras
   independentes; `agb_mg_ha` é a mediana entre equações; nenhuma feature
   derivada de AGB, GEDI ou LiDAR entra na tabela.
5. O catálogo de features é a fonte executável do contrato: features
   `vedada_como_feature` (GEDI, LiDAR, ICESat-2, lon/lat) são sempre excluídas;
   `permitida_experimental` (SOC) exige opt-in explícito para ablação.
6. **Reavaliar** uma reestruturação apenas se ocorrer um gatilho objetivo:
   duplicação real de pipeline, publicação como biblioteca com API pública,
   CLI acima de ~60 comandos, múltiplos mantenedores ou divergência de
   contratos de dados. Nenhum está ativo em 2026-11-27.

## Consequências

- O plano avança sem uma pausa de engenharia de semanas e sem regressão nos
  fluxos já validados.
- A dívida técnica fica **localizada e nomeada**: `features.py` e
  `observation_features.py` continuam módulos separados (um importa do outro,
  não há duplicação); uma futura unificação pode ocorrer sob demanda.
- O target e o conjunto de features passam a ter comando, teste, hash e
  manifesto próprios, pré-requisito para o registro champion/challenger
  (ADR-0033).
- Artefatos derivados grandes continuam fora do Git; caminhos e hashes ficam
  nos manifestos.

## Arquivos

`src/biomass_model/targets.py`, `src/biomass_model/feature_catalog.py`,
`src/biomass_model/cli.py`, `tests/test_targets.py`,
`tests/test_feature_catalog.py`, `docs/63_target_consolidado.md`.
