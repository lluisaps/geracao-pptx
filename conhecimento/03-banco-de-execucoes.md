# Banco de execuções

MySQL da Yank. Credenciais no `.env` (`DB_HOST`, `DB_PORT`, `DB_NAME`,
`DB_USER`, `DB_PASS`) — usuário **somente leitura**, restrito às tabelas de
execução. Host e nome da base nunca vão para arquivo versionado.

## Onde estão as execuções

Cada robô grava numa tabela própria, no padrão `yank_<número do cliente>` (às
vezes com sufixo). **A tabela de um robô sai da planilha** (ver 06) — nunca
de descoberta pelo banco. A antiga descoberta por `vw_robo_cliente` →
`sis_robo_execucao` foi removida: várias tabelas em uso não têm vínculo ali.

Colunas que o gerador usa em toda tabela de execução:

| Coluna | Uso |
|---|---|
| `time_exec` | data/hora da execução — define o mês |
| `status_execucao` | texto do resultado — vira balde (ver 07) |

Algumas tabelas têm colunas de quebra (`PORTAL`, `CLIENTE`, `ETAPA`), usadas
quando a OBS da planilha manda separar o gráfico.

## A consulta

```sql
SELECT YEAR(time_exec) AS ano, MONTH(time_exec) AS mes,
       status_execucao, COUNT(*) AS quantidade
FROM `<tabela>`
WHERE time_exec >= '<1º dia do 1º mês>' AND time_exec < '<1º dia do mês seguinte ao 3º>'
GROUP BY YEAR(time_exec), MONTH(time_exec), status_execucao
```

- faixa meio-aberta (`>=` / `<`): usa índice e atravessa virada de ano;
- várias tabelas do mesmo robô **somam** (só quando a planilha autoriza);
- nome de tabela é validado (`[A-Za-z0-9_]`) antes de entrar no SQL; coluna de
  quebra nunca entra por variável — só as escritas em `SQL_QUEBRA`.

## O que sai daqui

- gráfico de execuções (total por mês) e o cartão de itens processados;
- quebra por status → assertividade, itens entregues, tabela de volume,
  destaques de prevenção.

## Scripts de apoio (todos só leitura)

| Script | Para quê |
|---|---|
| `execucoes.py` | a consulta acima, isolada |
| `probe.py <tabela> <coluna>` | valores distintos de uma coluna (achar a quebra) |
| `checar_robos.py` | confere se as tabelas existem e têm as colunas |
| `fumaca.py <ini> <fim>` | roda todos os robôs e confere totais |

## Alertas

- **Mês zerado** com os outros cheios: alerta. Confira tabela, robô parado,
  migração de tabela — antes de gerar.
- Quebra que não soma o mesmo que os status: o script avisa; não gere sem
  entender.
- Robô novo: o script **para** listando os status sem classificação (ver 07).
