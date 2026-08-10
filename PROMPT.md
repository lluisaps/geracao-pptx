# Mensagem para pedir um ATE novo

Copie o bloco abaixo, troque o cabeçalho e os textos, anexe o logo e o export
do GLPI. O resto da estrutura fica igual todo mês.

---

```
Oi! Preciso do ATE da <<CLIENTE>>.

════════════════════════════════════════════════════════════════════
CABEÇALHO — é só isto que muda de um mês para o outro
════════════════════════════════════════════════════════════════════
  Cliente:        <<Cliente Exemplo>>
  Trimestre:      <<Abril, Maio e Junho de 2026>>
  Competência:    <<Jun/26>>   (opcional — sem isto, use o último mês do trimestre)
  Tabela do robô: <<yank_00005623>>

TUDO daqui para baixo se ajusta ao CLIENTE e ao TRIMESTRE do cabeçalho.
Onde eu escrever "o cliente" ou "o trimestre", usa o valor de cima — não
vou repetir o nome nem as datas ao longo da mensagem.

Deriva sozinho, sem me perguntar:
  - os argumentos do glpi_sla.py: o cliente e o trimestre;
  - o logo: o do cliente, em logos/ ou anexado;
  - o nome do arquivo de saída: ATE-<cliente>-<competência>.pptx;
  - a query de execuções: reescreve o CASE (números e nomes dos meses),
    o IN (...) e o YEAR para o trimestre do cabeçalho;
  - o título do gráfico de execuções: "Execuções - Abr/26, Mai/26, Jun/26";
  - os meses do gráfico de SLA e o recorte do export do GLPI;
  - a competência da capa, se eu não tiver preenchido acima.

Se algo no meu texto contradisser o cabeçalho — um mês que não bate, um
título com outro trimestre —, o CABEÇALHO VENCE. Aplica o cabeçalho e me
diz qual foi a divergência, para eu conferir se foi engano meu.

O gerador está em https://github.com/lluisaps/geracao-pptx — clona ele e
segue o README. Me devolve o .pptx pronto. Não precisa commitar nada no
repositório.

ANEXO
  O logo do cliente, se ele ainda não estiver em logos/ no repositório.

════════════════════════════════════════════════════════════════════
EXECUÇÕES  →  slide 4
════════════════════════════════════════════════════════════════════
A query vai colada aqui na mensagem (ela não fica no repositório):

    <<COLE AQUI A QUERY DE EXECUÇÕES>>

A query vem escrita para um trimestre qualquer — reescreve para o do
cabeçalho. O trimestre costuma aparecer em mais de um lugar (CASE, IN, YEAR)
e todos precisam concordar, senão o resultado vem errado sem nenhum aviso.
Me mostra a query final antes de rodar.

Antes de qualquer coisa, testa se o teu ambiente alcança o banco e me diz
qual dos dois casos vale:

  CASO A — você alcança o banco
    Segue a conexão (usuário somente leitura):
      host:    <<host>>
      porta:   <<porta>>
      base:    <<base>>
      usuário: <<usuário>>
      senha:   <<senha>>
    Roda a query você mesmo.
    Não grave a senha em arquivo do repositório e não faça commit dela.
    Se precisar, use variável de ambiente.

  CASO B — você NÃO alcança o banco, ou não recebeu a conexão acima
    Me avisa e para por aí — não tenta contornar. Eu rodo a query no DBeaver
    e te mando o resultado colado ou em CSV, e você segue do mesmo ponto.

A query devolve uma linha por mês × status. O gráfico é o TOTAL DO MÊS —
soma os status de cada mês. O status serve só para a assertividade:

    total do mês  = soma de todas as linhas daquele mês
    assertividade = Sucesso ÷ total, no trimestre inteiro

Em qualquer um dos dois casos, deriva do cabeçalho sem eu precisar repetir:
  - título do gráfico, no formato "Execuções - Jul/26, Ago/26, Set/26"
  - a assertividade, pela fórmula acima
Me mostra a tabela consolidada e a assertividade antes de gerar.

Deriva do cabeçalho, sem eu precisar repetir:
  - título do gráfico, no formato "Execuções - Jul/26, Ago/26, Set/26"
  - assertividade do trimestre = Sucesso ÷ total
Me mostra a tabela consolidada e a assertividade antes de gerar.

════════════════════════════════════════════════════════════════════
SLA  →  slide 5
════════════════════════════════════════════════════════════════════
Não precisa de planilha: puxa direto do GLPI, com o cliente e o trimestre
do cabeçalho.

    set GLPI_APP=<<app_token>>
    set GLPI_USER=<<user_token>>
    python glpi_sla.py "<cliente>" <1º mês AAAA-MM> <3º mês AAAA-MM>

(Em Linux/macOS troca `set` por `export`.)

O script já aplica as regras oficiais do indicador: conta pelo mês da data
de abertura, exclui a categoria Monitoramento, os tickets "[Projeto] -" e a
entidade interna, e trata chamado sem prazo de SLA como dentro do prazo.
Ele devolve o bloco `grafico_sla` pronto para o params.json.

Me mostra a tabela que ele imprimiu antes de gerar. Os três cartões do
slide 5 são calculados a partir desses números — não precisa me passar.

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
CONFERÊNCIA antes de me entregar
════════════════════════════════════════════════════════════════════
  - Os meses do gráfico de execuções, do título e do SLA são os três do
    cabeçalho?
  - Os chamados considerados são só os do trimestre e só deste robô?
  - Quais números saíram nos cartões do slide 5 (total, dentro, fora e %)?
  - Roda com --conferir e olha as imagens: algum texto estourou a caixa?
```

---

## Sobre os anexos

O logo é **obrigatório**. Sem ele o gerador para com erro, em vez de produzir
uma capa com o logo do cliente errado (o que veio no template). Clientes já
atendidos ficam em `logos/` e não precisam ser reenviados.

## Sobre o `--conferir`

Não exige nada especial: usa PowerPoint se houver (Windows) ou LibreOffice se
houver (qualquer sistema). Se não houver nenhum dos dois, o gerador avisa e
segue — o `.pptx` sai igual, só sem a conferência visual automática.

## Sobre o gráfico de execuções

A query acima agrupa por `status_execucao`, ou seja, as categorias do gráfico
serão os status (Sucesso, Erro…). Se o gráfico deste cliente for **por portal**
— como era no ATE de Jun/26, com Portal D, Portal A, Portal B e Portal C —, a query
precisa da coluna de portal:

```sql
GROUP BY MONTH(time_exec), <<coluna de portal>>, status_execucao
```

Rode `DESCRIBE <<tabela do robô>>;` e mande o resultado para ajustarmos a query
uma vez só.
