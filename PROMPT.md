# Como pedir um ATE

Este arquivo tem o texto pronto para pedir um ATE a uma IA com acesso à
máquina, e a explicação de onde sai cada pedaço do slide.

Copie o bloco abaixo e troque **só o cabeçalho e os slides 6 e 7**. Todo o
resto é fixo — é o que impede o assistente de reinventar o processo a cada mês.

O **objetivo e o escopo (slides 2 e 3) você não escreve**: eles saem do dossiê
do cliente no Obsidian.

**Nenhum dado de cliente entra neste arquivo.** Os exemplos são todos
genéricos de propósito — nome de cliente, código de robô, nome de tabela e
volume ficam na planilha e no dossiê, que são locais.

---

```
Oi! Preciso do ATE deste cliente:

════════════════════════════════════════════════════════════════════
CABEÇALHO — é só isto que muda de um mês para o outro
════════════════════════════════════════════════════════════════════

Cliente:      <nome como está na planilha>
Trimestre:    <AAAA-MM> a <AAAA-MM>
Competência:  <Mmm/AA>   (opcional — sem isto, o último mês do trimestre)
Robô:                    (opcional — só se o cliente tiver mais de um;
                          sem isto me mostra as opções e eu escolho)

TUDO daqui para baixo se ajusta ao CLIENTE e ao TRIMESTRE do cabeçalho.
Não vou repetir o nome nem as datas ao longo da mensagem: onde fizer
falta, pega de cima. Os três meses dos comandos são os do cabeçalho,
nunca os do exemplo.

Se algo no meu texto contradisser o cabeçalho, o CABEÇALHO VENCE —
aplica e me diz qual foi a divergência.


════════════════════════════════════════════════════════════════════
AMBIENTE — nada aqui é pergunta. Se não bater, você resolve sozinho.
════════════════════════════════════════════════════════════════════

PROJETO
  Já clonado, com o .env preenchido. NÃO te passo caminho: muda de
  máquina para máquina. Acha a pasta que tem gerar.py, template.pptx,
  glpi_sla.py, probe.py e sem-logo.png na raiz. Se achar mais de um
  clone, o certo é esse — os outros estão velhos.

  Usa a árvore de trabalho como ela está: não troca de branch, não faz
  git pull, não commita, não reverte alteração local.

CREDENCIAIS
  Tudo vem do .env local — banco e GLPI. Não precisa de query, de
  export, de token na mensagem nem de nada meu. Se faltar variável, o
  script diz qual é: me avisa qual, não tenta contornar.

PLANILHA
  "Tabelas Artemis.xlsx", na raiz do projeto. É a fonte da tabela do
  robô no banco e da quebra do gráfico. Não é anexo: não espera arquivo
  meu, não usa robos.csv, não descobre tabela pelo banco.

DOSSIÊS
  No vault do Obsidian (uma pasta "Obsidian Vault" em Documentos, ou
  equivalente). Um .md por cliente, com "cliente:" e a tag "dossie" no
  frontmatter. O nome da pasta de dentro já mudou antes — se não estiver
  onde você espera, acha pelo frontmatter, não pelo caminho.

CAPA
  SEM LOGO, sempre. Não pergunta por logo, não procura logo, não espera
  anexo de logo. O gerador já põe o placeholder transparente sozinho e a
  caixa da capa fica vazia. É assim mesmo, é o padrão do ATE.


════════════════════════════════════════════════════════════════════
DADOS — os dois gráficos saem de comando
════════════════════════════════════════════════════════════════════

Acha a linha do cliente na planilha e pega a tabela dele. Me diz qual
linha usou ANTES de rodar.

COMO LER A PLANILHA
────────────────────────────────────────────────────────────────────

Linha com a coluna Cliente em branco pertence ao cliente da última
linha preenchida acima.

"pode somar" na OBS vale também para essas linhas em branco logo
abaixo — essas tabelas somam e viram UM ROBÔ SÓ.

Sem "pode somar", linhas do mesmo cliente são robôs SEPARADOS: me
mostra as opções e espera eu escolher.

Não chuta e não soma robôs diferentes: um ATE é de UM ROBÔ SÓ.


OS DOIS COMANDOS
────────────────────────────────────────────────────────────────────

    python execucoes.py <tabela> <1º mês AAAA-MM> <3º mês AAAA-MM>

    python glpi_sla.py "<cliente>" <1º mês AAAA-MM> <3º mês AAAA-MM> --tudo

Passa a TABELA da planilha para o execucoes.py, não o nome do cliente:
com o nome ele cai no robos.csv, que está desatualizado. O glpi_sla.py
acha a entidade no GLPI pelo nome do cliente.

Cada um imprime uma tabela e devolve o bloco pronto do params.json:

    execucoes.py  ->  grafico_execucoes
    glpi_sla.py   ->  grafico_sla   (os três cartões saem daí,
                                     não me passa)


O SLA DO ATE NÃO É O SLA DO DASHBOARD
────────────────────────────────────────────────────────────────────

O glpi_sla.py vai SEMPRE com --tudo. Não é opcional.

Sem a flag ele reproduz o indicador canônico do Dashboard Sustain, que
descarta a árvore Monitoramento, os tickets "[Projeto] -" e a entidade
interna. Isso está certo para o indicador e errado para o ATE: o slide
5 diz "Total de Chamados", que é volume, e volume não se filtra. Já
saiu ATE com mês zerado no gráfico havendo chamado no GLPI no mês.

Se a tua cópia do script não aceitar --tudo, é a pasta errada — procura
o clone certo. Não roda sem a flag e não me pergunta se pode.

Nos dois modos ele imprime quantos chamados a regra canônica
descartaria. Me repassa essa linha: número alto ali significa que o ATE
e o dashboard vão contar histórias diferentes daquele cliente, e eu
quero saber disso antes da reunião, não durante.


QUEBRA DO GRÁFICO DE EXECUÇÕES
────────────────────────────────────────────────────────────────────

O gráfico sai num de dois formatos, e quem decide é a OBS da planilha:

    sem quebra  ->  uma barra por mês, com o total do mês

    com quebra  ->  uma série por mês e uma categoria por valor da
                    coluna (blocos "categorias" e "series" no lugar
                    de "meses" e "execucoes")

Passando a tabela direto, o execucoes.py não monta a quebra sozinho.
Confirma antes que a coluna existe mesmo naquela tabela, roda um mês
por vez e monta os blocos à mão:

    python probe.py <tabela> <COLUNA> <AAAA-MM-01> <mês seguinte AAAA-MM-01>

Me diz o nome da coluna e os valores distintos: já houve OBS pedindo
quebra por um conceito cujos valores estavam em outra coluna, com outro
nome. O total da quebra tem que bater com o total dos status.


O QUE ME MOSTRAR ANTES DE GERAR
────────────────────────────────────────────────────────────────────

  - qual linha da planilha e qual(is) tabela(s) você usou;
  - a quebra por status das execuções;
  - se houver quebra, a tabela dela também, com o total batendo;
  - os chamados do GLPI mês a mês e a linha de exclusões;
  - os dois textos do dossiê, com arquivo e seção de origem.

A assertividade do trimestre eu te confirmo depois de ver os status —
não preenche por conta própria e não reaproveita o valor que estiver no
params.json de outro ATE.


════════════════════════════════════════════════════════════════════
TEXTOS DOS SLIDES 2 E 3 — você busca no dossiê, eu não escrevo
════════════════════════════════════════════════════════════════════

O dossiê é a única fonte deles. Não inventa, não tira de nota técnica
de robô, de código nem do banco: o que não estiver no dossiê, você me
pergunta.

Casa o cliente pelo campo "cliente:" de DENTRO do arquivo, não pelo
nome dele — o arquivo costuma trazer a razão social inteira e o
cabeçalho vem com o nome curto, e ainda há diferença de acento e de "&"
vs "e". Na dúvida entre dois, PERGUNTA.


O DOSSIÊ VEM NUMA DE DUAS FORMAS — confere qual antes de ler
────────────────────────────────────────────────────────────────────

UM ROBÔ SÓ
    Tem a seção "### 2. Objetivo do projeto". É esse o texto.

VÁRIOS ROBÔS
    Não tem seção 1 nem seção 2. Tem blocos
    "## 🤖 Robô N — <código>: <nome>", cada um com uma linha
    "**Objetivo:**". Pega o bloco do robô do cabeçalho.

    É a forma dos clientes com mais de um robô, hoje 7 dos 18. Não
    decora quais: abre o arquivo e olha.

    Nesses casos o ROBÔ do cabeçalho decide o texto do slide 3. Se eu
    não tiver dito qual é, resolve junto com a escolha do robô na
    planilha — e me mostra o objetivo de cada opção, ajuda a escolher.

    Os códigos às vezes aparecem com as letras trocadas entre o dossiê
    e a planilha. Casa pelo número e pelo nome do robô também, não só
    pelas letras — e me diz quando tiver feito isso.


O QUE VIRA CADA SLIDE
────────────────────────────────────────────────────────────────────

Slide 3 — Escopo e objetivo, CURTO
    Sai da seção 2 (ou do "**Objetivo:**" do robô). No mínimo 4 e no
    máximo 5 linhas na caixa, régua de ~300 caracteres de texto
    visível: a caixa comporta ~76 por linha e os ** da marcação não
    contam. Confere no PNG do --conferir, não no olho.

    RESUMIR, não truncar. Pode condensar, desde que não entre nenhum
    fato que não esteja no dossiê. Nada de frase cortada no meio:
    cortar no primeiro ponto final resolve uns dossiês e quebra
    outros, que são uma frase só cheia de ponto-e-vírgula.

      fica: a ação principal + o que ela processa + o sistema onde
            acontece
      sai:  a enumeração de etapas (tudo depois de "Contempla:", as
            listas separadas por ponto-e-vírgula), volumetria,
            horário de execução, parâmetros técnicos

    Me mostra o original e o resumido lado a lado — eu aprovo ou
    corrijo. É isso que impede o resumo de virar invenção.

Slide 2 — Resumo do robô para a agenda
    Uma linha só, juntando a seção 1 ("Nome do projeto") com a 4
    ("Segmentação do projeto"). Nos dossiês com blocos de robô não
    existe seção 1: nesses, o título do bloco faz o papel dela. A
    seção 4 existe em todos.

Do dossiê sai SÓ isso. Valor de contrato, mensalidade, ROI, contato e
e-mail não entram no slide nem no params.json.

Se não achar o dossiê, ou achar e ele não tiver o objetivo do robô que
eu pedi, ME AVISA e me pede o texto. Não preenche com texto de outro
cliente e não escreve de cabeça.


════════════════════════════════════════════════════════════════════
TEXTOS DO TRIMESTRE — estes eu escrevo, é o que muda todo mês
════════════════════════════════════════════════════════════════════

DIFICULDADES / LIÇÕES APRENDIDAS  ->  slide 6
────────────────────────────────────────────────────────────────────

<tópico>
  - <o que aconteceu no trimestre e o que se aprendeu>

Maiores causas de abertura de chamado
  - <causa>
  - <causa>


PONTOS DE ATENÇÃO / MELHORIAS  ->  slide 7
────────────────────────────────────────────────────────────────────

<tópico>
  - <o que vem pela frente>


REGRAS DOS TEXTOS
────────────────────────────────────────────────────────────────────

Os números dos tópicos saem automáticos — não escreve 1., 2., 3.

Use **assim** para destacar: amarelo no slide 3, negrito nos
slides 6 e 7.


════════════════════════════════════════════════════════════════════
GERAR E CONFERIR
════════════════════════════════════════════════════════════════════

    python gerar.py params.json ATE-<cliente>-<competência>.pptx --conferir

  - Os meses dos dois gráficos são os três do cabeçalho?
  - Quais números saíram nos cartões do slide 5?
  - Algum texto estourou a caixa no PNG do --conferir?

Mês zerado em qualquer um dos dois gráficos é ALERTA, não resultado:
confere na fonte se aquele mês teve mesmo zero antes de me entregar.

Me devolve o .pptx.
```

