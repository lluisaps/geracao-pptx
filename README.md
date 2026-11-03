# Gerador de ATE em .pptx

Gera a apresentação de Acompanhamento Tático/Estratégico a partir do template
institucional da Yank, montado sobre o **modelo oficial de apresentação** (fundo
escuro, fonte Urbane). O template antigo, de fundo claro, está guardado na
branch `template-antigo`. A saída é um `.pptx` **nativo**: texto selecionável,
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

## A capa não tem logo de cliente

O modelo oficial traz só o logo da Yank na capa, fixo no template. O gerador
não lê logo de lugar nenhum e o `params.json` não tem campo de logo — não há o
que pedir, procurar ou anexar.

## Fontes

O modelo oficial usa **Urbane** (Medium e Bold). Ela precisa estar instalada
na máquina que abre o `.pptx`; sem ela o PowerPoint troca por outra fonte e os
textos mudam de largura.

## O caminho curto: `montar.py`

```bash
python montar.py "<cliente>" 2026-04 2026-06
```

Ele resolve sozinho a tabela do robô (na planilha), os textos dos slides 2 e 3
(no dossiê do Obsidian), as execuções (no banco) e os chamados (no GLPI, sempre
com `--tudo`), e escreve o `params.json`. O que depende de julgamento fica
marcado com `REVISAR:` dentro do arquivo — condensar o escopo do slide 3,
confirmar a assertividade e escrever os slides 6 e 7.

Cliente com mais de um robô faz o script listar as opções e parar: um ATE é de
um robô só. Use `--robo <código>` ou, quando o mesmo código aparecer em mais de
uma linha, `--robo <número da linha>`. `--sem-banco` monta só a parte de
planilha e dossiê, para conferir os textos antes de gastar consulta.

**Nada de caminho fixo.** O projeto é onde o `montar.py` está; a planilha é a
`.xlsx` que estiver junto dele; o vault sai do registro do próprio Obsidian, ou
da pasta que tiver um `.obsidian` dentro. As colunas da planilha são achadas
pelo cabeçalho, não pela posição, e a carteira pode ter qualquer tamanho — cada
gerente tem a sua.

Para montar à mão, copie o `params.exemplo.json` para `params.json` e ajuste os
valores. O [PROMPT.md](PROMPT.md) tem o texto pronto para pedir um ATE a uma IA.

## Nada de dado de cliente no repositório

`Tabelas Artemis.xlsx` e `params.json` são **locais** e estão no
`.gitignore`, junto com o `.env`. Eles carregam nome de cliente, tabela do
banco e volume de execução — nada disso entra em commit. Os dossiês, que trazem
os textos dos slides 2 e 3, ficam no vault do Obsidian e também não são
copiados para cá.

O que fica versionado é só o mecanismo: os scripts, o template e a
documentação. O `params.exemplo.json` é fictício de
propósito, e os exemplos do [PROMPT.md](PROMPT.md) são genéricos — nenhum nome
de cliente, código de robô ou nome de tabela real aparece em arquivo
versionado.

## O que cada campo preenche

| Campo | Slide | O que muda |
|---|---|---|
| `competencia` | 1 | data em azul, abaixo do título da capa |
| `resumo_escopo` | 2 | descrição do item 1 da agenda |
| `escopo_objetivo` | 3 | texto do escopo; `**termo**` sai em azul e negrito |
| `grafico_execucoes.titulo` | 4 | título acima do gráfico |
| `grafico_execucoes.assertividade` | 4 | nota abaixo do gráfico; vazia, a nota some |
| `grafico_execucoes.meses` / `execucoes` | 4 | uma barra por mês, com o total do mês |
| `grafico_execucoes.categorias` / `series` | 4 | alternativa: gráfico quebrado, uma série por mês |
| `grafico_sla.meses` / `chamados` / `dentro_do_sla` | 5 | dados do gráfico |
| `dificuldades` | 6 | tópicos das duas colunas |
| `pontos_de_atencao` | 7 | tópicos das duas colunas |

Os textos aceitam `**assim**` para destacar: azul no slide 3, negrito nos
slides 6 e 7.

## De onde vem a tabela do robô

Da **planilha** — a `.xlsx` que estiver ao lado do `montar.py`. Ela é local,
não versionada, e é a única fonte da tabela e da quebra no fluxo do `montar.py`.

As colunas são achadas pelo **cabeçalho**, nunca pela posição: nome da coluna,
aba e quantidade de linhas mudam sem aviso, e cada gerente tem a sua carteira.
Cada papel aceita sinônimos:

