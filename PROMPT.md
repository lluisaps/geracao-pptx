# Mensagem para pedir um ATE novo

Copie o bloco abaixo, troque o cabeçalho e os textos. O resto da estrutura fica
igual todo mês. Não precisa anexar query, planilha, export do GLPI nem
credencial: tudo isso sai do `.env` e do `robos.csv`.

---

```
Oi! Preciso do ATE deste cliente:

════════════════════════════════════════════════════════════════════
CABEÇALHO — é só isto que muda de um mês para o outro
════════════════════════════════════════════════════════════════════
  Cliente:      <<nome do cliente>>
  Trimestre:    <<Abril, Maio e Junho de 2026>>
  Competência:  <<Jun/26>>   (opcional — sem isto, o último mês do trimestre)
  Robô:         (opcional — se eu não puser e o cliente tiver mais de um,
                 me mostra a lista com o volume de cada e eu escolho)
  Tabela:       (opcional — só se o robô não estiver no robos.csv)

TUDO daqui para baixo se ajusta ao CLIENTE e ao TRIMESTRE do cabeçalho.
Não vou repetir o nome do cliente nem as datas ao longo da mensagem: onde
fizer falta, pega de cima. Se algo no meu texto contradisser o cabeçalho, o
CABEÇALHO VENCE — aplica e me diz qual foi a divergência.

O projeto já está clonado na tua máquina, com o .env configurado. Se estiver
desatualizado, roda um "git pull" antes. Não commita nem faça push.

ANEXO
  O logo do cliente, se ele ainda não estiver em logos/ no repositório.

════════════════════════════════════════════════════════════════════
DADOS — os dois gráficos saem de comando
════════════════════════════════════════════════════════════════════
Roda os dois, com o cliente e o trimestre do cabeçalho:

    python execucoes.py "<cliente>" <1º mês AAAA-MM> <3º mês AAAA-MM> [robô]
    python glpi_sla.py  "<cliente>" <1º mês AAAA-MM> <3º mês AAAA-MM>

Credenciais e conexão vêm do .env. O execucoes.py acha a tabela no robos.csv
só pelo nome do cliente; o glpi_sla.py descobre a entidade no GLPI do mesmo
jeito. Se o cliente tiver mais de um robô, o script para e lista as opções
com o volume de cada uma no período — me mostra essa lista e espera eu
escolher, não chuta.

Cada um imprime uma tabela e devolve o bloco pronto do params.json:
  - execucoes.py  -> grafico_execucoes (uma barra por mês, com o total do mês)
  - glpi_sla.py   -> grafico_sla (os três cartões saem daí, não me passa)

Me mostra as duas tabelas antes de gerar, e junto:
  - qual robô e qual(is) tabela(s) o execucoes.py resolveu;
  - a quebra por status das execuções;
  - se a planilha pedir quebra (por portal, cliente ou etapa), a tabela da
    quebra também, com os totais batendo com os dos status.

A assertividade do trimestre eu te confirmo depois de ver os status — não
preenche por conta própria se nessa base não existir status de erro.

════════════════════════════════════════════════════════════════════
TEXTOS
════════════════════════════════════════════════════════════════════
Resumo do robô pra agenda  →  slide 2
<<uma linha: o que o robô faz>>

Escopo e objetivo  →  slide 3
<<texto corrido; use **termo** para destacar em amarelo>>

Dificuldades / lições aprendidas  →  slide 6
  <<tópico>>
    - <<item>>
  <<tópico>>
    - <<item>>

Pontos de atenção / melhorias  →  slide 7
  <<tópico>>
    - <<item>>

(Os números dos tópicos saem automáticos — não escreve 1., 2., 3.)
(Use **assim** para destacar: amarelo no slide 3, negrito nos slides 6 e 7.)

════════════════════════════════════════════════════════════════════
GERAR E CONFERIR
════════════════════════════════════════════════════════════════════
    python gerar.py params.json ATE-<cliente>-<competência>.pptx --conferir

  - Os meses dos dois gráficos são os três do cabeçalho?
  - Quais números saíram nos cartões do slide 5?
  - Olha as imagens do --conferir: algum texto estourou a caixa?

Me devolve o .pptx.
```

---

## Clientes com mais de um robô

Você só precisa falar o nome do cliente. Para metade deles isso já resolve
sozinho. Para a outra metade o `execucoes.py` **para e lista as opções, com o
volume de cada uma no período**, em vez de escolher por conta própria — um ATE
é de um robô, não de um cliente, e é o robô que o texto do slide 3 descreve:

Quem tem mais de um robô está no `robos.csv` local — o script mostra a lista
na hora, então não precisa decorar nada nem consultar tabela aqui.

## Sobre os anexos

O logo é **obrigatório**. Sem ele o gerador para com erro, em vez de produzir
uma capa com o logo do cliente errado (o que veio no template). Clientes já
atendidos ficam em `logos/`, que é uma pasta local, e não precisam ser
reenviados a cada mês.

## Sobre o `--conferir`

Não exige nada especial: usa PowerPoint se houver (Windows) ou LibreOffice se
houver (qualquer sistema). Se não houver nenhum dos dois, o gerador avisa e
segue — o `.pptx` sai igual, só sem a conferência visual automática.

## Sobre a quebra do gráfico de execuções

Alguns robôs pedem o gráfico separado por uma coluna da tabela, não só o total
do mês. Isso está na coluna `quebra_por` do `robos.csv` local, e sai pronto: o
`execucoes.py` roda uma segunda consulta agrupada por essa coluna e devolve o
bloco com `categorias` e `series` em vez de `meses` e `execucoes`. O gráfico
vira uma série por mês e uma categoria por valor — que é a forma original do
gráfico no template. Os demais robôs seguem com a barra única por mês.
