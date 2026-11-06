# Planilha de robôs

A `.xlsx` ao lado do `montar.py` (local, no `.gitignore`). É a **única fonte**
de qual tabela do banco pertence a qual robô. Cada gerente tem a sua carteira.

## Colunas (achadas pelo cabeçalho, nunca pela posição)

| Papel | Cabeçalhos aceitos | Obrigatória |
|---|---|---|
| cliente | `cliente`, `empresa`, `conta` | sim |
| tabela | `tabela`, `banco`, `base`, `schema`, `db` | sim |
| obs | `obs`, `observacao`, `nota`, `comentario` | não |

## A OBS manda

- **OBS preenchida abre um robô novo**; linhas de OBS vazia logo abaixo são
  dele — mas só somam se a OBS disser "pode somar", "juntar", "agrupar"…
  Sem isso, o script avisa em vez de somar calado.
- **Código do robô** sai da OBS: 2–4 letras + 2–3 dígitos (`ABC01`). Sem
  código na OBS, o vault resolve (ver 05).
- **Quebra do gráfico**: "separar pela coluna Portal", "quebrar por etapa",
  "dividir por marketplace"… O apelido é pista; a coluna real está em
  `SQL_QUEBRA` no `execucoes.py`.

## Casamento de nomes

Planilha, dossiê e GLPI escrevem o cliente de jeitos diferentes (`&` × `e`,
acento, sufixo). O casamento ignora acento, caixa e pontuação; código casa
pelo número + conjunto de letras. Onde divergirem, **vale a planilha**.

## Quando parar

- cliente fora da planilha → peça a linha; não descubra pelo banco;
- mais de um robô → liste e espere a escolha (`--robo <código>`,
  `--robo <linha>`, `--robo <linha>,<linha>` se a gestora disser que é o mesmo
  robô).
