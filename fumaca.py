# -*- coding: utf-8 -*-
"""Passa o execucoes.py por todos os robôs do robos.csv e confere os totais.

    python fumaca.py <AAAA-MM inicial> <AAAA-MM final>

Para cada par cliente+robô: resolve as tabelas, roda a consulta de status e,
quando houver quebra, também a da quebra — e checa se os dois totais batem.
"""
import csv
import sys
from collections import OrderedDict

import execucoes as ex

ini = sys.argv[1] if len(sys.argv) > 1 else "2026-04"
fim = sys.argv[2] if len(sys.argv) > 2 else "2026-06"

with open(ex.MAPA, encoding="utf-8") as f:
    grupos = OrderedDict()
    for l in csv.DictReader(f):
        grupos.setdefault((l["cliente"], l["robo"].strip()), []).append(l)

print("%-18s %-28s %-10s %-9s %s"
      % ("cliente", "robô", "total", "quebra", "situação"))
falhas = []
for (cliente, robo), ls in grupos.items():
    tabelas = [l["tabela"] for l in ls]
    quebra = next((l["quebra_por"].strip() for l in ls if l["quebra_por"].strip()), "")
    try:
        buckets = ex.apurar(ex.consultar(tabelas, ini, fim), ini, fim)
        total = sum(sum(b.values()) for b in buckets.values())
        situacao = "ok" if total else "SEM EXECUÇÕES"
        if quebra:
            q = ex.apurar_quebra(
                ex.consultar_quebra(tabelas, ini, fim, quebra), ini, fim)
            soma = sum(sum(b.values()) for b in q.values())
            if soma != total:
                situacao = "QUEBRA NÃO BATE (%d)" % soma
        print("%-18s %-28s %-10d %-9s %s"
              % (cliente, robo or "-", total, quebra or "-", situacao))
        if situacao != "ok":
            falhas.append("%s / %s: %s" % (cliente, robo or "-", situacao))
    except Exception as e:                       # noqa: BLE001 - é um smoke test
        print("%-18s %-28s %-10s %-9s ERRO: %s"
              % (cliente, robo or "-", "-", quebra or "-", e))
        falhas.append("%s / %s: %s" % (cliente, robo or "-", e))

print("\n%d robôs testados, %d com pendência" % (len(grupos), len(falhas)))
for f in falhas:
    print("  - %s" % f)
