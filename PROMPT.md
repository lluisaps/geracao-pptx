# Como pedir um ATE

Este arquivo tem o texto pronto para pedir um ATE a uma IA com acesso à
máquina, e a explicação de onde sai cada pedaço do slide.

O ATE mostra **valor de negócio**, não só operação. São até nove slides
(o modelo oficial comporta onze); os marcados com * só entram quando há dado:

1. Capa
2. **Resumo Executivo — Valor Gerado**: escopo em uma faixa, quatro cartões
   (itens processados, horas poupadas, economia estimada, disponibilidade) e
   a lista do que foi entregue no trimestre
3. \* **Horas e Valor Financeiro**: a conta aberta — itens × tempo manual,
   dias úteis, horas × custo/hora, disponibilidade mês a mês. Só com tempo
   manual informado
4. **Indicadores de Operação**: execuções e SLA lado a lado, mais os cartões
   de assertividade, SLA e disponibilidade
5. \* **Volume Processado**: tabela mês a mês do que o robô entregou
6. \* **O que fizemos para evitar falhas**: três números (falhas de API
   detectadas, casos fora da regra, chamados no SLA) e uma faixa de contexto
7. **Melhorias Entregues no Período**: o que foi entregue no robô e o que se
   fez para evitar falhas
8. **Próximas Evoluções e Oportunidades**: o que vem para o robô e automações
   que outros clientes do mesmo segmento já usam
9. Encerramento

O agente que roda isto lê o [CLAUDE.md](CLAUDE.md) e a base em
[conhecimento/](conhecimento/README.md) — as regras abaixo estão lá também,
com o porquê.

Copie o bloco abaixo e troque **só o cabeçalho e os slides 6, 7 e 8**. Todo o
resto é fixo — é o que impede o assistente de reinventar o processo a cada mês.

O **escopo você não escreve**: ele sai do Obsidian, e quem vai buscar é o
`montar.py`.

**Nenhum dado de cliente entra neste arquivo.** Os exemplos são todos
genéricos de propósito — nome de cliente, código de robô, nome de tabela,
volume, tempo manual e custo/hora ficam na planilha, no Obsidian e nos
arquivos `-local.json`, que são locais.

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
Tempo manual: <minutos por item>   (opcional — informado pelo cliente)
Custo/hora:   <R$ por hora>        (opcional — informado pelo cliente)

Os três meses dos comandos são os do cabeçalho, nunca os do exemplo. Se
algo no meu texto contradisser o cabeçalho, o CABEÇALHO VENCE — aplica e
me diz qual foi a divergência.


════════════════════════════════════════════════════════════════════
AMBIENTE — nada aqui é pergunta
════════════════════════════════════════════════════════════════════

NÃO te passo caminho de nada: nem do projeto, nem da planilha, nem do
Obsidian. Mudam de máquina para máquina e os scripts acham sozinhos.

O vault do Obsidian é fonte OBRIGATÓRIA deste ATE, não é atalho nem
conveniência: o escopo e as automações do segmento só existem lá. Abrir
o vault é passo do processo — se esse passo não aconteceu, o ATE não está
pronto, por mais completo que ele pareça.

Acha a pasta que tem montar.py e gerar.py e trabalha nela. Antes de rodar
qualquer coisa, ATUALIZA o repositório — máquina com código velho quebra na
execução:

    git fetch
    git status -sb

Se o `status -sb` disser que o branch está atrás do remoto (`behind`), roda:

    git pull --ff-only

Não troca de branch e não commita nada. Se o pull não for fast-forward, ou se
algum arquivo modificado atrapalhar, PARA e me mostra o `git status` — não faz
merge, não faz rebase, não descarta alteração minha. Me diz em uma linha se
atualizou (e o que mudou) ou se já estava em dia.

Não achou a pasta em lugar nenhum? Clona:

    git clone https://github.com/lluisaps/geracao-pptx.git

Clone novo NÃO traz o .env, a planilha, o status-local.json nem o
valor-local.json — são locais e ficam fora do repositório de propósito.
Nesse caso: copia o .env.exemplo para .env e me pede as credenciais, e me
pede a planilha para pôr na raiz. Para e avisa; não inventa dado nem tenta
descobrir tabela pelo banco.

