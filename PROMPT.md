# Como pedir um ATE

Este arquivo tem o texto pronto para pedir um ATE a uma IA com acesso à
máquina, e a explicação de onde sai cada pedaço do slide.

Copie o bloco abaixo e troque **só o cabeçalho e os slides 6 e 7**. Todo o
resto é fixo — é o que impede o assistente de reinventar o processo a cada mês.

O **objetivo e o escopo (slides 2 e 3) você não escreve**: eles saem do dossiê
do cliente no Obsidian, e quem vai buscar é o `montar.py`.

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

Os três meses dos comandos são os do cabeçalho, nunca os do exemplo. Se
algo no meu texto contradisser o cabeçalho, o CABEÇALHO VENCE — aplica e
me diz qual foi a divergência.


════════════════════════════════════════════════════════════════════
AMBIENTE — nada aqui é pergunta
════════════════════════════════════════════════════════════════════

NÃO te passo caminho de nada: nem do projeto, nem da planilha, nem do
Obsidian. Mudam de máquina para máquina e os scripts acham sozinhos.

O vault do Obsidian é fonte OBRIGATÓRIA deste ATE, não é atalho nem
conveniência: os textos dos slides 2 e 3 só existem lá. Abrir o vault e
ler o dossiê do cliente é passo do processo — se esse passo não
aconteceu, o ATE não está pronto, por mais completo que ele pareça.

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

Clone novo NÃO traz o .env nem a planilha — os dois são locais e ficam
fora do repositório de propósito. Nesse caso: copia o .env.exemplo para
.env e me pede as credenciais, e me pede a planilha para pôr na raiz.
Para e avisa; não inventa dado nem tenta descobrir tabela pelo banco.

A capa vai SEM LOGO. Não pergunta por logo, não procura, não espera
anexo — o gerador já resolve. É o padrão do ATE.


════════════════════════════════════════════════════════════════════
O COMANDO
════════════════════════════════════════════════════════════════════

    python montar.py "<cliente>" <1º mês AAAA-MM> <3º mês AAAA-MM>

Isso sozinho acha a planilha, resolve a tabela do robô, acha o dossiê no
Obsidian, consulta o banco e o GLPI e escreve o params.json.

Se o cliente tiver mais de um robô, ele lista e para. Me mostra a lista e
espera eu escolher — um ATE é de UM ROBÔ SÓ, não chuta e não soma robôs
diferentes. Depois roda de novo com --robo <código>, ou --robo <número da
linha> quando o mesmo código aparecer em mais de uma linha.

Se ele falhar em algum ponto, me diz onde falhou antes de contornar. O
contorno é rodar os dois na mão e montar o params.json você:

    python execucoes.py <tabela> <1º mês> <3º mês>
    python glpi_sla.py "<cliente>" <1º mês> <3º mês> --tudo

O --tudo não é opcional. Sem ele o glpi_sla.py devolve o indicador
canônico do Dashboard Sustain, que descarta a árvore Monitoramento, os
tickets "[Projeto] -" e a entidade interna. Está certo para o indicador e
errado para o ATE: o slide 5 diz "Total de Chamados", que é volume, e
volume não se filtra. Já saiu ATE com mês zerado havendo chamado no GLPI.


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
  - os dois textos do dossiê do Obsidian, cada um com o arquivo .md e a
    seção de onde saiu — se não vier a origem, eu assumo que o texto foi
    escrito de cabeça e devolvo o ATE.

Mês zerado em qualquer um dos dois gráficos é ALERTA, não resultado:
confere na fonte antes de me entregar.


════════════════════════════════════════════════════════════════════
OS TEXTOS DOS SLIDES 2 E 3 SAEM DO OBSIDIAN — SEMPRE
════════════════════════════════════════════════════════════════════

As duas primeiras linhas de texto do params.json — `resumo_escopo` e
`escopo_objetivo` — vêm do DOSSIÊ DO CLIENTE no meu vault do Obsidian, e
de lugar nenhum além dele. Quem acha é o montar.py; ele procura o vault
sozinho e casa o dossiê pelo campo `cliente:` de dentro do arquivo.

Não vale, para preencher esses dois campos:

  - escrever de cabeça a partir do nome do cliente ou do código do robô;
  - deduzir o objetivo pelo que a tabela do banco parece fazer;
  - copiar de um params.json ou de um .pptx de outro ATE;
  - aproveitar o texto que já está no ATE do trimestre passado sem abrir
    o dossiê para conferir.

Condensar e reescrever PODE — é justamente o que o slide 3 pede. Entrar
fato que não está no dossiê, NÃO.

Me diga sempre, para cada um dos dois: qual arquivo .md e qual seção.
Sem essa origem eu não aprovo o texto, porque é o único erro do ATE que
não aparece no PNG do --conferir: texto inventado sai bonito.

Não achou o vault, não achou o dossiê, ou achou e ele não tem o objetivo
do robô que eu pedi? PARA e me pede o texto. Não preenche com texto de
outro cliente, não escreve de cabeça e não segue com placeholder.

