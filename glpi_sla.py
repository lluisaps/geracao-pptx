# -*- coding: utf-8 -*-
"""
Extrai do GLPI os números de SLA do trimestre e devolve o bloco pronto do
params.json.

    set GLPI_APP=...
    set GLPI_USER=...
    python glpi_sla.py "<cliente>" 2026-04 2026-06
    python glpi_sla.py "<cliente>" 2026-04 2026-06 --tudo
    python glpi_sla.py "<cliente>" 2026-04 2026-06 --tudo --entidade 123
    python glpi_sla.py "<cliente>" 2026-04 2026-06 --tudo --robo ABC01

O --robo acrescenta a disponibilidade estimada do robô (ver o bloco
"disponibilidade" para a regra).

Antes de buscar, o nome do cliente é resolvido para o(s) nó(s) de entidade do
GLPI, e os chamados saem desses nós e de todas as sub-entidades deles, sempre
filtrados por ID. Os nós usados vão impressos no começo da saída — confira que
são os do cliente. Nome que não casa com entidade nenhuma é ERRO, não zero.
O --entidade <id>[,<id>] força a mão. Ver o bloco "entidades" para o porquê.

Regras conforme a documentação canônica do indicador (workflow n8n
"GLPI - Dashboard Indicators", nó MySQL - SLA + Code - Montar Resposta):

  dentro   = solvedate <= time_to_resolve
  fora     = solvedate >  time_to_resolve
  em_risco = sem solvedate e já passou do time_to_resolve
  sem_sla  = time_to_resolve nulo  -> CONTA COMO DENTRO

  SLA geral = (dentro + sem_sla) / (dentro + sem_sla + fora)
  Repare que o denominador NÃO é o total: tickets ainda abertos ficam fora.

Exclusões globais do dashboard, aplicadas aqui também:
  - categoria contendo "Monitoramento"
  - título começando com "[Projeto] -"
  - entidade interna "Yank Solutions!"

O padrão acima reproduz o indicador canônico — é o mesmo número do Dashboard
Sustain para o período.

O --tudo desliga os três filtros. Existe para o ATE, que mostra o VOLUME de
chamados do cliente no trimestre, não o indicador: um cliente cujos chamados
sejam quase todos de Monitoramento sairia com meses zerados no gráfico enquanto
o GLPI tem chamado no período.

Isso é uma divergência DELIBERADA, não um conserto. O SLA impresso com --tudo
não é comparável ao do dashboard no mesmo período, e o total de chamados
tampouco. Não unifique os dois sem decidir antes qual dos números o ATE mostra.

De qualquer forma o script sempre diz quantos chamados do período cada regra
descarta, com ou sem --tudo, para o número nunca sumir calado.
"""
import html
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import OrderedDict
from datetime import datetime

import ambiente
ambiente.carregar()   # lê o .env local, se houver

BASE = os.environ.get("GLPI_URL")
APP = os.environ.get("GLPI_APP")
USER = os.environ.get("GLPI_USER")

MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# ids de campo do Ticket (confirmados via listSearchOptions/Ticket)
F_NOME, F_ID, F_CATEG, F_STATUS = 1, 2, 7, 12
F_ABERTURA, F_SOLUCAO, F_PRAZO, F_ENTIDADE = 15, 17, 18, 80


