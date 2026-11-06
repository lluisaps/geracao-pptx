# Limites e segurança

## Banco: somente leitura

- Só `SELECT`. Nunca `INSERT`, `UPDATE`, `DELETE`, `REPLACE`, `ALTER`,
  `CREATE`, `DROP`, `TRUNCATE`, `GRANT`, nem procedure que escreva.
- Mesmo que o usuário do `.env` permitisse, o agente não escreve.
- Consulta nova: sempre com filtro de período em `time_exec` e `GROUP BY` —
  nada de `SELECT *` em tabela de execução inteira.
- Tabela e coluna validadas antes de entrar no SQL (só `[A-Za-z0-9_]`).

## GLPI: somente leitura

- Só `GET` (mais `initSession`/`killSession`).
- Não abre, comenta, atribui, muda status nem fecha chamado.

## Vault: somente leitura

- O agente lê as notas; não edita o vault. Nota errada → avise a gestora.

## Git: o que pode e o que não pode entrar

| Pode commitar | Nunca commitar |
|---|---|
| scripts, `template.pptx`, `conhecimento/`, `PROMPT.md`, `README.md`, `params.exemplo.json` (fictício) | `.env`, planilha `.xlsx`, `params.json`, `params-*.json`, `status-local.json`, `valor-local.json`, `ATE*.pptx`, `conferencia/` |

Antes de commitar, confira `git diff --cached` procurando nome de cliente,
código de robô real, nome de tabela, host, token. O `.gitignore` cobre os
arquivos; o olho cobre o conteúdo.

Commit/push só quando a gestora pedir. Nunca `--force`, nunca reescrever
histórico, nunca trocar de branch sem pedido.

## Quando parar e perguntar

- clone novo sem `.env`/planilha → peça credenciais e planilha;
- cliente com vários robôs → liste e espere;
- status sem classificação → proponha e espere o ok;
- escopo sem nota no vault → peça o texto;
- tempo manual/custo em branco → gere com "a confirmar", não pergunte de novo;
- mês zerado → mostre como alerta antes de gerar;
- pull que não é fast-forward → mostre o `git status`.

## O que o agente não faz

- inventar número (tempo padrão, custo médio de mercado, reprocessamentos);
- copiar texto de ATE de outro cliente ou do trimestre passado sem reabrir a
  fonte;
- pôr logo de cliente na capa;
- mandar o .pptx para fora (e-mail, Teams) — entrega o arquivo à gestora.