A capa não tem logo de cliente. Não pergunta por logo, não procura, não
espera anexo — o template já traz só o logo da Yank.


════════════════════════════════════════════════════════════════════
O COMANDO
════════════════════════════════════════════════════════════════════

    python montar.py "<cliente>" <1º mês AAAA-MM> <3º mês AAAA-MM>

Isso sozinho acha a planilha, resolve a tabela do robô, acha o escopo no
Obsidian, consulta o banco e o GLPI, procura as automações do segmento no
vault e escreve o params.json.

Se o cliente tiver mais de um robô, ele lista e para. Me mostra a lista e
espera eu escolher — um ATE é de UM ROBÔ SÓ, não chuta e não soma robôs
diferentes. Depois roda de novo com --robo <código>, ou --robo <número da
linha> quando o mesmo código aparecer em mais de uma linha. Se eu disser
que são os fluxos do mesmo robô, junta as linhas com --robo <linha>,<linha>.

Se ele falhar em algum ponto, me diz onde falhou antes de contornar. O
contorno é rodar na mão e montar o params.json você:

    python execucoes.py <tabela> <1º mês> <3º mês>
    python glpi_sla.py "<cliente>" <1º mês> <3º mês> --tudo --robo <código>

O --tudo não é opcional. Sem ele o glpi_sla.py devolve o indicador
canônico do Dashboard Sustain, que descarta a árvore Monitoramento, os
tickets "[Projeto] -" e a entidade interna. Está certo para o indicador e
errado para o ATE: o gráfico mostra o total de chamados, que é volume, e
volume não se filtra. Já saiu ATE com mês zerado havendo chamado no GLPI.


════════════════════════════════════════════════════════════════════
VALOR GERADO — de onde sai cada cartão do slide 2
════════════════════════════════════════════════════════════════════

ITENS PROCESSADOS
    Total de execuções do trimestre, do banco. Automático.

HORAS POUPADAS = itens entregues × tempo manual por item
ECONOMIA       = horas poupadas × custo/hora
    "Itens entregues" são os status de SUCESSO (não as exceções de
    negócio). O tempo manual e o custo/hora são do CLIENTE: vêm do
    cabeçalho acima e moram no valor-local.json, por robô. Sem eles o
    cartão sai "a confirmar" — NUNCA inventa um tempo padrão nem copia o
    de outro robô. Número de valor inventado é pior que cartão vazio.

DISPONIBILIDADE
    Estimada pelo GLPI: tempo dos chamados de SUSTENTAÇÃO (Correção,
    Análise) do robô e do ambiente do cliente, sobre as horas corridas do
    trimestre. Os chamados de Monitoramento NÃO contam — são checagem de
    rotina e quase todos fecham em minutos. O percentual é arredondado
    para baixo (99,99 sai 99,9%). Se houver número melhor (healthcheck),
    eu passo e ele entra no lugar, com a fonte escrita no cartão.

O QUE FOI ENTREGUE
    Um item por status de sucesso, com a quantidade. A frase de negócio de
    cada status mora no valor-local.json ("DOCUMENTO INSERIDO COM SUCESSO"
    vira "documentos inseridos no <sistema>"). Robô sem frases no arquivo
    sai com o texto cru do status e REVISAR: me propõe as frases, a partir
    do status e da nota do robô no Obsidian, e grava no valor-local.json
    depois que eu aprovar. Não pode entrar na frase o que o status não diz.


════════════════════════════════════════════════════════════════════
O QUE ME MOSTRAR ANTES DE GERAR
════════════════════════════════════════════════════════════════════

