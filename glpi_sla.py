# -*- coding: utf-8 -*-
"""
Extrai do GLPI os números de SLA do trimestre e devolve o bloco pronto do
params.json.

    set GLPI_APP=...
    set GLPI_USER=...
    python glpi_sla.py "Cliente Exemplo" 2026-04 2026-06

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

BASE = os.environ.get("GLPI_URL", "https://management.yanksolutions.com.br/apirest.php")
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


def excluir(t):
    """Exclusões globais do dashboard."""
    cat = (t.get(str(F_CATEG)) or "")
    nome = (t.get(str(F_NOME)) or "")
    ent = (t.get(str(F_ENTIDADE)) or "")
    if "Monitoramento" in cat:
        return True
    if nome.startswith("[Projeto] -"):
        return True
    # nome do cliente = primeiro nível depois de "Clientes >"
    if "Clientes >" in ent:
        cliente = ent.split("Clientes >", 1)[1].split(">")[0].strip()
        if cliente == "Yank Solutions!":
            return True
    return False


def apurar(chamados, ini_mes, fim_mes):
    """ini_mes/fim_mes no formato AAAA-MM, inclusivos."""
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
        if excluir(t):
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
    if len(sys.argv) < 4:
        sys.exit('uso: python glpi_sla.py "<cliente>" <AAAA-MM inicial> <AAAA-MM final>')
    cliente, ini, fim = sys.argv[1], sys.argv[2], sys.argv[3]
    sess = abrir_sessao()
    try:
        dados = buscar_chamados(sess, cliente)
        print("chamados lidos para %r: %d" % (cliente, len(dados)))
        buckets = apurar(dados, ini, fim)
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