def _req(url, headers):
    r = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(r, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def abrir_sessao():
    if not BASE:
        sys.exit("defina GLPI_URL no .env — não há endpoint padrão no código")
    if not APP or not USER:
        sys.exit("defina GLPI_APP e GLPI_USER no ambiente (não deixe token em arquivo)")
    d = _req(BASE + "/initSession",
             {"App-Token": APP, "Authorization": "user_token " + USER})
    return d["session_token"]


# ---------------------------------------------------------------- entidades
#
# O cliente é uma ENTIDADE do GLPI e os chamados dele ficam nas SUB-entidades
# (uma por robô, mais a de produção). Achar essa entidade é a parte que mais dá
# errado, porque o nome da planilha quase nunca é o nome do GLPI: um lado tem a
# razão social e o outro o nome curto, um tem apóstrofo e o outro não, um tem
# "&" e o outro escreve "e" — e a API ainda devolve o "&" escapado como HTML.
#
# A versão antiga jogava o nome da planilha num "contains" sobre o campo de
# entidade. Quando o texto não casava, a busca voltava VAZIA e o script seguia
# em frente: o ATE saía com o gráfico de chamados zerado e sem aviso nenhum.
# Zero chamado é um resultado possível e por isso ninguém desconfia.
#
# Agora o nome vira um id de entidade aqui, comparando com a lista de entidades
# do GLPI, e o filtro dos chamados é por id. Nome que não casa é ERRO com a
# lista de candidatos, nunca zero calado.

PAGINA = 200

# Palavras que aparecem de um lado e não do outro; não valem como diferença.
RUIDO = frozenset(["e", "de", "da", "do", "das", "dos", "ltda", "sa", "me",
                   "eireli"])


def normalizar(nome):
    """Texto comparável: sem acento, sem pontuação, minúsculo.

    Desescapa o HTML antes de tudo, porque a API devolve "&#38;" no lugar de
    "&", e troca "&" por " e ", que é como o mesmo nome costuma vir escrito do
    outro lado. O apóstrofo é apagado em vez de virar espaço, para a forma com
    e a forma sem apóstrofo darem no mesmo texto.
    """
    t = html.unescape(nome or "")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("&", " e ")
    for apostrofo in "'’`´":
        t = t.replace(apostrofo, "")
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def palavras(nome):
    return [p for p in normalizar(nome).split() if p not in RUIDO]


def listar_entidades(sess):
    """Todas as entidades visíveis para a sessão."""
    headers = {"App-Token": APP, "Session-Token": sess}
    saida, ini = [], 0
    while True:
        lote = _req(BASE + "/Entity?range=%d-%d" % (ini, ini + PAGINA - 1),
                    headers)
        if not isinstance(lote, list) or not lote:
            break
        saida.extend(lote)
        ini += len(lote)
        if len(lote) < PAGINA:
            break
    return saida


def _descrever(e):
    return "%s (id %s)" % (html.unescape(e.get("completename")
                                         or e.get("name") or "?"), e.get("id"))


def resolver_entidades(sess, cliente, entidade_id=None):
    """Os nós de entidade que são o cliente. LISTA, não um só.

    Casa pelo NOME do nó, não pelo caminho: assim o nó do robô pendurado
    embaixo do cliente não concorre com o cliente, e o cliente não casa por
    acidente com o nome do squad que aparece no caminho dele.

    Vale todo nó cujo nome COMEÇA com o que foi pedido, e é de propósito que
    seja mais de um: nesta árvore o ambiente de produção de alguns clientes é
    um nó IRMÃO do nó do cliente ("<cliente>" e "<cliente> - Ambiente
    produção"), não um filho. Pegar só o primeiro deixaria metade dos chamados
    do cliente de fora. Nó que já está dentro da subárvore de outro nó casado
    é descartado, senão o chamado seria contado duas vezes.

    Se nada começar com o nome pedido, cai para "contém todas as palavras" —
    rede de segurança para nome escrito em outra ordem. Se ainda assim não
    achar nada, é ERRO com os nomes parecidos, nunca zero calado.

    Quem casa com mais de um nó vê a lista impressa com a contagem de cada um;
    se a lista misturar dois clientes diferentes, o desempate é --entidade
    <id> (aceita ids separados por vírgula).
    """
    entidades = listar_entidades(sess)
    if not entidades:
        sys.exit("o GLPI não devolveu nenhuma entidade para esta sessão.")

    if entidade_id is not None:
        pedidos = [i.strip() for i in str(entidade_id).split(",") if i.strip()]
        achados = [e for e in entidades if str(e.get("id")) in pedidos]
        faltando = set(pedidos) - {str(e.get("id")) for e in achados}
        if faltando:
            sys.exit("não há entidade com id %s no GLPI."
                     % ", ".join(sorted(faltando)))
        return achados

    alvo = palavras(cliente)
    if not alvo:
        sys.exit("nome de cliente vazio — não dá para achar a entidade.")

    achados = [e for e in entidades if palavras(e.get("name"))[:len(alvo)] == alvo]
    if not achados:
        achados = [e for e in entidades
                   if set(alvo) <= set(palavras(e.get("name")))]
    if not achados:
        quase = sorted({html.unescape(e.get("name") or "") for e in entidades
                        if set(palavras(e.get("name"))) & set(alvo)})
        sys.exit("nenhuma entidade do GLPI casa com %r.\n"
                 "      O nome da planilha não é o nome do GLPI (razão social,\n"
                 "      apóstrofo, \"&\"): confira e rode com --entidade <id>.\n"
                 "      Nomes parecidos: %s"
                 % (cliente, ", ".join(quase[:12]) or "nenhum"))

    # nó dentro da subárvore de outro nó casado seria contado duas vezes
    caminhos = [(e, html.unescape(e.get("completename") or "")) for e in achados]
    return [e for e, cn in caminhos
            if not any(cn.startswith(outro + " > ")
                       for o, outro in caminhos if o is not e)]


def buscar_chamados(sess, cliente, entidade_id=None):
    """Chamados dos nós do cliente e de TODAS as sub-entidades deles.

    O filtro é por id ("equals" no nó OU "under" na subárvore dele), o que
    dispensa acertar o texto do nome e não depende de como o caminho está
    escrito. Os dois critérios são necessários por nó: "under" pega só os
    descendentes, e chamado aberto direto no nó do cliente ficaria de fora.
    """
    nos = resolver_entidades(sess, cliente, entidade_id)
    print("entidade(s) do cliente %r:" % cliente)
    for e in nos:
        print("  %s" % _descrever(e))
    campos = [F_NOME, F_ID, F_CATEG, F_STATUS, F_ABERTURA, F_SOLUCAO, F_PRAZO, F_ENTIDADE]
    q, i = [], 0
    for e in nos:
        for tipo in ("equals", "under"):
            if i:
                q.append(("criteria[%d][link]" % i, "OR"))
            q.append(("criteria[%d][field]" % i, str(F_ENTIDADE)))
            q.append(("criteria[%d][searchtype]" % i, tipo))
            q.append(("criteria[%d][value]" % i, str(e["id"])))
            i += 1
    for i, c in enumerate(campos):
        q.append(("forcedisplay[%d]" % i, str(c)))
    headers = {"App-Token": APP, "Session-Token": sess}
    saida, ini, total = [], 0, None
    while True:
        url = BASE + "/search/Ticket?" + urllib.parse.urlencode(q) + \
              "&range=%d-%d" % (ini, ini + PAGINA - 1)
        try:
            d = _req(url, headers)
        except urllib.error.HTTPError as erro:
            # entidade sem nenhum chamado: o GLPI recusa a faixa em vez de
            # devolver lista vazia
            if erro.code == 400 and "RANGE_EXCEED" in erro.read().decode(
                    "utf-8", "replace").upper():
                break
            raise
        lote = d.get("data") or []
        if total is None and d.get("totalcount") is not None:
            total = int(d["totalcount"])
        saida.extend(lote)
        if not lote:
            break
        # Avança pelo que VEIO, não pelo que foi pedido. O servidor pode
        # devolver menos que a faixa; somando o pedido, a diferença vira um
        # buraco de chamados que ninguém vê — some do gráfico e pronto.
        ini += len(lote)
        if total is not None and ini >= total:
            break

    # O GLPI já disse quantos são. Se não vieram todos, é melhor parar do que
    # imprimir um número menor com cara de certo.
    if total is not None and len(saida) != total:
        sys.exit("o GLPI contou %d chamado(s) na entidade e vieram %d.\n"
                 "      Não vou seguir com número incompleto." % (total, len(saida)))
    if not saida:
        print("ATENÇÃO: a(s) entidade(s) acima não têm NENHUM chamado em tempo\n"
              "         algum. É a entidade certa? Confira antes de aceitar o\n"
              "         gráfico zerado.")
    return saida


def _dt(v):
    if not v:
        return None
    return datetime.strptime(str(v)[:19], "%Y-%m-%d %H:%M:%S")


def motivo_exclusao(t):
    """Qual das exclusões globais do dashboard descarta este ticket, ou None."""
    cat = (t.get(str(F_CATEG)) or "")
    nome = (t.get(str(F_NOME)) or "")
    ent = (t.get(str(F_ENTIDADE)) or "")
    if "Monitoramento" in cat:
        return "Monitoramento"
    if nome.startswith("[Projeto] -"):
        return "[Projeto] -"
    # nome do cliente = primeiro nível depois de "Clientes >"
    if "Clientes >" in ent:
        cliente = ent.split("Clientes >", 1)[1].split(">")[0].strip()
        if cliente == "Yank Solutions!":
            return "entidade interna"
    return None


def excluir(t):
    """Exclusões globais do dashboard."""
    return motivo_exclusao(t) is not None


def apurar(chamados, ini_mes, fim_mes, tudo=False):
    """ini_mes/fim_mes no formato AAAA-MM, inclusivos.

    tudo=True desliga as exclusões do dashboard — é o modo do ATE.
    """
    a0, m0 = [int(x) for x in ini_mes.split("-")]
    a1, m1 = [int(x) for x in fim_mes.split("-")]
    faixa = []
    a, m = a0, m0
    while (a, m) <= (a1, m1):
        faixa.append((a, m))
        m += 1
        if m == 13:
            a, m = a + 1, 1

    buckets = OrderedDict((am, {"total": 0, "dentro": 0, "fora": 0,
                                "em_risco": 0, "sem_sla": 0}) for am in faixa)
    agora = datetime.now()
    for t in chamados:
        if not tudo and excluir(t):
            continue
        ab = _dt(t.get(str(F_ABERTURA)))
        if not ab or (ab.year, ab.month) not in buckets:
            continue
        b = buckets[(ab.year, ab.month)]
        b["total"] += 1
        sol = _dt(t.get(str(F_SOLUCAO)))
        prazo = _dt(t.get(str(F_PRAZO)))
        if prazo is None:
            b["sem_sla"] += 1
        elif sol is not None:
            b["dentro" if sol <= prazo else "fora"] += 1
        elif agora > prazo:
            b["em_risco"] += 1
    return buckets


def relatorio(buckets):
    print("mes         total  dentro  fora  em_risco  sem_sla   SLA%")
    tot = {k: 0 for k in ("total", "dentro", "fora", "em_risco", "sem_sla")}
    vazios = []
    for (a, m), b in buckets.items():
        for k in tot:
            tot[k] += b[k]
        d = b["dentro"] + b["sem_sla"]
        base = d + b["fora"]
        # Mês sem chamado não tem SLA 0% — não tem SLA. Mostrar 0 aqui faria
        # o slide anunciar uma catástrofe onde só há ausência de dado.
        rotulo = "%5d%%" % round(d / base * 100) if base else "    —"
        if b["total"] == 0:
            vazios.append("%s/%02d" % (MESES[m - 1][:3], a % 100))
        print("%-10s %5d %7d %5d %9d %8d %s"
              % ("%s/%02d" % (MESES[m - 1][:3], a % 100), b["total"], b["dentro"],
                 b["fora"], b["em_risco"], b["sem_sla"], rotulo))
    d = tot["dentro"] + tot["sem_sla"]
    base = d + tot["fora"]
    geral = round(d / base * 100) if base else 0
    print("-" * 58)
    print("%-10s %5d %7d %5d %9d %8d %5d%%"
          % ("TRIMESTRE", tot["total"], tot["dentro"], tot["fora"],
             tot["em_risco"], tot["sem_sla"], geral))
    print()
    print("SLA geral = (dentro + sem_sla) / (dentro + sem_sla + fora)")
    print("          = (%d + %d) / (%d + %d + %d) = %d%%"
          % (tot["dentro"], tot["sem_sla"], tot["dentro"], tot["sem_sla"],
             tot["fora"], geral))
    return tot, geral


def contar_exclusoes(chamados, buckets):
    """Quantos chamados DO PERÍODO cada exclusão do dashboard descarta.

    Conta sempre, inclusive com --tudo: é o que impede um mês de sair zerado
    sem ninguém perceber que o filtro comeu os chamados.
    """
    contagem = OrderedDict()
    for t in chamados:
        motivo = motivo_exclusao(t)
        if not motivo:
            continue
        ab = _dt(t.get(str(F_ABERTURA)))
        if not ab or (ab.year, ab.month) not in buckets:
            continue
        contagem[motivo] = contagem.get(motivo, 0) + 1
    return contagem


def relatorio_exclusoes(contagem, tudo):
    n = sum(contagem.values())
    detalhe = ", ".join("%d %s" % (v, k) for k, v in contagem.items())
    if tudo:
        print("--tudo: exclusões do dashboard DESLIGADAS — todos os chamados "
              "do período entram no cálculo.")
        if n:
            print("        (a regra canônica descartaria %d: %s)" % (n, detalhe))
        return
    if n:
        print("exclusões do dashboard: %d chamado(s) do período fora do "
              "cálculo (%s)." % (n, detalhe))
        print("                        para o ATE, rode de novo com --tudo.")
    else:
        print("exclusões do dashboard: nenhum chamado do período foi descartado.")


# ----------------------------------------------------------- disponibilidade
#
# Não existe registro de "robô fora do ar" no banco (as tabelas de
# monitoramento pararam em 2022) e o intervalo entre execuções não serve: os
# robôs rodam por demanda, então dia sem execução é dia sem demanda.
#
# A fonte é o GLPI, e a categoria importa:
#   - "Monitoramento > Acompanhamento" NÃO é queda. É a checagem de rotina, e
#     quase todos fecham em minutos. Usar esses chamados inventaria queda.
#   - "Sustentação" (Correção, Análise) é o robô com problema. É isto que
#     conta como indisponibilidade, do momento em que o chamado abriu até a
#     solução.
#
# Valem os chamados abertos no nó do robô e os do ambiente compartilhado do
# cliente (produção, nó raiz): problema no ambiente para todos os robôs.
# Chamados de OUTROS robôs do mesmo cliente ficam de fora.
#
# É uma ESTIMATIVA e o slide diz isso. Ela pende para o lado conservador:
# o chamado conta inteiro como indisponível, mesmo que o robô tenha voltado
# antes de alguém registrar a solução.

CODIGO_ROBO = re.compile(r"^[A-Z]{2,4}\d{2,3}\b")


def _no_do_chamado(t):
    return (html.unescape(t.get(str(F_ENTIDADE)) or "")).split(">")[-1].strip()


def _meses_do_periodo(ini_mes, fim_mes):
    a, m = [int(x) for x in ini_mes.split("-")]
    a1, m1 = [int(x) for x in fim_mes.split("-")]
    while (a, m) <= (a1, m1):
        yield "%04d-%02d" % (a, m), m
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)