Tudo isto de uma vez, que é o que eu confiro:

  - qual linha da planilha e qual(is) tabela(s) o script usou;
  - a quebra por status das execuções, e a tabela da quebra se houver
    (o total da quebra tem que bater com o total dos status);
  - os chamados do GLPI mês a mês e a linha de exclusões — número alto
    ali significa que o ATE e o dashboard vão contar histórias
    diferentes desse cliente, e eu quero saber antes da reunião;
  - a entidade do GLPI que o script usou (o nome da planilha não é o
    nome do GLPI) e os chamados que entraram na disponibilidade;
  - os quatro cartões do slide 2 e a lista de entregas;
  - o escopo, com o arquivo .md e a seção de onde saiu — se não vier a
    origem, eu assumo que o texto foi escrito de cabeça e devolvo o ATE;
  - as automações do segmento que o script achou no vault.

Mês zerado em qualquer um dos dois gráficos é ALERTA, não resultado:
confere na fonte antes de me entregar.


════════════════════════════════════════════════════════════════════
O ESCOPO SAI DO OBSIDIAN — SEMPRE
════════════════════════════════════════════════════════════════════

O `escopo` do params.json vem do DOSSIÊ DO CLIENTE no meu vault do
Obsidian ou, quando o cliente não tem dossiê, da NOTA DO ROBÔ (seção
"Objetivo"). De lugar nenhum além disso. Quem acha é o montar.py.

Não vale:

  - escrever de cabeça a partir do nome do cliente ou do código do robô;
  - deduzir o objetivo pelo que a tabela do banco parece fazer;
  - copiar de um params.json ou de um .pptx de outro ATE;
  - aproveitar o texto do ATE do trimestre passado sem abrir a nota.

Condensar PODE — a faixa do slide 2 pede: régua de ~200 caracteres, no
máximo duas linhas no PNG do --conferir. Fica a ação principal + o que ela
processa + o sistema onde acontece; sai enumeração de etapas, volumetria,
horário e parâmetro técnico. RESUMIR, não truncar. Entrar fato que não
está na nota, NÃO. Me mostra o original e o resumido lado a lado.

Não achou o vault ou a nota? PARA e me pede o texto.

Do Obsidian sai só isso e o segmento — nada de valor de contrato,
mensalidade, ROI ou contato.


════════════════════════════════════════════════════════════════════
AUTOMAÇÕES DO SEGMENTO (slide 8, coluna da direita)
════════════════════════════════════════════════════════════════════

O script lê as notas de robô do vault, pega as da mesma área (o que vem
antes do " - " no segmento_projeto) em OUTROS clientes, tira o que este
cliente já tem e conta em quantos clientes cada assunto roda.

NUNCA entra nome de outro cliente no slide — nem no texto, nem como
exemplo. O ATE vai para fora. Pode reescrever cada item como oportunidade
("Cadastro de processos: hoje roda em 3 clientes do segmento"), desde que
o assunto e a contagem sejam os do script. Tira o que não fizer sentido
para este cliente e me diz o que tirou.


════════════════════════════════════════════════════════════════════
SLIDE 5 — volume processado (opcional)
════════════════════════════════════════════════════════════════════

A tabela sai do banco sozinha. Volumetria que não é status do banco
entra só se eu escrever aqui, com o número:
  - <ex.: 350 GB de áudios tratados no trimestre>


════════════════════════════════════════════════════════════════════
SLIDE 6 — o que fizemos para evitar falhas
════════════════════════════════════════════════════════════════════

Os três números saem do banco e do GLPI. A faixa de baixo é minha:
  <o que a equipe fez no trimestre para evitar falhas>

Não escreve "reprocessamentos automáticos" com número — o banco não
guarda retentativa.


════════════════════════════════════════════════════════════════════
SLIDE 7 — melhorias entregues no período
════════════════════════════════════════════════════════════════════

O que foi entregue no robô
  - <ajuste, evolução, nova regra no trimestre>

O que fizemos para evitar falhas
  - <prevenção, monitoramento, reprocessamento, correção de causa>

(O script conta os chamados de Melhoria e de Sustentação do robô no
trimestre, como pista — os títulos do GLPI não dizem o que foi feito.)


════════════════════════════════════════════════════════════════════
SLIDE 8 — próximas evoluções (coluna da esquerda)
════════════════════════════════════════════════════════════════════

<tópico>
  - <o que vem pela frente neste robô>


