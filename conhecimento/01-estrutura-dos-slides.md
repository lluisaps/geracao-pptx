# Estrutura dos slides

O ATE nasce do **MODELO OFICIAL de apresentação** da Yank (fundo escuro,
fonte Urbane), que traz 11 tipos de slide. O `template.pptx` usa parte deles;
o `construir_template.py` copia os tipos novos do modelo quando preciso.

## Os 11 tipos do modelo oficial

| # | Tipo | Usado no ATE como |
|---|---|---|
| 1 | Capa | Capa |
| 2 | Textos em colunas | — (livre) |
| 3 | Textos | — (livre) |
| 4 | Tópicos | — (livre) |
| 5 | Tópicos em colunas | Melhorias · Próximas evoluções |
| 6 | Destaques (3 cartões + faixa) | O que fizemos para evitar falhas |
| 7 | Imagens | — (livre: print de dashboard, fluxo do robô) |
| 8 | Números (3 colunas com pílula) | Horas e Valor Financeiro |
| 9 | Tabelas | Volume Processado |
| 10 | Frase / citação | — (livre) |
| 11 | Encerramento | Encerramento |

O ATE tem **no máximo 11 slides**. Hoje são até 9; sobram dois espaços para
um slide de imagem ou de frase, se a gestora pedir.

## A sequência do ATE

| # | Slide | Entra quando | Campo do params.json |
|---|---|---|---|
| 1 | Capa | sempre | `competencia` |
| 2 | Resumo Executivo — Valor Gerado | sempre | `escopo`, `valor_gerado`, `disponibilidade` |
| 3 | Horas e Valor Financeiro | `valor_gerado.minutos_por_item` preenchido | (derivado) |
| 4 | Indicadores de Operação | sempre | `grafico_execucoes`, `grafico_sla`, `disponibilidade` |
| 5 | Volume Processado | `volume_processado.linhas` existe | `volume_processado` |
| 6 | O que fizemos para evitar falhas | `prevencao.destaques` existe | `prevencao` |
| 7 | Melhorias Entregues no Período | sempre | `melhorias` |
| 8 | Próximas Evoluções e Oportunidades | sempre | `proximas_evolucoes` |
| 9 | Encerramento | sempre | (fixo) |

Slide opcional sem dado **sai do .pptx** — não fica slide vazio. Para tirar um
slide que tem dado, use `"ocultar": ["valor" | "volume" | "prevencao"]`.

O `gerar.py` acha cada slide por uma forma que só ele tem, não pela posição.
Quem editar o `template.pptx` à mão mantém os nomes das formas (Painel de
Seleção do PowerPoint).

## Slide a slide

### 1 · Capa
Só a competência (`Jun/26`). **Sem logo de cliente** — não pergunte, não
procure.

### 2 · Resumo Executivo — Valor Gerado
- **Escopo**: até ~200 caracteres, no máximo 2 linhas. Ação + o que processa +
  sistema. `**termo**` sai em azul. Fonte: Obsidian (ver 05).
- **Quatro cartões**: itens processados · horas poupadas (com ≈ dias úteis) ·
  economia estimada (horas × R$/h) · disponibilidade estimada.
- **O que foi entregue no trimestre**: um item por status de sucesso, com a
  quantidade em negrito. Frase de negócio, não texto de sistema.
- **Nota de rodapé**: diz de onde vieram tempo e custo (`valor_gerado.origem`,
  padrão "informados pelo cliente") e como a disponibilidade foi estimada.

### 3 · Horas e Valor Financeiro (opcional)
Abre os números do slide 2 para quem quer ver a conta:

| Coluna | Número | Legenda | Pílula |
|---|---|---|---|
| Horas economizadas | `1.764 h` | `35.276 itens × 3 min manuais` | `≈ 220 dias úteis` |
| Valor financeiro | `R$ 79,4 mil` | `1.764 h × custo médio da equipe` | `R$ 45/h` |
| Disponibilidade | `99,9%` | `Abr 100% · Mai 99,9% · Jun 100%` | `1 chamado` |

Legenda e pílula cabem em **uma linha** cada. Sem tempo manual, o slide sai
do deck (o slide 2 já mostra "a confirmar").

### 4 · Indicadores de Operação
- Gráfico de execuções: uma barra por mês (ou quebrado por portal/etapa
  quando a planilha manda).
- Gráfico de chamados × % dentro do SLA.
- Cartões: assertividade · % no SLA (calculado do gráfico, nunca digitado) ·
  disponibilidade com o mês a mês na linha de baixo.

### 5 · Volume Processado (opcional)
Tabela: uma linha por entrega + casos fora da regra + falhas de API
detectadas + falhas do robô + **Total processado**. Colunas: os três meses e
o trimestre. É aqui que entra volumetria que não é status do banco
("350 GB de áudio tratados", "120 cidades processadas") — **só se o pedido
trouxer o número**; acrescente uma linha com `valores` em texto.

### 6 · O que fizemos para evitar falhas (opcional)
Três destaques com número e uma faixa de contexto. O `montar.py` propõe, na
ordem, e usa os três primeiros que existirem:

1. falhas de API/sistema externo detectadas (status que casam com `EXTERNO`
   no `montar.py`: HTTP 5xx, socket hang up, timeout, portal fora do ar);
2. casos fora da regra separados automaticamente (exceção de negócio);
3. chamados resolvidos dentro do SLA (`N de M`);
4. assertividade.

A faixa de baixo é texto do trimestre — o que a equipe fez (vem do pedido).
**Nunca** escreva "reprocessamentos automáticos" com número: o banco não
guarda retentativa, só o status final.

### 7 · Melhorias Entregues no Período
Duas colunas, tópicos numerados automaticamente (a numeração continua da
esquerda para a direita — não escreva 1., 2.):
- esquerda: **O que foi entregue no robô**;
- direita: **O que fizemos para evitar falhas** (qualitativo).
Fonte: o pedido. O GLPI dá só a pista de quantos chamados de Melhoria houve.

### 8 · Próximas Evoluções e Oportunidades
- esquerda: **Próximas evoluções** — do pedido;
- direita: **Oportunidades no segmento** — do vault (ver 05), reescritas como
  oportunidade, sem nome de cliente. Tire o que não fizer sentido e diga o quê.

### 9 · Encerramento
Fixo.

## Conferência antes de entregar

`python gerar.py params.json ATE-<cliente>-<competência>.pptx --conferir`
exporta PNGs em `conferencia/`. Olhe: meses dos gráficos = cabeçalho; números
dos cartões; nenhum `REVISAR` no params.json; nenhum texto estourando caixa;
quantos slides saíram e quais ficaram de fora (o gerador imprime).