def disponibilidade(chamados, ini_mes, fim_mes, robos, agora=None,
                    por_mes=True):
    """Disponibilidade estimada do(s) robô(s) no período, 24x7.

    robos = códigos como estão no nó do GLPI ("ABC01"). Devolve um dict com
    percentual, horas indisponíveis, horas do período e os chamados usados.
    Com por_mes, também "meses": a mesma conta mês a mês, para o comparativo
    do slide (cada mês com as próprias horas; chamado que atravessa a virada
    do mês conta em cada mês só a parte dele).
    """
    meses = None
    if por_mes:
        meses = []
        for am, m in _meses_do_periodo(ini_mes, fim_mes):
            d = disponibilidade(chamados, am, am, robos, agora, por_mes=False)
            meses.append(OrderedDict([
                ("mes", MESES[m - 1]),
                ("percentual", None if d["percentual"] is None
                 else round(d["percentual"], 3)),
                ("horas_indisponivel", d["horas_indisponivel"]),
                ("chamados", d["chamados"])]))
    a0, m0 = [int(x) for x in ini_mes.split("-")]
    a1, m1 = [int(x) for x in fim_mes.split("-")]
    inicio = datetime(a0, m0, 1)
    fim = datetime(a1 + (m1 == 12), m1 % 12 + 1, 1)
    agora = agora or datetime.now()
    fim_efetivo = min(fim, agora)
    alvo = {r.upper() for r in robos}

    usados, faixas = [], []
    for t in chamados:
        if "Sustenta" not in html.unescape(t.get(str(F_CATEG)) or ""):
            continue
        no = _no_do_chamado(t)
        codigo = CODIGO_ROBO.match(no.upper())
        if codigo and codigo.group(0) not in alvo:
            continue                               # é de outro robô
        ab = _dt(t.get(str(F_ABERTURA)))
        sol = _dt(t.get(str(F_SOLUCAO))) or agora
        if not ab or sol <= inicio or ab >= fim_efetivo:
            continue
        faixas.append((max(ab, inicio), min(sol, fim_efetivo)))
        usados.append(t)

    # junta faixas sobrepostas: dois chamados do mesmo incidente não dobram
    horas_fora, atual = 0.0, None
    for a, b in sorted(faixas):
        if atual and a <= atual[1]:
            atual = (atual[0], max(atual[1], b))
            continue
        if atual:
            horas_fora += (atual[1] - atual[0]).total_seconds() / 3600
        atual = (a, b)
    if atual:
        horas_fora += (atual[1] - atual[0]).total_seconds() / 3600

    horas = (fim_efetivo - inicio).total_seconds() / 3600
    pct = 100.0 * (1 - horas_fora / horas) if horas > 0 else None
    d = OrderedDict([("percentual", pct),
                     ("horas_indisponivel", round(horas_fora, 1)),
                     ("horas_periodo", round(max(horas, 0))),
                     ("chamados", len(usados))])
    if meses is not None:
        d["meses"] = meses
    d["_usados"] = usados
    return d


