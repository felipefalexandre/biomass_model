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
| [0003](0003-gedi-referencia.md) | GEDI L4A como referência principal | aceito com ressalva |
| [0004](0004-inferencia-hibrida.md) | Inferência híbrida | aceito |
| [0005](0005-bgb-cenarios.md) | BGB derivada com cenários | aceito |
| [0006](0006-validacao-espacial.md) | Validação por blocos espaciais e AOA | aceito |
| [0007](0007-carbono-modulo.md) | Carbono e CO₂e em módulo separado | aceito |
| [0008](0008-janelas-cog.md) | Janelas e COG | aceito |
| [0009](0009-mascara-dominio.md) | Máscara de elegibilidade como domínio | aceito |
