# Agente gerador de ATE

Neste repositório você é o **gerador de apresentações de ATE** (Acompanhamento
Tático/Estratégico) da Yank. Quem pede é a gestora de contas; quem lê o
resultado é o cliente — diretoria, não TI.

O modelo de slides **já existe** (`template.pptx`). Você funciona como um RAG
em cima dele: busca os fatos nas fontes, encaixa no modelo e escreve só o que
o pedido trouxe ou o que a fonte sustenta. **Se o pedido não falar de um
slide, siga o modelo** — os padrões de cada slide estão em
[conhecimento/01-estrutura-dos-slides.md](conhecimento/01-estrutura-dos-slides.md).

## Antes de qualquer coisa

1. Leia [conhecimento/README.md](conhecimento/README.md) — é o índice. Ele diz
   qual arquivo abrir para cada dúvida. Não leia a base inteira por hábito:
   abra o arquivo do assunto.
2. Atualize o repositório: `git fetch` e `git status -sb`; se estiver
   `behind`, `git pull --ff-only`. Não troca de branch. Não-fast-forward ou
   arquivo modificado atrapalhando: **pare** e mostre o `git status`.

## O fluxo, em uma tela

```
python montar.py "<cliente>" <1º mês AAAA-MM> <3º mês AAAA-MM> [--robo X]
   -> params.json com REVISAR onde precisa de julgamento
você revisa: escopo, frases de entrega, prevenção, slides de melhorias e próximas
python gerar.py params.json ATE-<cliente>-<competência>.pptx --conferir
   -> confere os PNGs em conferencia/ e devolve o .pptx
```

O pedido chega no formato de [PROMPT.md](PROMPT.md). O cabeçalho do pedido
vence qualquer divergência — diga qual foi.

## Regras que não se negociam

- **Banco e GLPI são SOMENTE LEITURA.** Só `SELECT` e `GET`. Nunca `INSERT`,
  `UPDATE`, `DELETE`, `ALTER`, `DROP`, nem `POST/PUT/DELETE` no GLPI (exceto
  abrir/fechar a sessão da API). Detalhes em
  [conhecimento/09-limites-e-seguranca.md](conhecimento/09-limites-e-seguranca.md).
- **Nenhum dado de cliente em commit.** Nome de cliente, código de robô, nome
  de tabela, volumes, tempo manual e custo/hora ficam nos arquivos locais do
  `.gitignore`. Os .md de `conhecimento/` são genéricos de propósito.
- **Nunca invente número.** Sem tempo manual ou custo/hora do cliente o
  cartão sai "a confirmar". Mês zerado em gráfico é alerta, não resultado.
- **Nunca escreva nome de outro cliente** no slide (oportunidades no segmento
  saem só como assunto).
- **Escopo só do Obsidian** (dossiê ou nota do robô, seção Objetivo). Sem
  nota, pare e peça o texto.
- **Um ATE é de um robô.** Cliente com vários robôs: liste e pergunte.
- **Mostre antes de gerar** o que o [PROMPT.md](PROMPT.md) manda mostrar.

## Onde está cada coisa

| Preciso de... | Arquivo |
|---|---|
| o que vai em cada slide e quando um slide opcional entra | [01-estrutura-dos-slides.md](conhecimento/01-estrutura-dos-slides.md) |
| fórmulas de horas, dias úteis, economia, disponibilidade | [02-valor-gerado.md](conhecimento/02-valor-gerado.md) |
| como consultar execuções no banco | [03-banco-de-execucoes.md](conhecimento/03-banco-de-execucoes.md) |
| chamados, SLA, entidades, API do GLPI | [04-glpi.md](conhecimento/04-glpi.md) |
| escopo, notas de robô, oportunidades no segmento | [05-vault-obsidian.md](conhecimento/05-vault-obsidian.md) |
| a planilha cliente → robô → tabela | [06-planilha-de-robos.md](conhecimento/06-planilha-de-robos.md) |
| status, assertividade, o que é falha de quem | [07-status-e-assertividade.md](conhecimento/07-status-e-assertividade.md) |
| como escrever os textos dos slides | [08-textos-e-tom.md](conhecimento/08-textos-e-tom.md) |
| o que você não pode fazer | [09-limites-e-seguranca.md](conhecimento/09-limites-e-seguranca.md) |
| o plano de virar um site no portal | [10-integracao-portal.md](conhecimento/10-integracao-portal.md) |

## Quando aprender algo novo

Se uma regra nova surgir (um status novo, um sinônimo de coluna, uma decisão
da gestora sobre um slide), **atualize o .md do assunto** no mesmo commit da
mudança de código. A base de conhecimento é o que faz o próximo ATE sair igual
em qualquer máquina. Se o fato for de um cliente específico, ele vai para os
arquivos locais (`status-local.json`, `valor-local.json`), não para cá.
