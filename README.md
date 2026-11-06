# Gerador de ATE em .pptx

Gera a apresentação de Acompanhamento Tático/Estratégico a partir do template
institucional da Yank, montado sobre o **modelo oficial de apresentação** (fundo
escuro, fonte Urbane). O template antigo, de fundo claro, está guardado na
branch `template-antigo`. A saída é um `.pptx` **nativo**: texto selecionável,
gráficos de verdade, tudo editável no PowerPoint.

O layout, as fontes, as cores e a decoração vêm intactos do `template.pptx` —
o gerador só troca conteúdo.

O ATE mostra **valor de negócio**, não só operação. São até nove slides — o
modelo oficial tem onze tipos, e os opcionais (*) só entram com dado:

| # | Slide | O que mostra |
|---|---|---|
| 1 | Capa | competência |
| 2 | Resumo Executivo — Valor Gerado | escopo, quatro cartões (itens processados, horas poupadas, economia, disponibilidade) e o que foi entregue |
| 3* | Horas e Valor Financeiro | a conta aberta: itens × tempo manual, dias úteis, horas × custo/hora, disponibilidade mês a mês |
| 4 | Indicadores de Operação | execuções e SLA lado a lado; cartões de assertividade, SLA e disponibilidade |
| 5* | Volume Processado | tabela mês a mês: entregas, casos fora da regra, falhas detectadas, total |
| 6* | O que fizemos para evitar falhas | três números (falhas de API detectadas, casos barrados, chamados no SLA) e uma faixa de contexto |
| 7 | Melhorias Entregues no Período | o que foi entregue no robô e o que se fez para evitar falhas |
| 8 | Próximas Evoluções e Oportunidades | o que vem para o robô e automações do mesmo segmento em outros clientes |
| 9 | Encerramento | fixo |

**Agente**: o [CLAUDE.md](CLAUDE.md) transforma o Claude Code no gerador de ATE
deste repositório, e a pasta [conhecimento/](conhecimento/README.md) é a base
que ele consulta — um .md por fonte (slides, valor, banco, GLPI, vault,
planilha, status, textos, limites, integração com o portal).

Os slides opcionais vêm do MODELO OFICIAL pelo `construir_template.py`
(roda uma vez, quando o modelo mudar).

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

O `--conferir` exporta os 6 slides em imagem. Ele se vira com o que existir no
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

Ele resolve sozinho a tabela do robô (na planilha), o escopo (no dossiê do
Obsidian ou, sem dossiê, na nota do robô), as execuções, a assertividade e as
entregas (no banco), os chamados e a disponibilidade (no GLPI, sempre com
`--tudo`) e as automações do mesmo segmento (nas notas de robô do vault), e
escreve o `params.json`. O que depende de julgamento fica marcado com
`REVISAR:` dentro do arquivo — condensar o escopo, dar frase de negócio às
entregas e escrever os slides 4 e 5.

Cliente com mais de um robô faz o script listar as opções e parar: um ATE é de
um robô só. Use `--robo <código>` ou, quando o mesmo código aparecer em mais de
uma linha, `--robo <número da linha>`. Dois fluxos do mesmo robô em linhas
separadas entram juntos com `--robo <linha>,<linha>`. `--sem-banco` monta só a parte de
planilha e dossiê, para conferir os textos antes de gastar consulta.

**Nada de caminho fixo.** O projeto é onde o `montar.py` está; a planilha é a
`.xlsx` que estiver junto dele; o vault sai do registro do próprio Obsidian, ou
da pasta que tiver um `.obsidian` dentro. As colunas da planilha são achadas
pelo cabeçalho, não pela posição, e a carteira pode ter qualquer tamanho — cada
gerente tem a sua.

Para montar à mão, copie o `params.exemplo.json` para `params.json` e ajuste os
valores. O [PROMPT.md](PROMPT.md) tem o texto pronto para pedir um ATE a uma IA.

## Nada de dado de cliente no repositório

