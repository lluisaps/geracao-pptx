# -*- coding: utf-8 -*-
"""
Extrai do banco as execuções do robô no trimestre e devolve o bloco pronto
do params.json.

    python execucoes.py <cliente> <AAAA-MM inicial> <AAAA-MM final> [robo]
    python execucoes.py "<cliente>" 2026-04 2026-06
    python execucoes.py "<cliente>" 2026-04 2026-06 "<robo>"

A tabela sai SEMPRE do robos.csv, ao lado deste arquivo — é a única fonte.
Cliente fora do CSV não é adivinhado pelo banco: o script para e pede a linha.
Clientes com mais de um robô exigem o quarto argumento. Quando o CSV tem
várias linhas para o mesmo par cliente+robô, as tabelas são somadas.

Credenciais vêm do .env (veja .env.exemplo). Consulta somente leitura.

O gráfico do slide 4 é o TOTAL DO MÊS — uma barra por mês. A quebra por
status_execucao serve só para a assertividade do trimestre:

    total do mês  = soma de todos os status daquele mês
    assertividade = Sucesso / total, no trimestre inteiro
"""
import csv
import json
import os
import sys
import unicodedata
from collections import OrderedDict
from datetime import date

import ambiente

MAPA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "robos.csv")

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


def normalizar(texto):
    """Sem acento, sem caixa, sem espaço sobrando — para casar nomes digitados."""
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", texto or "")
                         if unicodedata.category(c) != "Mn")
    return " ".join(sem_acento.lower().split())


def contar(tabelas, ini, fim):
    """Quantas execuções há no período, somando as tabelas. Só para ajudar a
    escolher entre os robôs de um cliente."""
    con = conectar()
    try:
        total = 0
        with con.cursor() as cur:
            for t in tabelas:
                if not t.replace("_", "").isalnum():
                    continue
                cur.execute("SELECT COUNT(*) AS n FROM `%s` "
                            "WHERE time_exec >= %%s AND time_exec < %%s" % t,
                            (primeiro_dia(ini), primeiro_dia_seguinte(fim)))
                total += cur.fetchone()["n"]
        return total
    finally:
        con.close()


def resolver_no_csv(cliente, robo, ini=None, fim=None):
    """(rótulo, [tabelas], coluna_de_quebra) a partir do robos.csv.

    Linhas com o mesmo par cliente+robô são somadas — é assim que o CSV diz
    "pode somar" sem depender de texto livre. Rótulos diferentes são robôs
    diferentes, e portanto ATEs diferentes.
    """
    if not os.path.exists(MAPA):
        return None
    with open(MAPA, encoding="utf-8") as f:
        linhas = [l for l in csv.DictReader(f)
                  if normalizar(l["cliente"]) == normalizar(cliente)]
    if not linhas:
        return None

    grupos = OrderedDict()
    for l in linhas:
        grupos.setdefault(l["robo"].strip(), []).append(l)
    if robo:
        achado = [r for r in grupos if normalizar(r) == normalizar(robo)]
        if not achado:
            raise SystemExit("o robô %r não está no robos.csv para %r.\n"
                             "Opções: %s"
                             % (robo, cliente, ", ".join(r or "(sem código)"
                                                         for r in grupos)))
        rotulo = achado[0]
    elif len(grupos) > 1:
        # Não dá para escolher sozinho: um ATE é de um robô, não de um
        # cliente — o escopo do slide 3 descreve um robô específico. Então
        # lista as opções com o volume de cada uma e deixa a escolha na mão
        # de quem pediu.
        print("o cliente %r tem %d robôs no robos.csv:\n" % (cliente, len(grupos)))
        print("%-32s %-12s %s" % ("robô", "no período", "tabela(s)"))
        for nome, ls in grupos.items():
            tabelas = [l["tabela"] for l in ls]
            quantas = contar(tabelas, ini, fim) if ini else "-"
            print("%-32s %-12s %s"
                  % (nome or "(sem código)", quantas, ", ".join(tabelas)))
        raise SystemExit('\nRode de novo com o robô: python execucoes.py "%s" '
                         '%s %s "<robô>"' % (cliente, ini or "<ini>", fim or "<fim>"))
    else:
        rotulo = list(grupos)[0]

    escolhidas = grupos[rotulo]
    quebra = next((l["quebra_por"].strip() for l in escolhidas
                   if l["quebra_por"].strip()), "")
    return rotulo, [l["tabela"] for l in escolhidas], quebra


