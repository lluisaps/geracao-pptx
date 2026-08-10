# -*- coding: utf-8 -*-
"""Sonda pontual: valores distintos de uma coluna no trimestre. Só leitura.

    python probe.py <tabela> <coluna> [AAAA-MM-DD ini] [AAAA-MM-DD fim]
"""
import sys

import ambiente
import pymysql

tabela, coluna = sys.argv[1], sys.argv[2]
ini = sys.argv[3] if len(sys.argv) > 3 else "2026-04-01"
fim = sys.argv[4] if len(sys.argv) > 4 else "2026-07-01"
for nome in (tabela, coluna):
    if not nome.replace("_", "").isalnum():
        raise SystemExit("nome suspeito: %r" % nome)

host, porta, base, user, senha = ambiente.exigir(
    "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASS")
con = pymysql.connect(host=host, port=int(porta), user=user, password=senha,
                      database=base, charset="utf8mb4",
                      cursorclass=pymysql.cursors.DictCursor, connect_timeout=20)
try:
    with con.cursor() as cur:
        cur.execute("SELECT `%s` AS v, COUNT(*) AS n FROM `%s` "
                    "WHERE time_exec >= %%s AND time_exec < %%s "
                    "GROUP BY `%s` ORDER BY n DESC" % (coluna, tabela, coluna),
                    (ini, fim))
        linhas = cur.fetchall()
        print("%s.%s — %d valores distintos entre %s e %s"
              % (tabela, coluna, len(linhas), ini, fim))
        for r in linhas[:30]:
            print("   %-45s %d" % (r["v"], r["n"]))
        if len(linhas) > 30:
            print("   ... e mais %d" % (len(linhas) - 30))
finally:
    con.close()
