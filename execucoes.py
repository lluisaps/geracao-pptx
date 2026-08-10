# -*- coding: utf-8 -*-
"""
Extrai do banco as execuções do robô no trimestre e devolve o bloco pronto
do params.json.

    python execucoes.py <tabela_do_robo> <AAAA-MM inicial> <AAAA-MM final>
    python execucoes.py yank_00005623 2026-04 2026-06

Credenciais vêm do .env (veja .env.exemplo). Consulta somente leitura.

O gráfico do slide 4 é o TOTAL DO MÊS — uma barra por mês. A quebra por
status_execucao serve só para a assertividade do trimestre:

    total do mês  = soma de todos os status daquele mês
    assertividade = Sucesso / total, no trimestre inteiro
"""
import json
import sys
from collections import OrderedDict
from datetime import date

import ambiente

try:
    import pymysql
except ImportError:
    sys.exit("falta o driver.  Instale com:\n\n    python -m pip install pymysql\n")

MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
ABREV = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
         "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def primeiro_dia(am):
    a, m = [int(x) for x in am.split("-")]
    return date(a, m, 1)


def primeiro_dia_seguinte(am):
    a, m = [int(x) for x in am.split("-")]
    return date(a + 1, 1, 1) if m == 12 else date(a, m + 1, 1)


def conectar():
    host, porta, base, user, senha = ambiente.exigir(
        "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASS")
    return pymysql.connect(host=host, port=int(porta), user=user,
                           password=senha, database=base, charset="utf8mb4",
                           cursorclass=pymysql.cursors.DictCursor,
                           connect_timeout=20)


def resolver_tabela(cliente, ini, fim):
    """Descobre a tabela de execuções do robô do cliente.

    O caminho no banco é:
        vw_robo_cliente   cliente  -> nome do robô
        robo              nome     -> id
        sis_robo_execucao robo_id  -> tabela(s)
    Um robô pode ter mais de uma tabela; devolvemos a que tem dados no
    período, que é a de execuções (as outras são etapas intermediárias).
    """
    con = conectar()
    try:
        with con.cursor() as cur:
            cur.execute("SELECT robo FROM vw_robo_cliente WHERE cliente LIKE %s",
                        ("%" + cliente + "%",))
            robos = [r["robo"] for r in cur.fetchall()]
            if not robos:
                raise SystemExit("nenhum robô encontrado para o cliente %r" % cliente)
            if len(robos) > 1:
                raise SystemExit("o cliente %r tem mais de um robô: %s\n"
                                 "Rode informando a tabela direto."
                                 % (cliente, ", ".join(robos)))
            cur.execute("SELECT id, nome FROM robo WHERE nome = %s", (robos[0],))
            linha = cur.fetchone()
            if not linha:
                raise SystemExit("robô %r não está na tabela robo" % robos[0])
            # A ordem do id importa: a primeira tabela registrada é a de
            # execuções; as seguintes são etapas intermediárias, com volume
            # muito maior (item a item). Escolher "a maior" pega a errada.
            cur.execute("SELECT tabela FROM sis_robo_execucao WHERE robo_id=%s "
                        "ORDER BY id", (linha["id"],))
            tabelas, vistas = [], set()
            for r in cur.fetchall():
                t = r["tabela"]
                if t and t not in vistas and t.replace("_", "").isalnum():
                    vistas.add(t)
                    tabelas.append(t)
            com_dados = []
            for t in tabelas:
                cur.execute("SELECT COUNT(*) AS n FROM `%s` "
                            "WHERE time_exec >= %%s AND time_exec < %%s" % t,
                            (primeiro_dia(ini), primeiro_dia_seguinte(fim)))
                n = cur.fetchone()["n"]
                if n:
                    com_dados.append((t, n))
            if not com_dados:
                raise SystemExit("nenhuma tabela de %r tem execuções no período "
                                 "(candidatas: %s)" % (robos[0], ", ".join(tabelas)))
            escolhida, quantas = com_dados[0]      # a de menor id, não a maior
            print("cliente %r -> robô %r -> tabela %s (%d execuções no período)"
                  % (cliente, robos[0], escolhida, quantas))
            if len(com_dados) > 1:
                print("  (o robô tem outras tabelas com dados no período: %s —"
                      " são etapas, não execuções)"
                      % ", ".join("%s com %d" % x for x in com_dados[1:]))
            return escolhida
    finally:
        con.close()