def consultar(tabelas, ini, fim):
    host, porta, base, user, senha = ambiente.exigir(
        "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASS")
    for t in tabelas:
        if not t.replace("_", "").isalnum():
            raise SystemExit("nome de tabela suspeito: %r" % t)

    # Faixa meio-aberta em vez de YEAR()/MONTH(): usa índice em time_exec e
    # atravessa a virada de ano sem tratamento especial.
    sql = (
        "SELECT YEAR(time_exec) AS ano, MONTH(time_exec) AS mes,"
        "       status_execucao, COUNT(*) AS quantidade "
        "FROM `%s` "
        "WHERE time_exec >= %%s AND time_exec < %%s "
        "GROUP BY YEAR(time_exec), MONTH(time_exec), status_execucao "
        "ORDER BY ano, mes, quantidade DESC"
    )
    con = pymysql.connect(host=host, port=int(porta), user=user,
                          password=senha, database=base, charset="utf8mb4",
                          cursorclass=pymysql.cursors.DictCursor,
                          connect_timeout=20)
    try:
        linhas = []
        with con.cursor() as cur:
            for t in tabelas:
                cur.execute(sql % t,
                            (primeiro_dia(ini), primeiro_dia_seguinte(fim)))
                linhas.extend(cur.fetchall())
        return linhas
    finally:
        con.close()


# As quebras são poucas e conhecidas, então cada consulta fica escrita por
# extenso. Nome de coluna não entra por variável: quem escolhe é a chave do
# dicionário, e o robos.csv só pode citar uma destas.
SQL_QUEBRA = {
    "PORTAL": (
        "SELECT YEAR(time_exec) AS ano, MONTH(time_exec) AS mes,"
        "       PORTAL AS chave, COUNT(*) AS quantidade "
        "FROM `%s` "
        "WHERE time_exec >= %%s AND time_exec < %%s "
        "GROUP BY YEAR(time_exec), MONTH(time_exec), PORTAL "
        "ORDER BY ano, mes, quantidade DESC"
    ),
    "CLIENTE": (
        "SELECT YEAR(time_exec) AS ano, MONTH(time_exec) AS mes,"
        "       CLIENTE AS chave, COUNT(*) AS quantidade "
        "FROM `%s` "
        "WHERE time_exec >= %%s AND time_exec < %%s "
        "GROUP BY YEAR(time_exec), MONTH(time_exec), CLIENTE "
        "ORDER BY ano, mes, quantidade DESC"
    ),
    "ETAPA": (
        "SELECT YEAR(time_exec) AS ano, MONTH(time_exec) AS mes,"
        "       ETAPA AS chave, COUNT(*) AS quantidade "
        "FROM `%s` "
        "WHERE time_exec >= %%s AND time_exec < %%s "
        "GROUP BY YEAR(time_exec), MONTH(time_exec), ETAPA "
        "ORDER BY ano, mes, quantidade DESC"
    ),
}


def consultar_quebra(tabelas, ini, fim, quebra):
    """Mesma contagem por mês, mas agrupada pela coluna da quebra."""
    if quebra not in SQL_QUEBRA:
        raise SystemExit("quebra %r desconhecida. Conhecidas: %s"
                         % (quebra, ", ".join(sorted(SQL_QUEBRA))))
    host, porta, base, user, senha = ambiente.exigir(
        "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASS")
    for t in tabelas:
        if not t.replace("_", "").isalnum():
            raise SystemExit("nome de tabela suspeito: %r" % t)
    con = pymysql.connect(host=host, port=int(porta), user=user,
                          password=senha, database=base, charset="utf8mb4",
                          cursorclass=pymysql.cursors.DictCursor,
                          connect_timeout=20)
    try:
        linhas = []
        with con.cursor() as cur:
            for t in tabelas:
                cur.execute(SQL_QUEBRA[quebra] % t,
                            (primeiro_dia(ini), primeiro_dia_seguinte(fim)))
                linhas.extend(cur.fetchall())
        return linhas
    finally:
        con.close()


def apurar_quebra(linhas, ini, fim):
    """{(ano, mes): {valor da quebra: quantidade}}, com os meses todos
    presentes mesmo sem dados."""
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
            valor = r["chave"]
            valor = "(vazio)" if valor is None or str(valor).strip() == "" \
                else str(valor)
            b = buckets[chave]
            b[valor] = b.get(valor, 0) + int(r["quantidade"])
    return buckets


