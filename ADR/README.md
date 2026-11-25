# ADR — Architecture Decision Records

Este diretório contém os registros de decisão. O texto completo, com contexto e consequências,
está em [`docs/26_registro_de_decisoes.md`](../docs/26_registro_de_decisoes.md).

Para evitar divergência, os arquivos aqui são **registros curtos** e apontam para o documento
canônico. Qualquer mudança de decisão deve:

1. criar um novo ADR (não editar o antigo como se nunca tivesse existido);
2. marcar o antigo como `substituído por ADR-XXXX`;
3. atualizar o índice em `docs/26`.

## Índice

| ADR | Decisão | Status |
|---|---|---|
| [0001](0001-python-local.md) | Python local em vez de GEE | aceito |
| [0002](0002-modelos-por-bioma.md) | Dois modelos por bioma e escada de complexidade | aceito |
| [0003](0003-gedi-referencia.md) | GEDI L4A como referência principal | aceito com ressalva; substituído parcialmente por ADR-0027 |
| [0004](0004-inferencia-hibrida.md) | Inferência híbrida | aceito |
| [0005](0005-bgb-cenarios.md) | BGB derivada com cenários | substituído por ADR-0011 |
| [0006](0006-validacao-espacial.md) | Validação por blocos espaciais e AOA | aceito |
| [0007](0007-carbono-modulo.md) | Carbono e CO₂e em módulo separado | aceito |
| [0008](0008-janelas-cog.md) | Janelas e COG | aceito |
| [0009](0009-mascara-dominio.md) | Máscara de elegibilidade como domínio | substituído por ADR-0010 |
| [0010](0010-dominio-classes-3-4.md) | Domínio = classes brutas 3 e 4 do MapBiomas | aceito |
| [0011](0011-bgb-modelo-independente.md) | BGB como modelo separado, não derivado da AGB | aceito |
| [0012](0012-filtro-qualidade-gedi.md) | Filtro de qualidade do GEDI L4A | aceito |
| [0013](0013-grade-e-amostragem.md) | Grade de modelagem e amostragem | aceito |
| [0014](0014-escala-piloto.md) | Escala do piloto | aceito |
| [0015](0015-referencia-cerrado.md) | Cerrado: campo primeiro, GEDI auxiliar | aceito |
| [0016](0016-validacao-entre-regioes.md) | Validação entre regiões | aceito |
| [0017](0017-calibracao-local.md) | Calibração local obrigatória | aceito |
| [0018](0018-historico-mapbiomas.md) | Histórico MapBiomas como feature | aceito |
| [0019](0019-area-de-aplicabilidade.md) | Área de Aplicabilidade obrigatória | aceito |
| [0020](0020-validacao-duas-linhas.md) | Validação em duas linhas + temporal | proposto |
| [0021](0021-produto-anual-estado-mudanca.md) | Produto anual de biomassa | aceito, com ressalvas |
| [0022](0022-gedi-apenas-calibracao.md) | GEDI apenas como calibração | aceito |
| [0023](0023-taxonomia-fitofisionomica.md) | Taxonomia fitofisionômica | aceito |
| [0024](0024-criterios-aceitacao.md) | Critérios de aceitação e promoção | proposto |
| [0025](0025-dominio-vs-estrato.md) | Domínio 3/4 vs estrato fitofisionômico | aceito |
| [0026](0026-produto-mapa-primeiro.md) | Produto mapa-first + tabela por polígono | aceito; resolução em ADR-0030 |
| [0027](0027-hierarquia-referencia.md) | Campo primário, GEDI auxiliar | aceito |
| [0028](0028-produto-poligono.md) | Produto C: polígono arbitrário | aceito |
| [0029](0029-fitofisionomia-ibge.md) | Fitofisionomia IBGE 1:250k | aceito |
| [0030](0030-resolucao-30m-oficial.md) | 30 m oficial, 1 km experimental | aceito |
| [0031](0031-escopo-agb-e-inventarios.md) | Escopo de AGB e inventários | aceito |
| [0032](0032-ingestao-canonica-inventarios.md) | Ingestão canônica de inventários | aceito |
| [0033](0033-champion-challenger.md) | Registro de modelos e champion/challenger | aceito |