def consultar(tabela, ini, fim):
    host, porta, base, user, senha = ambiente.exigir(
        "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASS")
    if not tabela.replace("_", "").isalnum():
        raise SystemExit("nome de tabela suspeito: %r" % tabela)

    # Faixa meio-aberta em vez de YEAR()/MONTH(): usa índice em time_exec e
    # atravessa a virada de ano sem tratamento especial.
    sql = (
        "SELECT YEAR(time_exec) AS ano, MONTH(time_exec) AS mes,"
        "       status_execucao, COUNT(*) AS quantidade "
        "FROM `%s` "
        "WHERE time_exec >= %%s AND time_exec < %%s "
        "GROUP BY YEAR(time_exec), MONTH(time_exec), status_execucao "
        "ORDER BY ano, mes, quantidade DESC" % tabela
    )
    con = pymysql.connect(host=host, port=int(porta), user=user,
                          password=senha, database=base, charset="utf8mb4",
                          cursorclass=pymysql.cursors.DictCursor,
                          connect_timeout=20)
    try:
        with con.cursor() as cur:
            cur.execute(sql, (primeiro_dia(ini), primeiro_dia_seguinte(fim)))
            return cur.fetchall()
    finally:
        con.close()


def apurar(linhas, ini, fim):
    a0, m0 = [int(x) for x in ini.split("-")]
    a1, m1 = [int(x) for x in fim.split("-")]
    faixa, a, m = [], a0, m0
    while (a, m) <= (a1, m1):
        faixa.append((a, m))
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)

    buckets = OrderedDict((am, OrderedDict()) for am in faixa)
    for r in linhas:
        chave = (int(r["ano"]), int(r["mes"]))
        if chave in buckets:
            buckets[chave][r["status_execucao"] or "(sem status)"] = int(r["quantidade"])
    return buckets


def relatorio(buckets):
    status = []
    for b in buckets.values():
        for s in b:
            if s not in status:
                status.append(s)

    larg = max([12] + [len(s) for s in status])
    print("mes        " + "".join(("%" + str(larg + 2) + "s") % s for s in status)
          + "%12s" % "TOTAL")
    totais, soma_status = [], OrderedDict((s, 0) for s in status)
    for (a, m), b in buckets.items():
        tot = sum(b.values())
        totais.append(tot)
        for s in status:
            soma_status[s] += b.get(s, 0)
        print("%-10s" % ("%s/%02d" % (ABREV[m - 1], a % 100))
              + "".join(("%" + str(larg + 2) + "d") % b.get(s, 0) for s in status)
              + "%12d" % tot)
    print("-" * (10 + (larg + 2) * len(status) + 12))
    print("%-10s" % "TRIMESTRE"
          + "".join(("%" + str(larg + 2) + "d") % soma_status[s] for s in status)
          + "%12d" % sum(totais))

    geral = sum(totais)
    sucesso = next((v for k, v in soma_status.items()
                    if k.strip().lower().startswith("sucesso")), None)
    print()
    if sucesso is None:
        print("assertividade: não achei um status começando com 'Sucesso'.")
        print("               status vistos: %s" % ", ".join(status))
        pct = None
    else:
        pct = round(sucesso / geral * 100) if geral else 0
        print("assertividade = Sucesso / total = %d / %d = %d%%" % (sucesso, geral, pct))
    return totais, pct


def bloco_params(buckets, totais, pct):
    meses = [MESES[m - 1] for (a, m) in buckets.keys()]
    chaves = list(buckets.keys())
    titulo = "Execuções - " + ", ".join(
        "%s/%02d" % (ABREV[m - 1], a % 100) for (a, m) in chaves)
    saida = OrderedDict([("titulo", titulo)])
    if pct is not None:
        saida["assertividade"] = "Assertividade de %d%% no trimestre" % pct
    saida["meses"] = meses
    saida["execucoes"] = totais
    return saida


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit('uso: python execucoes.py "<cliente ou tabela>" '
                 "<AAAA-MM inicial> <AAAA-MM final>\n"
                 '  ex.: python execucoes.py "Cliente Exemplo" 2026-04 2026-06')
    alvo, ini, fim = sys.argv[1], sys.argv[2], sys.argv[3]
    # aceita tanto o nome do cliente quanto a tabela direto
    tabela = alvo if alvo.startswith("yank_") else resolver_tabela(alvo, ini, fim)
    linhas = consultar(tabela, ini, fim)
    print("linhas retornadas: %d" % len(linhas))
    print()
    buckets = apurar(linhas, ini, fim)
    totais, pct = relatorio(buckets)
    print()
    print('bloco "grafico_execucoes" para o params.json:')
    print(json.dumps(bloco_params(buckets, totais, pct), ensure_ascii=False, indent=2))
