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
python gerar.py params.json ATE-Cliente Exemplo-Set26.pptx
```

Para conferir visualmente antes de entregar:

```bash
python gerar.py params.json ATE-Cliente Exemplo-Set26.pptx --conferir
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

Para um ATE novo, copie o `params.json`, ajuste os valores e rode. O
[PROMPT.md](PROMPT.md) tem o texto pronto para pedir isso a uma IA.

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
| `grafico_sla.meses` / `chamados` / `dentro_do_sla` | 5 | dados do gráfico |
| `dificuldades` | 6 | tópicos das duas colunas |
| `pontos_de_atencao` | 7 | tópicos das duas colunas |

Os textos aceitam `**assim**` para destacar: amarelo no slide 3, negrito nos
slides 6 e 7.

## SLA direto do GLPI

O `glpi_sla.py` puxa os chamados pela API REST e devolve o bloco `grafico_sla`
pronto, dispensando o export manual:

```bash
set GLPI_APP=<app_token>
set GLPI_USER=<user_token>
python glpi_sla.py "Cliente Exemplo" 2026-04 2026-06
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
gerar.py        o gerador
template.pptx   o modelo institucional (não editar)
params.json     exemplo preenchido com o ATE de Jun/26
PROMPT.md       prompt pronto para pedir um ATE novo
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
