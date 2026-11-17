# 11 — Carbono e CO₂e

## 1. Regra de ouro

**Biomassa, carbono e CO₂e são grandezas distintas.** Toda tabela publicada deve declarar a
unidade no cabeçalho. Nunca apresentar "carbono" como sinônimo de "biomassa".

| Grandeza | Unidade | Definição |
|---|---|---|
| biomassa | Mg (matéria seca) | massa física |
| carbono | Mg C | carbono contido na biomassa |
| CO₂e | Mg CO₂e | equivalente em CO₂ |

## 2. Conversões

### 2.1 Biomassa → carbono

```
C = f_C × B
```

- `f_C` é a **fração de carbono** da matéria seca.
- Padrão comum: `f_C = 0,47` (IPCC). **A confirmar na tabela oficial aplicável** (as diretrizes
  trazem valores por componente e por tipo de floresta; o valor único é uma simplificação).
- Alternativa: medir `f_C` por componente (madeira, folhas, raízes) — mais preciso, raramente
  disponível.

### 2.2 Carbono → CO₂e

```
CO₂e = C × (44 / 12)
```

- `44/12 ≈ 3,6667` (massa molar CO₂ / massa molar C).
- Se houver CH₄ ou N₂O, usar potenciais de aquecimento globais (GWP) da versão do relatório
  IPCC adotada e declarar. Neste projeto, o padrão é **apenas CO₂**; outros gases ficam fora,
  salvo pedido explícito.

### 2.3 Cadeia completa

```
AGBD (Mg ha⁻¹) ──× área──► AGB (Mg)
AGB + BGB ─────────────► TB (Mg)
TB × f_C ──────────────► C (Mg C)
C × 44/12 ─────────────► CO₂e (Mg CO₂e)
```

## 3. Exemplo numérico ilustrativo (não é resultado do projeto)

Suponha, apenas para checar a aritmética, um polígono de 100 ha com AGBD média de 100 Mg ha⁻¹,
R:S = 0,30 e f_C = 0,47:

```
AGB   = 100 ha × 100 Mg ha⁻¹ = 10.000 Mg
BGB   = 0,30 × 10.000        =  3.000 Mg
TB    = 13.000 Mg
C     = 0,47 × 13.000        =  6.110 Mg C
CO₂e  = 6.110 × 44/12        = 22.403,3 Mg CO₂e
```

Checagem rápida: CO₂e ≈ 3,67 × C; C ≈ 0,47 × TB. Um erro de 10% em `f_C` desloca C e CO₂e em
10%; um erro de 10% em AGB desloca tudo em 10%. Isso mostra por que a incerteza de AGB domina.

## 4. Propagação de incerteza nas conversões

Se `f_C` e R:S têm incerteza, o intervalo de C e CO₂e deve incluí-las. Aproximação por
primeira ordem (independentes):

```
Var(C) ≈ (f_C)² Var(TB) + (TB)² Var(f_C)
```

e

```
Var(CO₂e) ≈ (44/12)² Var(C)
```

Se as variáveis não forem independentes (ex.: AGB e BGB correlacionadas), incluir covariância
ou usar simulação de Monte Carlo. **Não** somar desvios-padrão como se fossem independentes sem
justificar.

## 5. Convenções que devem constar no relatório

1. `f_C` usado e sua fonte.
2. Se C inclui raízes (sim/não) e necromassa (sim/não).
3. Se CO₂e inclui apenas CO₂.
4. Fator 44/12 e versão.
5. Se a massa é seca a 65 °C ou outra convenção.
6. Se o total é estoque ou fluxo (emissão/remoção).
7. Arredondamento: relatar com algarismos significativos compatíveis com a incerteza.

## 6. Estoque vs fluxo

- **Estoque:** quantidade em um instante (Mg, Mg C).
- **Fluxo:** variação por tempo (Mg ano⁻¹, Mg CO₂e ano⁻¹).
- A série de desmatamento 2014–2025 da etapa anterior permite estimar **fluxo por conversão**:
  AGBD removida × área desmatada, com ressalva sobre destino da biomassa (queima, decomposição,
  madeira) — o destino não é observável e deve ser tratado como cenário, não como fato.

## 7. Erros comuns a evitar

| Erro | Correção |
|---|---|
| somar AGB carbono + BGB biomassa | converter tudo para a mesma grandeza antes |
| aplicar 0,5 como se fosse 0,47 | declarar e usar um valor consistente |
| multiplicar C por 3,67 e chamar de "biomassa" | é CO₂e |
| usar Mg e tonelada como diferentes | 1 Mg = 1 t |
| ignorar BGB no total | incluir ou declarar explicitamente que o total é AGB |