`Tabelas Artemis.xlsx`, `params.json`, `status-local.json` e
`valor-local.json` são **locais** e estão no `.gitignore`, junto com o `.env`.
Eles carregam nome de cliente, código de robô, tabela do banco, volume de
execução, tempo manual e custo/hora — nada disso entra em commit. O Obsidian,
de onde saem o escopo e o segmento, também não é copiado para cá.

O que fica versionado é só o mecanismo: os scripts, o template e a
documentação. O `params.exemplo.json` é fictício de
propósito, e os exemplos do [PROMPT.md](PROMPT.md) são genéricos — nenhum nome
de cliente, código de robô ou nome de tabela real aparece em arquivo
versionado.

## O que cada campo preenche

| Campo | Slide | O que muda |
|---|---|---|
| `competencia` | 1 | data em azul, abaixo do título da capa |
| `escopo` | 2 | faixa do escopo; `**termo**` sai em azul e negrito |
| `valor_gerado.itens_entregues` | 2 | base das horas poupadas (status de sucesso) |
| `valor_gerado.minutos_por_item` | 2 | tempo manual médio por item, do cliente; `null` = "a confirmar" |
| `valor_gerado.custo_hora` | 2 | R$ por hora da equipe, do cliente; `null` = "a confirmar" |
| `valor_gerado.entregas` | 2 | lista "O que foi entregue no trimestre" |
| `disponibilidade.percentual` | 2 e 3 | cartão de disponibilidade; `null` = "a confirmar" |
| `disponibilidade.horas_indisponivel` | 3 | detalhe do cartão ("0,2 h de parada no trimestre") |
| `disponibilidade.fonte` | 2 e 4 | opcional: quando o número vem de outra fonte, ela vai escrita no cartão |
| `valor_gerado.origem` | 2 | opcional: de onde vieram tempo e custo (padrão "informados pelo cliente") |
| `volume_processado` | 5 | `colunas` (meses + Trimestre) e `linhas` (`rotulo`, `valores`, `destaque`) |
| `prevencao` | 6 | `destaques` (`numero`, `titulo`, `texto`) e `faixa` (`titulo`, `texto`) |
| `ocultar` | 3, 5, 6 | lista de slides opcionais a tirar mesmo com dado: `valor`, `volume`, `prevencao` |
| `grafico_execucoes.titulo` | 3 | título acima do gráfico |
| `grafico_execucoes.assertividade` | 3 | número (99.35) ou texto pronto; vira o cartão de assertividade |
| `grafico_execucoes.meses` / `execucoes` | 2 e 3 | uma barra por mês; a soma é o cartão de itens processados |
| `grafico_execucoes.categorias` / `series` | 2 e 3 | alternativa: gráfico quebrado, uma série por mês |
| `grafico_sla.meses` / `chamados` / `dentro_do_sla` | 3 | dados do gráfico e do cartão de SLA |
| `melhorias` | 4 | tópicos das duas colunas |
| `proximas_evolucoes` | 5 | tópicos das duas colunas (direita: oportunidades no segmento) |

Os textos aceitam `**assim**` para destacar: azul no escopo, negrito nas
entregas e nos slides 4 e 5.

## Valor gerado

As horas e a economia são **estimativa**, e o slide diz isso na nota de rodapé:

```
horas poupadas = itens entregues × minutos por item ÷ 60
dias úteis     = horas ÷ 8
economia       = horas × custo/hora
```

"Itens entregues" são os status classificados como **sucesso** pelo
`status.py` — exceção de negócio não entra, porque não foi trabalho poupado.
O tempo manual e o custo/hora são **do cliente** e ficam no
`valor-local.json`, por robô. Sem eles os cartões saem "a confirmar": o
gerador não tem tempo padrão e não deve ter.

```json
{
  "<código do robô>": {
    "minutos_por_item": 4,
    "custo_hora": 55,
    "entregas": {
      "<STATUS DE SUCESSO>": "<frase de negócio que vai no slide>"
    }
  }
}
```