---

## De onde sai cada coisa

| Slide | Conteúdo | Origem |
|---|---|---|
| 1 | competência | cabeçalho do pedido |
| 1 | logo | nenhum — placeholder transparente, sempre |
| 2 | resumo do robô | dossiê, seções 1 + 4 |
| 3 | escopo e objetivo | dossiê, seção 2 (ou o `**Objetivo:**` do robô) |
| 4 | execuções do trimestre | banco, via `execucoes.py` |
| 5 | chamados e SLA | GLPI, via `glpi_sla.py --tudo` |
| 6 | dificuldades / lições | você, na mensagem |
| 7 | pontos de atenção | você, na mensagem |

Os slides 6 e 7 continuam na mensagem porque são **do trimestre**, não do
contrato: o que quebrou, o que melhorou, o que abriu chamado. O dossiê é o que
foi vendido, e isso não muda de um ATE para o outro.

## As quatro fontes locais

Nenhuma delas está no repositório, e é de propósito.

| Fonte | Onde | Para quê |
|---|---|---|
| `.env` | raiz do projeto | credenciais do banco e do GLPI |
| `Tabelas Artemis.xlsx` | raiz do projeto | tabela do robô no banco e a quebra do gráfico |
| dossiês | vault do Obsidian | textos dos slides 2 e 3 |
| GLPI | rede | chamados e SLA do trimestre |

O `.env` é por máquina — copie o `.env.exemplo` e preencha. Os acessos são
**somente leitura**: nenhum script escreve no banco nem no GLPI.

A planilha fica na raiz e está no `.gitignore`. Ela substituiu o `robos.csv`,
que continua no código por compatibilidade mas já diverge dela — por isso o
pedido manda passar a tabela direto para o `execucoes.py`.

## A capa vai sem logo

Não é opção nem configuração: o `gerar.py` sempre cobre a área do logo com o
`sem-logo.png`, um PNG transparente de 342×101 versionado na raiz. A caixa da
capa fica vazia em todos os ATEs.

Isso existe porque o `template.pptx` traz o logo de um cliente antigo embutido.
Sem o placeholder, qualquer ATE sairia com o logo de outra empresa na capa. O
gerador não lê logo de lugar nenhum e o `params.json` não tem campo de logo —
não há o que perguntar, procurar ou anexar.

## Sobre o `--conferir`

Não exige nada especial: usa PowerPoint se houver (Windows) ou LibreOffice se
houver (qualquer sistema). Se não houver nenhum dos dois, o gerador avisa e
segue — o `.pptx` sai igual, só sem a conferência visual automática.