def relatorio_disponibilidade(d, robos):
    print("disponibilidade estimada de %s (chamados de Sustentação do robô "
          "e do ambiente do cliente, 24x7):" % ", ".join(robos))
    for t in sorted(d["_usados"], key=lambda t: t.get(str(F_ABERTURA)) or ""):
        print("  %s -> %s  %-28s %s"
              % ((t.get(str(F_ABERTURA)) or "")[:16],
                 (t.get(str(F_SOLUCAO)) or "em aberto")[:16],
                 html.unescape(t.get(str(F_CATEG)) or "").split(">")[-1].strip()[:28],
                 _no_do_chamado(t)))
    if not d["_usados"]:
        print("  nenhum chamado de Sustentação no período.")
    print("  %.1f h indisponível de %d h  ->  %s"
          % (d["horas_indisponivel"], d["horas_periodo"],
             "—" if d["percentual"] is None else "%.2f%%" % d["percentual"]))
    for m in d.get("meses") or []:
        print("    %-10s %5.1f h  %d chamado(s)  ->  %s"
              % (m["mes"], m["horas_indisponivel"], m["chamados"],
                 "—" if m["percentual"] is None else "%.3f%%" % m["percentual"]))


def bloco_params(buckets):
    meses, chamados, dentro = [], [], []
    for (a, m), b in buckets.items():
        meses.append(MESES[m - 1])
        chamados.append(b["total"])
        dentro.append(b["dentro"] + b["sem_sla"])
    return OrderedDict([("titulo", "Chamados por Mês - SLA"),
                        ("meses", meses),
                        ("chamados", chamados),
                        ("dentro_do_sla", dentro)])


