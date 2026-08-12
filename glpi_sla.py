# -*- coding: utf-8 -*-
"""
Extrai do GLPI os números de SLA do trimestre e devolve o bloco pronto do
params.json.

    set GLPI_APP=...
    set GLPI_USER=...
    python glpi_sla.py "<cliente>" 2026-04 2026-06
    python glpi_sla.py "<cliente>" 2026-04 2026-06 --tudo

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
import json
import os
import sys
import urllib.parse
import urllib.request
from collections import OrderedDict
from datetime import datetime

import ambiente
ambiente.carregar()   # lê o .env local, se houver

BASE = os.environ.get("GLPI_URL", "URL-DO-GLPI")
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
    if not APP or not USER:
        sys.exit("defina GLPI_APP e GLPI_USER no ambiente (não deixe token em arquivo)")
    d = _req(BASE + "/initSession",
             {"App-Token": APP, "Authorization": "user_token " + USER})
    return d["session_token"]


def buscar_chamados(sess, cliente):
    campos = [F_NOME, F_ID, F_CATEG, F_STATUS, F_ABERTURA, F_SOLUCAO, F_PRAZO, F_ENTIDADE]
    q = [("criteria[0][field]", str(F_ENTIDADE)),
         ("criteria[0][searchtype]", "contains"),
         ("criteria[0][value]", cliente)]
    for i, c in enumerate(campos):
        q.append(("forcedisplay[%d]" % i, str(c)))
    headers = {"App-Token": APP, "Session-Token": sess}
    saida, ini = [], 0
    while True:
        url = BASE + "/search/Ticket?" + urllib.parse.urlencode(q) + \
              "&range=%d-%d" % (ini, ini + 199)
        d = _req(url, headers)
        lote = d.get("data") or []
        saida.extend(lote)
        if len(saida) >= int(d.get("totalcount", 0)) or not lote:
            break
        ini += 200
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
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 3:
        sys.exit('uso: python glpi_sla.py "<cliente>" <AAAA-MM inicial> '
                 '<AAAA-MM final> [--tudo]')
    cliente, ini, fim = args[0], args[1], args[2]
    sess = abrir_sessao()
    try:
        dados = buscar_chamados(sess, cliente)
        print("chamados lidos para %r: %d" % (cliente, len(dados)))
        buckets = apurar(dados, ini, fim, tudo)
        print()
        relatorio_exclusoes(contar_exclusoes(dados, buckets), tudo)
        print()
        relatorio(buckets)
        print()
        print('bloco "grafico_sla" para o params.json:')
        print(json.dumps(bloco_params(buckets), ensure_ascii=False, indent=2))
    finally:
        try:
            _req(BASE + "/killSession", {"App-Token": APP, "Session-Token": sess})
        except Exception:
            pass
