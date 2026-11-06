# Valor gerado

O ATE mostra **valor de negócio**: quanto trabalho o robô tirou da equipe do
cliente e quanto isso vale. Tudo aqui é **estimativa** e o slide diz isso.

## As contas

```
itens processados = total de execuções do trimestre (banco, todos os status)
itens entregues   = execuções com status de SUCESSO (ver 07)
horas poupadas    = itens entregues × minutos manuais por item ÷ 60
dias úteis        = horas poupadas ÷ 8
economia          = horas poupadas × custo/hora da equipe
```

- **Exceção de negócio não entra nas horas**: não foi trabalho poupado.
- **Tempo manual e custo/hora são do cliente.** Vêm do cabeçalho do pedido e
  vão para o `valor-local.json`, por código de robô. Em branco: "a confirmar".
  Nunca use tempo padrão, nunca copie de outro robô, nunca deduza.
- Se o número foi combinado internamente e não veio do cliente, preencha
  `valor_gerado.origem` (ex.: "estimados pela equipe Yank") — a nota de rodapé
  muda de acordo.

## valor-local.json (local, fora do git)

```json
{
  "ABC01": {
    "minutos_por_item": 4,
    "custo_hora": 55,
    "entregas": {
      "<STATUS DE SUCESSO EXATO>": "<frase de negócio, sem o número>"
    }
  }
}
```

Com `entregas` preenchido, só os status listados contam como itens entregues,
cada um com a frase dele. Sem isso, entra todo status de sucesso com texto
cru e `REVISAR` — proponha as frases (só o que o status diz) e grave **depois
que a gestora aprovar**.

## Disponibilidade

Não existe registro confiável de "robô fora do ar": as tabelas de
monitoramento do banco pararam em 2022, e o intervalo entre execuções não
serve (os robôs rodam por demanda — dia sem execução é dia sem demanda).

Estimativa pelo GLPI (`glpi_sla.disponibilidade`):

- contam os chamados de **Sustentação** (Correção, Análise), da abertura à
  solução, do nó do robô ou do ambiente do cliente;
- **Monitoramento não conta** (checagem de rotina);
- chamados de outros robôs do mesmo cliente ficam de fora;
- faixas sobrepostas se juntam; base = horas corridas do período (24x7);
- sai também **mês a mês** (o "Julho 99,8%, agosto 99,9%" que a gestora
  pediu), na linha de baixo do cartão do slide 4 e na coluna do slide 3.

Percentual **arredondado para baixo** (99,99 → 99,9%): 100% só sem nenhuma
parada. Quem tiver número melhor (healthcheck) põe em
`disponibilidade.percentual` com `disponibilidade.fonte`.

## Formato dos números

- milhar com ponto: `96.878`;
- dinheiro curto: `R$ 950`, `R$ 53,2 mil`, `R$ 1,4 mi`;
- percentual com uma casa, piso: `99,9%`.
