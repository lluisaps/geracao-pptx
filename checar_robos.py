# -*- coding: utf-8 -*-
"""Confere o robos.csv contra o banco. Somente leitura, uso pontual.

    python checar_robos.py [robos.csv]

Para cada tabela do CSV verifica se ela existe, se tem as colunas que o
execucoes.py usa (time_exec, status_execucao) e qual robô o banco associa a
ela. Para as linhas com `quebra_por` preenchido, procura a coluna da quebra e
lista os valores distintos no trimestre de referência.
"""
import csv
import sys
from collections import OrderedDict

import ambiente
import pymysql

INI, FIM = "2026-04-01", "2026-07-01"   # trimestre de referência da conferência


def conectar():
    host, porta, base, user, senha = ambiente.exigir(
        "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASS")
    con = pymysql.connect(host=host, port=int(porta), user=user, password=senha,
                          database=base, charset="utf8mb4",
                          cursorclass=pymysql.cursors.DictCursor,
                          connect_timeout=20)
    return con, base


def ler_csv(caminho):
    with open(caminho, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def colunas(cur, base, tabelas):
    """{tabela: [colunas]} numa consulta só, em vez de 39 SHOW COLUMNS."""
    marcas = ",".join(["%s"] * len(tabelas))
    cur.execute("SELECT TABLE_NAME AS t, COLUMN_NAME AS c FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=%s AND TABLE_NAME IN (" + marcas + ") "
                "ORDER BY TABLE_NAME, ORDINAL_POSITION", [base] + tabelas)
    mapa = OrderedDict((t, []) for t in tabelas)
    for r in cur.fetchall():
        mapa[r["t"]].append(r["c"])
    return mapa


def robos_do_banco(cur, tabelas):
    """{tabela: nome do robô} pelo caminho sis_robo_execucao -> robo."""
    marcas = ",".join(["%s"] * len(tabelas))
    cur.execute("SELECT e.tabela AS t, r.nome AS robo FROM sis_robo_execucao e "
                "JOIN robo r ON r.id = e.robo_id WHERE e.tabela IN (" + marcas + ")",
                tabelas)
    mapa = {}
    for r in cur.fetchall():
        mapa.setdefault(r["t"], set()).add(r["robo"])
    return mapa


def achar_coluna(cols, palavras):
    for c in cols:
        alvo = c.lower()
        if any(p in alvo for p in palavras):
            return c
    return None


def main(caminho):
    linhas = ler_csv(caminho)
    tabelas = [l["tabela"] for l in linhas]
    con, base = conectar()
    problemas = []
    try:
        with con.cursor() as cur:
            cols = colunas(cur, base, tabelas)
            robos = robos_do_banco(cur, tabelas)

            print("=== tabelas ===")
            print("%-18s %-9s %-9s %-10s %s"
                  % ("tabela", "time_exec", "status", "no tri", "robo no banco"))
            for l in linhas:
                t = l["tabela"]
                c = cols.get(t) or []
                if not c:
                    print("%-18s NAO EXISTE" % t)
                    problemas.append("%s nao existe no schema %s" % (t, base))
                    continue
                tem_time = "time_exec" in c
                tem_status = "status_execucao" in c
                n = "-"
                if tem_time:
                    cur.execute("SELECT COUNT(*) AS n FROM `%s` "
                                "WHERE time_exec >= %%s AND time_exec < %%s" % t,
                                (INI, FIM))
                    n = cur.fetchone()["n"]
                nomes = ", ".join(sorted(robos.get(t, []))) or "(sem vinculo)"
                print("%-18s %-9s %-9s %-10s %s"
                      % (t, "ok" if tem_time else "FALTA",
                         "ok" if tem_status else "FALTA", n, nomes))
                if not tem_time:
                    problemas.append("%s nao tem time_exec" % t)
                if not tem_status:
                    problemas.append("%s nao tem status_execucao" % t)
                if tem_time and n == 0:
                    problemas.append("%s sem execucoes no trimestre de referencia" % t)

            print()
            print("=== quebras pedidas na planilha ===")
            for l in linhas:
                # O quebra_por e escrito a mao no CSV: normaliza caixa e
                # espaco antes de comparar, como o execucoes.py faz.
                q = l["quebra_por"].strip().lower()
                if not q:
                    continue
                t = l["tabela"]
                c = cols.get(t) or []
                # "portal" na planilha nem sempre é uma coluna PORTAL: em
                # algumas tabelas a mesma ideia está sob outro nome.
                palavras = (["portal", "marketplace"] if q == "portal"
                            else ["etapa", "step", "fase"])
                col = achar_coluna(c, palavras)
                print("\n%s / %s  ->  %s (quebra por %r)"
                      % (l["cliente"], l["robo"] or "-", t, q))
                if not col:
                    print("   NAO ACHEI coluna de %r. Colunas: %s" % (q, ", ".join(c)))
                    problemas.append("%s nao tem coluna de %s" % (t, q))
                    continue
                cur.execute("SELECT `%s` AS v, COUNT(*) AS n FROM `%s` "
                            "WHERE time_exec >= %%s AND time_exec < %%s "
                            "GROUP BY `%s` ORDER BY n DESC" % (col, t, col), (INI, FIM))
                valores = cur.fetchall()
                print("   coluna %r, %d valores distintos no trimestre:" % (col, len(valores)))
                for v in valores[:20]:
                    print("      %-40s %d" % (v["v"], v["n"]))
                if len(valores) > 20:
                    print("      ... e mais %d" % (len(valores) - 20))
    finally:
        con.close()

    print()
    print("=== pendencias ===")
    if problemas:
        for p in problemas:
            print(" - %s" % p)
    else:
        print("nenhuma")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "robos.csv")