| Papel | Cabeçalhos aceitos | Obrigatória |
|---|---|---|
| cliente | `cliente`, `empresa`, `conta` | sim |
| tabela | `tabela`, `banco`, `base`, `schema`, `db` | sim |
| obs | `obs`, `observacao`, `nota`, `comentario` | não |

Planilha sem coluna de OBS apenas significa nenhum robô com quebra nem com
"pode somar". Sem as duas obrigatórias, o script para e diz o que procurou.

A **OBS** é quem carrega a inteligência. Uma OBS preenchida abre um robô novo, e
as linhas de OBS vazia logo abaixo pertencem a ele — mas só quando a OBS
autoriza, escrevendo "pode somar", "juntar", "agrupar" ou equivalente. Linha em
branco sem essa autorização faz o script **avisar em vez de somar calado**,
porque um ATE é de um robô só.

O código do robô sai da própria OBS, por padrão: duas a quatro letras seguidas
de dois ou três dígitos. Não fixa o `R` inicial nem o tamanho, porque cada
gerente numera a carteira do seu jeito.

O normal é passar só o cliente. Quando ele tem mais de um robô, o `montar.py`
lista as opções e para — ele não escolhe sozinho de propósito: o escopo do
slide 3 descreve um robô específico, e somar dois daria um gráfico que não
corresponde a texto nenhum. Aí você repete com `--robo <código>`, ou
`--robo <número da linha>` quando o mesmo código aparecer em mais de uma linha.

Não existe descoberta pelo banco. A antiga (`vw_robo_cliente` →
`sis_robo_execucao`) foi removida porque não dava para confiar nela — **nove das
tabelas em uso não têm vínculo em `sis_robo_execucao`** e eram invisíveis por
ali, o que tornava alguns robôs impossíveis de gerar. Cliente que não estiver na
planilha faz o script parar e pedir a linha, em vez de adivinhar.

Os nomes divergem entre planilha e dossiê o tempo todo (`&` contra `e`, acento
que some, letras trocadas no código do robô). O casamento ignora acento, caixa e
pontuação, e compara o código pelo número mais o conjunto de letras — onde os
dois divergirem, vale a planilha.

## O gráfico quebrado

Alguns robôs não querem o total do mês, e sim a divisão por uma coluna da
tabela. Quem diz isso é a **OBS da planilha**: "separar pela coluna Portal",
"quebrar por etapa", "dividir por marketplace" e afins são reconhecidos.

O apelido extraído da OBS é só uma pista, não a resposta — já houve OBS citando
uma coluna cujos valores estavam guardados em outra, com outro nome. Quem acha a
coluna de verdade é o `execucoes.py`, e as quebras reconhecidas estão em
`SQL_QUEBRA`, lá dentro.

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
  montar.py            monta o params.json a partir da planilha e do dossiê
  gerar.py             o gerador
  template.pptx        o modelo institucional (não editar)
  params.exemplo.json  exemplo fictício, copie para params.json
  execucoes.py         extrai as execuções do trimestre
  glpi_sla.py          extrai o SLA do GLPI
  probe.py             valores distintos de uma coluna, para a quebra
  checar_robos.py      confere as tabelas contra o banco
  fumaca.py            roda todos os robôs pela consulta e confere os totais
  PROMPT.md            prompt pronto para pedir um ATE novo

local, nunca versionado:
  .env                    credenciais do banco e do GLPI
  Tabelas Artemis.xlsx    cliente -> robô -> tabela(s) -> quebra
  params.json             o ATE que você está montando agora
```

## Detalhes de implementação

Os gráficos do template têm a planilha **embutida**, então o gerador usa
`chart.replace_data()`: cache e planilha mudam juntos, e "Editar Dados" no
PowerPoint abre os números do ATE. Cores e formato de cada série vêm do
template.

O gráfico de SLA é um combo: barras de chamados no eixo principal e a linha de
"Dentro do SLA" (uma fração, rótulo `0%`) num eixo secundário de 0 a 115%. Os
dois eixos de valor estão **escondidos, não apagados** — com o eixo apagado o
PowerPoint desenha a linha na escala dos chamados e ela cola no chão.

O gerador acha cada caixa pelo nome (`Capa`, `Agenda`, `Escopo`,
`Grafico Execucoes`, `Assertividade`, `Grafico SLA`, `Total`, `Dentro`, `Fora`,
`Esquerda`, `Direita`). Quem editar o `template.pptx` à mão precisa manter
esses nomes (Página Inicial → Organizar → Painel de Seleção).
