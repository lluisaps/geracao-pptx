# Gerador de ATE em .pptx

Gera a apresentação de Acompanhamento Tático/Estratégico a partir do template
institucional da Yank. A saída é um `.pptx` **nativo**: texto selecionável,
gráficos de verdade, tudo editável no PowerPoint.

O layout, as fontes, as cores e a decoração vêm intactos do `template.pptx` —
o gerador só troca conteúdo.

## Requisitos

- Python 3
- `python-pptx` — `python -m pip install python-pptx`

Só isso. Roda em Windows, Linux e macOS.

## Usar

```bash
python gerar.py params.json ATE-<cliente>-<competencia>.pptx
```

Para conferir visualmente antes de entregar:

```bash
python gerar.py params.json ATE-<cliente>-<competencia>.pptx --conferir
```

O `--conferir` exporta os 8 slides em imagem. Ele se vira com o que existir no
ambiente: **PowerPoint** (Windows, via `pywin32`) ou **LibreOffice** (qualquer
sistema, via `soffice`). Se não achar nenhum dos dois, avisa e segue — o
`.pptx` sai igual, só sem a conferência automática. Nada disso é necessário
para gerar.

## O logo do cliente

Obrigatório. Sem ele o gerador **para com erro** em vez de produzir uma capa
com o logo que veio no template, ou seja, o de outro cliente.

O gerador procura em duas ordens: ao lado do `params.json` (o arquivo anexado
no pedido) e depois em `logos/`. Clientes recorrentes ficam em `logos/` e não
precisam ser reenviados a cada mês.

Quando o logo do cliente não existir mesmo, use `sem-logo.png` — um PNG
transparente de 342×101 versionado na raiz. A caixa da capa fica **vazia**, que
é diferente de deixar o campo em branco: sem `logo_cliente` o gerador para, e
qualquer bypass deixaria na capa o logo que veio no template (o da Cliente Exemplo),
ou seja, o de outro cliente.

Para um ATE novo, copie o `params.exemplo.json` para `params.json`, ajuste os
valores e rode. O [PROMPT.md](PROMPT.md) tem o texto pronto para pedir isso a
uma IA.

## Nada de dado de cliente no repositório

`robos.csv`, `params.json` e a pasta `logos/` são **locais** e estão no
`.gitignore`, junto com o `.env`. Eles carregam nome de cliente, tabela do
banco, volume de execução e logo — nada disso entra em commit. O que fica
versionado é só o mecanismo: os scripts, o template e este README. O
`params.exemplo.json` é fictício de propósito.

## O que cada campo preenche

| Campo | Slide | O que muda |
|---|---|---|
| `competencia` | 1 | data na pílula ao lado do título |
| `logo_cliente` | 1 | logo do cliente, encaixado na caixa mantendo a proporção |
| `resumo_escopo` | 2 | descrição da etapa 1 da agenda |
| `escopo_objetivo` | 3 | texto do escopo; `**termo**` sai com realce amarelo |
| `grafico_execucoes.titulo` | 4 | título acima do gráfico |
| `grafico_execucoes.assertividade` | 4 | nota à direita do gráfico |
| `grafico_execucoes.meses` / `execucoes` | 4 | uma barra por mês, com o total do mês |
| `grafico_execucoes.categorias` / `series` | 4 | alternativa: gráfico quebrado, uma série por mês |
| `grafico_sla.meses` / `chamados` / `dentro_do_sla` | 5 | dados do gráfico |
| `dificuldades` | 6 | tópicos das duas colunas |
| `pontos_de_atencao` | 7 | tópicos das duas colunas |

Os textos aceitam `**assim**` para destacar: amarelo no slide 3, negrito nos
slides 6 e 7.

## De onde vem a tabela do robô

Do `robos.csv`, um arquivo **local**, na raiz do projeto ao lado do `.env`. Ele
não é versionado — veja a seção acima. Quatro colunas:

| Coluna | Para que serve |
|---|---|
| `cliente` | repetido em toda linha; o casamento ignora acento e caixa |
| `robo` | chave de agrupamento — **linhas com o mesmo rótulo somam** |
| `tabela` | a `yank_...` de execuções |
| `quebra_por` | coluna de quebra, quando o gráfico não é só o total do mês |

O normal é passar só o cliente. Quando ele tem mais de um robô, o script lista
as opções com o volume de cada uma no período e para:

```
o cliente '<cliente>' tem 2 robôs no robos.csv:

robô                             no período   tabela(s)
<rótulo A>                       2537         <tabela>, <tabela>
<rótulo B>                       274          <tabela>, <tabela>, <tabela>
```

Aí você repete com o robô no quarto argumento:

```bash
python execucoes.py "<cliente>" 2026-04 2026-06 "<rótulo B>"
```