def relatorio_quebra(buckets, quebra):
    """Imprime meses x valores da quebra e devolve as categorias ordenadas
    pelo volume do trimestre — a ordem em que vão para o eixo do gráfico."""
    totais = OrderedDict()
    for b in buckets.values():
        for v, n in b.items():
            totais[v] = totais.get(v, 0) + n
    categorias = [v for v, _ in sorted(totais.items(), key=lambda x: -x[1])]

    larg = max([10] + [len(c) for c in categorias])
    print("quebra por %s:" % quebra)
    print("mes        " + "".join(("%" + str(larg + 2) + "s") % c for c in categorias)
          + "%12s" % "TOTAL")
    for (a, m), b in buckets.items():
        print("%-10s" % ("%s/%02d" % (ABREV[m - 1], a % 100))
              + "".join(("%" + str(larg + 2) + "d") % b.get(c, 0) for c in categorias)
              + "%12d" % sum(b.values()))
    print("-" * (10 + (larg + 2) * len(categorias) + 12))
    print("%-10s" % "TRIMESTRE"
          + "".join(("%" + str(larg + 2) + "d") % totais[c] for c in categorias)
          + "%12d" % sum(totais.values()))
    return categorias


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
            # soma em vez de atribuir: um robô pode vir de várias tabelas, e
            # o mesmo status aparece uma vez por tabela.
            status = r["status_execucao"] or "(sem status)"
            b = buckets[chave]
            b[status] = b.get(status, 0) + int(r["quantidade"])
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


def bloco_params_quebra(buckets, categorias, pct):
    """Bloco do gráfico quebrado: uma série por mês, uma categoria por valor
    da quebra — que é o formato nativo do gráfico do template."""
    chaves = list(buckets.keys())
    titulo = "Execuções - " + ", ".join(
        "%s/%02d" % (ABREV[m - 1], a % 100) for (a, m) in chaves)
    saida = OrderedDict([("titulo", titulo)])
    if pct is not None:
        saida["assertividade"] = "Assertividade de %d%% no trimestre" % pct
    saida["categorias"] = categorias
    saida["series"] = [
        OrderedDict([("nome", MESES[m - 1]),
                     ("valores", [buckets[(a, m)].get(c, 0) for c in categorias])])
        for (a, m) in chaves
    ]
    return saida


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit('uso: python execucoes.py "<cliente ou tabela>" '
                 "<AAAA-MM inicial> <AAAA-MM final> [robo]\n"
                 '  o robo so e preciso quando o cliente tem mais de um;\n'
                 '  sem ele o script lista as opcoes e para.')
    alvo, ini, fim = sys.argv[1], sys.argv[2], sys.argv[3]
    robo = sys.argv[4] if len(sys.argv) > 4 else ""
    quebra = ""
    if alvo.startswith("yank_"):              # tabela direto, atalho de sempre
        tabelas = [alvo]
    else:
        achado = resolver_no_csv(alvo, robo, ini, fim)
        if not achado:
            sys.exit("o cliente %r não está no robos.csv.\n"
                     "Acrescente a linha com a tabela yank_ correta — o CSV é "
                     "a única fonte da tabela." % alvo)
        rotulo, tabelas, quebra = achado
        print("cliente %r -> robô %r -> %s"
              % (alvo, rotulo or "(sem código)", ", ".join(tabelas)))
    linhas = consultar(tabelas, ini, fim)
    print("linhas retornadas: %d" % len(linhas))
    print()
    buckets = apurar(linhas, ini, fim)
    totais, pct = relatorio(buckets)

    if quebra:
        # A quebra é uma segunda consulta, não um recorte da primeira: a de
        # cima agrupa por status (assertividade), esta por PORTAL/CLIENTE/ETAPA
        # (o gráfico). Os totais têm que bater.
        print()
        q = apurar_quebra(consultar_quebra(tabelas, ini, fim, quebra), ini, fim)
        categorias = relatorio_quebra(q, quebra)
        soma_q = sum(sum(b.values()) for b in q.values())
        if soma_q != sum(totais):
            print("\nATENÇÃO: a quebra soma %d e os status somam %d — não bate."
                  % (soma_q, sum(totais)))
        bloco = bloco_params_quebra(q, categorias, pct)
    else:
        bloco = bloco_params(buckets, totais, pct)

    print()
    print('bloco "grafico_execucoes" para o params.json:')
    print(json.dumps(bloco, ensure_ascii=False, indent=2))