Do dossiê sai só isso — nada de valor de contrato, mensalidade, ROI ou
contato.


════════════════════════════════════════════════════════════════════
O QUE O SCRIPT DEIXA MARCADO COM "REVISAR"
════════════════════════════════════════════════════════════════════

SLIDE 3 — escopo, CURTO (texto do dossiê, ver a seção acima)
    O script entrega o texto do dossiê já sem a enumeração de etapas.
    Falta condensar: no mínimo 4 e no máximo 5 linhas na caixa, régua de
    ~300 caracteres visíveis (a caixa comporta ~76 por linha; os ** da
    marcação não contam). Confere no PNG do --conferir, não no olho.

    RESUMIR, não truncar. Pode reescrever condensando, desde que não
    entre nenhum fato que não esteja no dossiê. Nada de frase cortada no
    meio.

      fica: a ação principal + o que ela processa + o sistema onde
            acontece
      sai:  a enumeração de etapas, volumetria, horário de execução,
            parâmetros técnicos

    Me mostra o original e o resumido lado a lado.

SLIDE 2 — resumo do robô (texto do dossiê, ver a seção acima)
    O script propõe uma linha juntando o nome do projeto com a
    segmentação. Me mostra para eu aprovar ou corrigir.

    Se ele avisar que casou o código pelo número e pelas letras (o
    código às vezes vem com as letras trocadas entre a planilha e o
    dossiê), me repassa esse aviso.

ASSERTIVIDADE
    Eu confirmo depois de ver a quebra por status. Não preenche sozinho e
    não reaproveita o valor de um params.json de outro ATE.

SLIDES 6 E 7
    São do trimestre, não do contrato: vão abaixo, na minha mensagem.

ENTIDADE DO GLPI
    O glpi_sla.py imprime a(s) entidade(s) que usou antes da contagem.
    Me repassa essa linha: o nome da planilha não é o nome do GLPI, e é
    ali que dá para ver se ele foi buscar no cliente certo.


════════════════════════════════════════════════════════════════════
SLIDE 6 — dificuldades / lições aprendidas
════════════════════════════════════════════════════════════════════

<tópico>
  - <o que aconteceu no trimestre e o que se aprendeu>

Maiores causas de abertura de chamado
  - <causa>
  - <causa>


════════════════════════════════════════════════════════════════════
SLIDE 7 — pontos de atenção / melhorias
════════════════════════════════════════════════════════════════════

<tópico>
  - <o que vem pela frente>


Os números dos tópicos saem automáticos — não escreve 1., 2., 3.
Use **assim** para destacar: amarelo no slide 3, negrito nos slides 6 e 7.


════════════════════════════════════════════════════════════════════
GERAR E CONFERIR
════════════════════════════════════════════════════════════════════

    python gerar.py params.json ATE-<cliente>-<competência>.pptx --conferir

  - Os meses dos dois gráficos são os três do cabeçalho?
  - Quais números saíram nos cartões do slide 5?
  - Algum texto estourou a caixa no PNG do --conferir?

Me devolve o .pptx.
```

---

## De onde sai cada coisa

| Slide | Conteúdo | Origem |
|---|---|---|
| 1 | competência | cabeçalho do pedido |
| 1 | logo | nenhum — placeholder transparente, sempre |
| 2 | resumo do robô | **dossiê no Obsidian** (obrigatório), nome do projeto + segmentação |
| 3 | escopo e objetivo | **dossiê no Obsidian** (obrigatório), objetivo do projeto (ou do robô) |
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
| planilha `.xlsx` | raiz do projeto | tabela do robô no banco e a quebra do gráfico |
| dossiês | vault do Obsidian | textos dos slides 2 e 3 — **fonte obrigatória, sem alternativa** |
| GLPI | rede | chamados e SLA do trimestre |

O `.env` é por máquina — copie o `.env.exemplo` e preencha. Os acessos são
**somente leitura**: nenhum script escreve no banco nem no GLPI.

**Nenhum caminho é fixo no código.** O projeto é onde o `montar.py` está; a
planilha é a `.xlsx` que estiver junto dele; o vault sai do registro do próprio
Obsidian, ou da pasta que tiver um `.obsidian` dentro. As colunas da planilha
são achadas pelo cabeçalho, não pela posição, e a carteira pode ter qualquer
tamanho — cada gerente tem a sua.

## A capa vai sem logo

Não é opção nem configuração: o `gerar.py` sempre cobre a área do logo com o
`sem-logo.png`, um PNG transparente de 342×101 versionado na raiz. A caixa da
capa fica vazia em todos os ATEs.

Isso existe porque o `template.pptx` já trouxe logo de cliente embutido no
passado. O gerador não lê logo de lugar nenhum e o `params.json` não tem campo
de logo — não há o que perguntar, procurar ou anexar.

## Sobre o `--conferir`

Não exige nada especial: usa PowerPoint se houver (Windows) ou LibreOffice se
houver (qualquer sistema). Se não houver nenhum dos dois, o gerador avisa e
segue — o `.pptx` sai igual, só sem a conferência visual automática.