Os números dos tópicos saem automáticos — não escreve 1., 2., 3.
Use **assim** para destacar: azul no escopo, negrito nas entregas e nos
slides 7 e 8.


════════════════════════════════════════════════════════════════════
GERAR E CONFERIR
════════════════════════════════════════════════════════════════════

    python gerar.py params.json ATE-<cliente>-<competência>.pptx --conferir

  - Os meses dos dois gráficos são os três do cabeçalho?
  - Quais números saíram nos cartões dos slides 2, 3 e 4?
  - Quantos slides saíram e quais opcionais ficaram de fora?
  - Sobrou algum REVISAR no params.json?
  - Algum texto estourou a caixa no PNG do --conferir?

Me devolve o .pptx.
```

---

## De onde sai cada coisa

| Slide | Conteúdo | Origem |
|---|---|---|
| 1 | competência | cabeçalho do pedido |
| 2 | escopo | **Obsidian** (obrigatório): dossiê do cliente ou nota do robô |
| 2 | itens processados | banco, via `execucoes.py` |
| 2 | horas e economia | status de sucesso do banco × tempo manual e custo/hora do **cliente** (`valor-local.json`) |
| 2 | disponibilidade | GLPI: chamados de Sustentação do robô (`glpi_sla.py --robo`) |
| 2 | o que foi entregue | status de sucesso do banco + frases do `valor-local.json` |
| 3 | horas, dias úteis, economia | mesmos números do slide 2, abertos |
| 4 | execuções e assertividade | banco, via `execucoes.py` e `status.py` |
| 4 | chamados e SLA | GLPI, via `glpi_sla.py --tudo` |
| 5 | volume mês a mês | banco (status por mês) + volumetria extra da mensagem |
| 6 | falhas detectadas, casos barrados, SLA | banco + GLPI; a faixa é da mensagem |
| 7 | melhorias entregues | você, na mensagem |
| 8 | próximas evoluções | você, na mensagem |
| 8 | oportunidades no segmento | notas de robô do vault, sem nome de cliente |

Os slides 6 a 8 continuam na mensagem porque são **do trimestre**: o que
melhorou, o que se evitou, o que vem. O Obsidian é o que foi vendido, e isso
não muda de um ATE para o outro.

## As fontes locais

Nenhuma delas está no repositório, e é de propósito.

| Fonte | Onde | Para quê |
|---|---|---|
| `.env` | raiz do projeto | credenciais do banco e do GLPI |
| planilha `.xlsx` | raiz do projeto | tabela do robô no banco e a quebra do gráfico |
| `status-local.json` | raiz do projeto | classificação de cada status (sucesso / exceção / falha) |
| `valor-local.json` | raiz do projeto | tempo manual, custo/hora e frases de entrega, por robô |
| vault do Obsidian | máquina | escopo e segmento — **fonte obrigatória, sem alternativa** |
| GLPI | rede | chamados, SLA e disponibilidade do trimestre |

O `.env` é por máquina — copie o `.env.exemplo` e preencha. Os acessos são
**somente leitura**: nenhum script escreve no banco nem no GLPI.

**Nenhum caminho é fixo no código.** O projeto é onde o `montar.py` está; a
planilha é a `.xlsx` que estiver junto dele; o vault sai do registro do próprio
Obsidian, ou da pasta que tiver um `.obsidian` dentro. As colunas da planilha
são achadas pelo cabeçalho, não pela posição, e a carteira pode ter qualquer
tamanho — cada gerente tem a sua.

## A capa não tem logo de cliente

O `template.pptx` segue o modelo oficial da Yank: a capa traz só o logo da
Yank, fixo. O gerador não lê logo de lugar nenhum e o `params.json` não tem
campo de logo — não há o que perguntar, procurar ou anexar.

## Sobre o `--conferir`

Não exige nada especial: usa PowerPoint se houver (Windows) ou LibreOffice se
houver (qualquer sistema). Se não houver nenhum dos dois, o gerador avisa e
segue — o `.pptx` sai igual, só sem a conferência visual automática.