Com `entregas` preenchido, contam como itens só os status listados, cada um
com a sua frase. Sem isso, entra todo status de sucesso com o texto cru e
`REVISAR:` — status de sistema não é frase de diretoria.

## Disponibilidade

Não existe registro de "robô fora do ar" que dê para usar: as tabelas de
monitoramento do banco pararam em 2022, e o intervalo entre execuções não
serve, porque os robôs rodam por demanda — dia sem execução é dia sem demanda.

A estimativa sai do GLPI (`glpi_sla.py --robo <código>`):

- contam os chamados de **Sustentação** (Correção, Análise), da abertura à
  solução, abertos no nó do robô ou no ambiente compartilhado do cliente;
- **Monitoramento não conta**: é checagem de rotina, e quase todos fecham em
  minutos;
- chamados de outros robôs do mesmo cliente ficam de fora;
- faixas sobrepostas se juntam, e a base são as horas corridas do trimestre
  (24x7).

O percentual sai **arredondado para baixo** (99,99 vira 99,9%): só aparece
100% quando não houve nenhuma parada. É uma estimativa conservadora — o
chamado conta inteiro, mesmo que o robô tenha voltado antes do registro da
solução. Quem tiver número melhor (healthcheck) põe em
`disponibilidade.percentual` com `disponibilidade.fonte`.

## Oportunidades no segmento

O `montar.py` lê as notas de robô do vault (`tipo: robo`), pega as da mesma
área — o que vem antes do ` - ` no `segmento_projeto` — em **outros**
clientes, tira os assuntos que este cliente já tem e conta em quantos clientes
cada um roda. Sai só o assunto e a contagem: **nome de outro cliente nunca vai
para o slide**.

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
slide 2 descreve um robô específico, e somar dois daria um gráfico que não
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

## O cartão de SLA é calculado

Você **não** informa o número do cartão de SLA do slide 3. Ele sai dos dados
do gráfico:

```
total   = soma de chamados
dentro  = soma de dentro_do_sla
%dentro = dentro / total
```

Assim o cartão nunca discorda do gráfico. O gerador imprime os valores no
terminal para conferência.

## Numeração dos tópicos

Os tópicos dos slides 4 e 5 são numerados automaticamente e **a numeração
continua da coluna da esquerda para a da direita** — dois tópicos à esquerda
fazem a direita começar em 3. Não escreva o número no texto.

## Estrutura

```
versionado:
  CLAUDE.md            instruções do agente gerador de ATE
  conhecimento/        base de conhecimento do agente, um .md por fonte
  montar.py            monta o params.json (planilha, Obsidian, banco, GLPI)
  gerar.py             o gerador
  construir_template.py copia os slides opcionais do MODELO OFICIAL
  template.pptx        o modelo institucional (não editar)
  params.exemplo.json  exemplo fictício, copie para params.json
  execucoes.py         extrai as execuções do trimestre
  glpi_sla.py          extrai o SLA e a disponibilidade do GLPI
  probe.py             valores distintos de uma coluna, para a quebra
  checar_robos.py      confere as tabelas contra o banco
  fumaca.py            roda todos os robôs pela consulta e confere os totais
  PROMPT.md            prompt pronto para pedir um ATE novo

local, nunca versionado:
  .env                    credenciais do banco e do GLPI
  Tabelas Artemis.xlsx    cliente -> robô -> tabela(s) -> quebra
  status-local.json       classificação dos status, por robô
  valor-local.json        tempo manual, custo/hora e frases de entrega, por robô
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

O gerador acha cada caixa pelo nome (`Capa`; no slide 2 `Escopo`, `Volume`,
`Horas`, `Economia`, `Disponibilidade`, `Entregas`, `Nota`; no slide 3
`Grafico Execucoes`, `Grafico SLA`, `Assertividade`, `SLA`, `Disponibilidade`;
nos slides 4 e 5 `Esquerda` e `Direita`). Cada cartão tem três parágrafos:
número, legenda e detalhe. Quem editar o `template.pptx` à mão precisa manter
esses nomes (Página Inicial → Organizar → Painel de Seleção).