Ele não escolhe sozinho de propósito: um ATE é de **um robô**, não de um
cliente — o escopo do slide 3 descreve um robô específico, e somar dois daria
um gráfico que não corresponde a texto nenhum.

O CSV é a **única** fonte da tabela. Não existe descoberta pelo banco: cliente
que não estiver no arquivo faz o script parar e pedir a linha, em vez de
adivinhar. A descoberta antiga (`vw_robo_cliente` → `sis_robo_execucao`) foi
removida porque não dava para confiar nela — **nove das tabelas em uso não têm
vínculo em `sis_robo_execucao`** e eram invisíveis por ali, o que tornava
alguns robôs impossíveis de gerar.

Os rótulos da coluna `robo` são os da planilha de origem, não os nomes
cadastrados no banco. Onde os dois divergem, vale a planilha: o rótulo existe
para ser digitado por quem pede o ATE.

O `checar_robos.py` confere o CSV contra o banco: existência das tabelas,
presença de `time_exec`/`status_execucao`, o robô que o banco associa a cada
uma e os valores distintos das colunas de quebra. O `fumaca.py` passa todos os
robôs do CSV pela consulta de verdade e confere se os totais fecham.

## O gráfico quebrado

Alguns robôs não querem o total do mês, e sim a divisão por uma coluna da
tabela. Quem diz isso é a coluna `quebra_por` do `robos.csv`, com o nome da
coluna em maiúsculas. As quebras reconhecidas estão em `SQL_QUEBRA`, no
`execucoes.py`.

Nesses casos o `execucoes.py` roda uma **segunda** consulta, agrupada por essa
coluna, e devolve o bloco com `categorias` e `series` no lugar de `meses` e
`execucoes`. O gráfico passa a ter uma série por mês e uma categoria por valor
— que é exatamente como o gráfico nasceu no template; o gerador é que vinha
descartando as séries extras para forçar a barra única.

As duas consultas têm que dar o mesmo total. Quando não dão, o script avisa em
vez de deixar passar.

## SLA direto do GLPI

O `glpi_sla.py` puxa os chamados pela API REST e devolve o bloco `grafico_sla`
pronto, dispensando o export manual:

```bash
set GLPI_APP=<app_token>
set GLPI_USER=<user_token>
python glpi_sla.py "<cliente>" 2026-04 2026-06
```

Os tokens vêm do ambiente — nunca de arquivo versionado. Aplica as regras da
documentação canônica do indicador: exclui categoria *Monitoramento*, tickets
`[Projeto] -` e a entidade interna; conta pelo mês da data de abertura; e
trata **chamado sem prazo de SLA como dentro do prazo**.

O SLA geral é `(dentro + sem_sla) / (dentro + sem_sla + fora)` — repare que o
denominador não é o total: chamados ainda abertos ficam de fora.

Mês sem nenhum chamado sai como `—`, não como `0%`.

## Os cartões de SLA são calculados

Você **não** informa os números dos três cartões do slide 5. Eles saem dos
dados do gráfico:

```
total   = soma de chamados
dentro  = soma de dentro_do_sla
fora    = total - dentro
%dentro = dentro / total
%fora   = 100 - %dentro
```

Assim os cartões nunca discordam do gráfico. O gerador imprime os valores no
terminal para conferência.

## Numeração dos tópicos

Os tópicos dos slides 6 e 7 são numerados automaticamente e **a numeração
continua da coluna da esquerda para a da direita** — dois tópicos à esquerda
fazem a direita começar em 3. Não escreva o número no texto.

## Estrutura

```
versionado:
  gerar.py             o gerador
  template.pptx        o modelo institucional (não editar)
  params.exemplo.json  exemplo fictício, copie para params.json
  execucoes.py         extrai as execuções do trimestre
  glpi_sla.py          extrai o SLA do GLPI
  checar_robos.py      confere o robos.csv contra o banco
  fumaca.py            roda todos os robôs do CSV e confere os totais
  PROMPT.md            prompt pronto para pedir um ATE novo

local, nunca versionado:
  .env                 credenciais do banco e do GLPI
  robos.csv            cliente -> robô -> tabela(s) -> quebra
  params.json          o ATE que você está montando agora
  logos/               os logos dos clientes
```

## Detalhes de implementação

Os gráficos do template apontam para uma planilha **externa**, que não existe
mais. Por isso o `chart.replace_data()` do python-pptx não funciona aqui — o
gerador escreve direto no cache embutido do gráfico, que é de onde o PowerPoint
desenha. Efeito colateral: clicar em "Editar Dados" no PowerPoint tenta abrir a
planilha ausente. Isso já acontecia no template original.

A nota de assertividade fica num desenho dentro do gráfico
(`ppt/drawings/drawing1.xml`), que o python-pptx não expõe; ela é aplicada num
segundo passo, direto no pacote.