if __name__ == "__main__":
    tudo = "--tudo" in sys.argv[1:]
    entidade, robos, args, pulando = None, [], [], None
    for a in sys.argv[1:]:
        if pulando == "--entidade":
            entidade, pulando = a, None
        elif pulando == "--robo":
            robos, pulando = [r.strip() for r in a.split(",") if r.strip()], None
        elif a in ("--entidade", "--robo"):
            pulando = a
        elif not a.startswith("--"):
            args.append(a)
    if len(args) < 3:
        sys.exit('uso: python glpi_sla.py "<cliente>" <AAAA-MM inicial> '
                 '<AAAA-MM final> [--tudo] [--entidade <id>] [--robo <código>]')
    cliente, ini, fim = args[0], args[1], args[2]
    sess = abrir_sessao()
    try:
        dados = buscar_chamados(sess, cliente, entidade)
        print("chamados lidos para %r: %d" % (cliente, len(dados)))
        buckets = apurar(dados, ini, fim, tudo)
        print()
        relatorio_exclusoes(contar_exclusoes(dados, buckets), tudo)
        print()
        relatorio(buckets)
        print()
        print('bloco "grafico_sla" para o params.json:')
        print(json.dumps(bloco_params(buckets), ensure_ascii=False, indent=2))
        if robos:
            print()
            relatorio_disponibilidade(disponibilidade(dados, ini, fim, robos), robos)
    finally:
        try:
            _req(BASE + "/killSession", {"App-Token": APP, "Session-Token": sess})
        except Exception:
            pass
