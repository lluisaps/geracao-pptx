# GLPI

Sistema de chamados da Yank. Acesso pela **API REST** (`apirest.php`),
credenciais no `.env`: `GLPI_URL`, `GLPI_APP` (app token — Configurar → Geral
→ API → Clientes de API), `GLPI_USER` (user token — Preferências → Tokens de
API). O endpoint não vai para arquivo versionado.

## Como o gerador usa a API

1. `GET /initSession` com os tokens → `Session-Token`;
2. `GET /search/Entity` → resolve o nome do cliente para o(s) **id(s) de
   entidade** (o nó do cliente e todas as sub-entidades);
3. `GET /search/Ticket` filtrando por id de entidade (nunca por nome);
4. `GET /killSession` no fim.

Só `GET` (e abrir/fechar sessão). O agente **não cria, edita, atribui nem
fecha chamado**.

Campos do Ticket usados (ids do `listSearchOptions/Ticket`):

| id | campo |
|---|---|
| 1 | título |
| 2 | id |
| 7 | categoria |
| 12 | status |
| 15 | abertura |
| 17 | solução |
| 18 | prazo (time_to_resolve) |
| 80 | entidade |

## Entidades

A árvore é `Yank Solutions! > Tech Team Produto > Squads > <squad> > Clientes
> <cliente> > <robô>`. O script **imprime os nós usados** — confira que são os
do cliente. Nome que não casa com nenhuma entidade é **erro, não zero**.
`--entidade <id>` força à mão.

O nó do chamado (`_no_do_chamado`) é como se sabe de qual robô ele é: chamado
aberto no nó de outro robô do mesmo cliente não conta na disponibilidade deste.

## SLA (regra do indicador canônico — workflow n8n "GLPI - Dashboard Indicators")

```
dentro   = solução <= prazo
fora     = solução >  prazo
em_risco = sem solução e já passou do prazo
sem_sla  = prazo nulo  -> CONTA COMO DENTRO
SLA      = (dentro + sem_sla) / (dentro + sem_sla + fora)
```

Chamado ainda aberto fica fora do denominador. Mês sem chamado sai `—`.

### Exclusões do dashboard

- categoria contendo **Monitoramento**;
- título começando com **`[Projeto] -`**;
- entidade interna **Yank Solutions!**.

O ATE roda com **`--tudo`** (exclusões desligadas): o gráfico é **volume** de
chamados do cliente, e cliente com quase tudo em Monitoramento sairia com
meses zerados. É divergência **deliberada** do Dashboard Sustain — o script
sempre imprime quantos chamados cada regra teria descartado. Não unifique sem
decisão da gestora.

## Categorias que importam

| Categoria | Uso no ATE |
|---|---|
| Sustentação › Correção / Análise | entra na disponibilidade; conta como pista de prevenção |
| Melhoria | pista para o slide de melhorias (o título não diz O QUE foi feito) |
| Monitoramento | fica fora da disponibilidade (rotina) |

## Antes de gerar, mostre

Chamados mês a mês com a linha de exclusões; a linha "entidade(s) do cliente";
os chamados que entraram na disponibilidade (data, categoria, título).
