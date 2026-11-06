# -*- coding: utf-8 -*-
"""
Gera o ATE em .pptx a partir do template institucional + params.json.

    python gerar.py params.json saida.pptx

Só o conteúdo muda: layout, fontes, cores e decoração vêm intactos do template.
Use **texto** dentro das strings para destacar (azul no escopo do slide 2,
negrito nas entregas e nos slides 4 e 5).

Slides (até 9; os marcados com * são opcionais e só ficam quando o
params.json tem dado para eles):

  1 capa · 2 resumo executivo (valor gerado) · 3* horas e valor financeiro ·
  4 indicadores de operação · 5* volume processado · 6* o que fizemos para
  evitar falhas · 7 melhorias entregues · 8 próximas evoluções · 9 encerramento

O modelo oficial tem 11 tipos de slide; os opcionais vêm dele, pelo
construir_template.py.
"""
import json
import os
import re
import shutil
import sys
from copy import deepcopy

try:
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.oxml.ns import qn
except ImportError:
    sys.exit("falta a dependência python-pptx.  Instale com:\n\n"
             "    python -m pip install python-pptx\n")

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.pptx")
XMLSPACE = "{http://www.w3.org/XML/1998/namespace}space"


# ----------------------------------------------------------------- utilidades
def achar(slide, nome):
    """Acha uma forma pelo nome, inclusive dentro de grupos."""
    def busca(shapes):
        for sh in shapes:
            if sh.name == nome:
                return sh
            if sh.shape_type is not None and str(sh.shape_type).startswith("GROUP"):
                achou = busca(sh.shapes)
                if achou is not None:
                    return achou
        return None
    sh = busca(slide.shapes)
    if sh is None:
        raise KeyError("forma %r não encontrada" % nome)
    return sh


def runs_de(p):
    return p.findall(qn("a:r"))


def negritar(run_el):
    """Clona um run e marca negrito."""
    r = deepcopy(run_el)
    rPr = r.find(qn("a:rPr"))
    if rPr is None:
        rPr = r.makeelement(qn("a:rPr"), {})
        r.insert(0, rPr)
    rPr.set("b", "1")
    return r


def escrever(p, texto, r_normal, r_destaque):
    """Reescreve o parágrafo, alternando formatação em cada **trecho**."""
    for tag in ("a:r", "a:br", "a:fld"):
        for el in p.findall(qn(tag)):
            p.remove(el)
    fim = p.find(qn("a:endParaRPr"))
    partes = re.split(r"\*\*(.+?)\*\*", texto)
    for i, parte in enumerate(partes):
        if parte == "":
            continue
        r = deepcopy(r_destaque if (i % 2) else r_normal)
        t = r.find(qn("a:t"))
        t.text = parte
        t.set(XMLSPACE, "preserve")
        if fim is not None:
            fim.addprevious(r)
        else:
            p.append(r)


def trocar_texto(p, texto):
    """Troca o texto do parágrafo inteiro mantendo a formatação do 1º run."""
    rn = deepcopy(runs_de(p)[0])
    escrever(p, texto, rn, rn)


def prototipos(shape):
    """Colhe do template um parágrafo de tópico, um de item e um vazio."""
    txb = shape.text_frame._txBody
    proto_top = proto_item = proto_vazio = None
    for p in txb.findall(qn("a:p")):
        pPr = p.find(qn("a:pPr"))
        tem_runs = bool(runs_de(p))
        if pPr is not None and pPr.find(qn("a:buAutoNum")) is not None and tem_runs and proto_top is None:
            proto_top = deepcopy(p)
        elif pPr is not None and pPr.find(qn("a:buChar")) is not None and tem_runs and proto_item is None:
            proto_item = deepcopy(p)
        elif not tem_runs and proto_vazio is None:
            proto_vazio = deepcopy(p)
    return proto_top, proto_item, proto_vazio


def montar_coluna(shape, blocos, numero_inicial, proto_top, proto_item, proto_vazio):
    """Reconstrói uma coluna dos slides 6/7 a partir dos blocos do params."""
    txb = shape.text_frame._txBody
    for p in txb.findall(qn("a:p")):
        txb.remove(p)

    n = numero_inicial
    for bi, bloco in enumerate(blocos):
        p = deepcopy(proto_top)
        pPr = p.find(qn("a:pPr"))
        bu = pPr.find(qn("a:buAutoNum")) if pPr is not None else None
        if bu is not None:
            bu.set("startAt", str(n))
        rn = runs_de(p)[0]
        escrever(p, bloco["topico"], rn, negritar(rn))
        txb.append(p)
        n += 1

        for item in bloco.get("itens", []):
            pi = deepcopy(proto_item)
            ri = runs_de(pi)[0]
            escrever(pi, item, ri, negritar(ri))
            txb.append(pi)

        if bi < len(blocos) - 1 and proto_vazio is not None:
            txb.append(deepcopy(proto_vazio))

    # Caixa de texto sem nenhum <a:p> é XML inválido: coluna vazia faz o
    # PowerPoint recusar o arquivo inteiro.
    if txb.find(qn("a:p")) is None:
        txb.append(deepcopy(proto_vazio) if proto_vazio is not None
                   else txb.makeelement(qn("a:p"), {}))
    return n


# --------------------------------------------------------------- gráficos
# Os gráficos do template têm a planilha EMBUTIDA, então replace_data() troca
# o cache e a planilha juntos — "Editar Dados" no PowerPoint abre os números
# certos. O formato e as cores de cada série vêm do template; séries a mais
# são removidas e as que faltam são clonadas da última.
def escrever_grafico(chart, categorias, series):
    """series = lista de (nome, valores[, formato]) na ordem do gráfico."""
    cd = CategoryChartData()
    cd.categories = categorias
    for item in series:
        cd.add_series(item[0], item[1], number_format=item[2] if len(item) > 2 else "#,##0")
    chart.replace_data(cd)


def trocar_titulo(chart, texto):
    pt = chart.chart_title.text_frame._txBody.findall(qn("a:p"))[0]
    trocar_texto(pt, texto)


# ------------------------------------------------------------- números
def milhar(n):
    """9470 -> '9.470' (formato brasileiro, sem casas)."""
    return "{:,.0f}".format(n).replace(",", ".")


def decimal_br(v, casas=1):
    t = ("{:,.%df}" % casas).format(v)
    return t.replace(",", "X").replace(".", ",").replace("X", ".")


def reais(v):
    """Valor curto para cartão: R$ 950 / R$ 53,2 mil / R$ 1,4 mi."""
    if v >= 1e6:
        return "R$ %s mi" % decimal_br(v / 1e6)
    if v >= 1e4:
        return "R$ %s mil" % decimal_br(v / 1e3)
    return "R$ %s" % milhar(v)


def pct_piso(v):
    """Percentual com uma casa, arredondado PARA BAIXO: 99,99 vira 99,9%, e
    só sai 100% quando foi 100% mesmo. Arredondar para cima anunciaria
    disponibilidade total num trimestre que teve parada."""
    if v >= 100:
        return "100%"
    piso = int(v * 10) / 10.0
    return "%s%%" % decimal_br(piso, 0 if piso.is_integer() else 1)


A_CONFIRMAR = "a confirmar"


def preencher_cartao(slide, nome, numero, legenda, detalhe):
    ps = achar(slide, nome).text_frame._txBody.findall(qn("a:p"))
    trocar_texto(ps[0], numero)
    if numero == A_CONFIRMAR:
        # o texto não cabe no corpo do número; diminui só neste cartão
        runs_de(ps[0])[0].find(qn("a:rPr")).set("sz", "1600")
    trocar_texto(ps[1], legenda)
    trocar_texto(ps[2], detalhe)


def montar_lista(shape, itens):
    """Mantém o 1º parágrafo (título) e refaz os itens a partir do 2º."""
    txb = shape.text_frame._txBody
    ps = txb.findall(qn("a:p"))
    proto = deepcopy(ps[1])
    for p in ps[1:]:
        txb.remove(p)
    for item in itens:
        p = deepcopy(proto)
        r = runs_de(p)[0]
        escrever(p, item, r, negritar(r))
        txb.append(p)


# ------------------------------------------------------- slides do modelo
# Cada slide é reconhecido por uma forma que só ele tem — a ordem do
# template pode mudar sem quebrar o gerador.
MARCAS = [
    ("valor", "Slide Valor"),
    ("volume", "Slide Volume"),
    ("prevencao", "Slide Prevencao"),
    ("resumo", "Escopo"),
    ("indicadores", "Grafico Execucoes"),
    ("capa", "Capa"),
]


def _tem(slide, nome):
    try:
        achar(slide, nome)
        return True
    except KeyError:
        return False


def identificar(prs):
    """{papel: slide}. Os dois slides de colunas (Esquerda/Direita) são, na
    ordem, melhorias e próximas evoluções."""
    papeis, colunas = {}, []
    for slide in prs.slides:
        papel = next((p for p, m in MARCAS if _tem(slide, m)), None)
        if papel:
            papeis[papel] = slide
        elif _tem(slide, "Esquerda"):
            colunas.append(slide)
    papeis["melhorias"], papeis["proximas"] = colunas[:2]
    return papeis


def remover_slide(prs, slide):
    lista = prs.slides._sldIdLst
    for sid in list(lista):
        if prs.part.related_part(sid.rId) is slide.part:
            prs.part.drop_rel(sid.rId)
            lista.remove(sid)
            return


def _p0(slide, nome):
    return achar(slide, nome).text_frame._txBody.findall(qn("a:p"))[0]


def cabecalho(slide, tag, titulo, subtitulo):
    """Tag, título (**trecho** em azul) e subtítulo de um slide do modelo."""
    trocar_texto(_p0(slide, "Tag"), tag)
    p = _p0(slide, "Titulo")
    rs = runs_de(p)
    escrever(p, titulo, deepcopy(rs[0]), deepcopy(rs[-1]))
    trocar_texto(_p0(slide, "Subtitulo"), subtitulo)


def _estilo(p, tamanho=None, negrito=False, centro=False):
    for r in runs_de(p):
        rPr = r.find(qn("a:rPr"))
        rPr.attrib.pop("err", None)     # sublinhado de ortografia do lorem
        if tamanho:
            rPr.set("sz", str(int(tamanho * 100)))
        if negrito:
            rPr.set("b", "1")
    if centro:
        pPr = p.find(qn("a:pPr"))
        if pPr is None:
            pPr = p.makeelement(qn("a:pPr"), {})
            p.insert(0, pPr)
        pPr.set("algn", "ctr")


def _texto(slide, nome, texto, tamanho=None, negrito=False):
    p = _p0(slide, nome)
    trocar_texto(p, texto)
    _estilo(p, tamanho, negrito)


def slide_valor(slide, itens, minutos, horas, custo, pct_disp, detalhe_disp, disp):
    """Tipo 'números' do modelo: horas, economia e disponibilidade abertas."""
    cabecalho(slide, "Valor Gerado", "Horas e Valor **Financeiro**",
              "Como chegamos aos números do trimestre")
    casas = 0 if float(minutos).is_integer() else 1
    _texto(slide, "Cabecalho Horas", "Horas economizadas")
    _texto(slide, "Numero Horas", "%s h" % milhar(horas), 28, True)
    # legenda e pílula cabem em UMA linha cada (a pílula tem ~1,3")
    _texto(slide, "Legenda Horas", "%s itens × %s min manuais"
           % (milhar(itens), decimal_br(minutos, casas)), 9)
    _texto(slide, "Pilula Horas", "≈ %s dias úteis" % milhar(horas / 8), 11)

    _texto(slide, "Cabecalho Economia", "Valor financeiro")
    if custo:
        _texto(slide, "Numero Economia", reais(horas * custo), 28, True)
        _texto(slide, "Legenda Economia", "%s h × custo médio da equipe"
               % milhar(horas), 9)
    else:
        _texto(slide, "Numero Economia", A_CONFIRMAR, 20, True)
        _texto(slide, "Legenda Economia", "falta o custo/hora médio da equipe", 9)
    _texto(slide, "Pilula Economia",
           "R$ %s/h" % milhar(custo) if custo else "estimativa", 11)

    _texto(slide, "Cabecalho Disponibilidade", "Disponibilidade")
    _texto(slide, "Numero Disponibilidade", pct_disp,
           28 if pct_disp != A_CONFIRMAR else 20, True)
    _texto(slide, "Legenda Disponibilidade", detalhe_disp, 9)
    n = (disp or {}).get("chamados")
    _texto(slide, "Pilula Disponibilidade",
           "sem parada" if not n else
           "%d chamado%s" % (n, "s" if n > 1 else ""), 11)


def _fmt(v):
    return milhar(v) if isinstance(v, (int, float)) else str(v)


def _celula(cel, texto, tamanho=None, negrito=False, centro=False):
    corpo = cel.text_frame._txBody
    ps = corpo.findall(qn("a:p"))
    for extra in ps[1:]:
        corpo.remove(extra)
    rn = deepcopy(runs_de(ps[0])[0])
    escrever(ps[0], texto, rn, negritar(rn))
    _estilo(ps[0], tamanho, negrito, centro)


def slide_volume(slide, vol):
    """Tipo 'tabelas' do modelo: uma linha por entrega, uma coluna por mês."""
    cabecalho(slide, "Volume", vol.get("titulo", "Volume **Processado**"),
              vol.get("subtitulo", "O que o robô entregou, mês a mês"))
    forma = achar(slide, "Tabela Volume")
    tbl = forma.table._tbl
    colunas = [""] + list(vol["colunas"])
    linhas = vol["linhas"]

    # colunas: clona uma coluna do MEIO e insere antes da última — a última
    # tem borda direita diferente, e a linha termina num <a:extLst> depois do
    # qual nenhuma célula é lida. Para remover, tira as do meio pelo mesmo
    # motivo.
    grid = tbl.find(qn("a:tblGrid"))
    trs = tbl.findall(qn("a:tr"))
    while len(grid.findall(qn("a:gridCol"))) < len(colunas):
        gcs = grid.findall(qn("a:gridCol"))
        gcs[-1].addprevious(deepcopy(gcs[1]))
        for tr in trs:
            tcs = tr.findall(qn("a:tc"))
            tcs[-1].addprevious(deepcopy(tcs[1]))
    while len(grid.findall(qn("a:gridCol"))) > len(colunas):
        grid.remove(grid.findall(qn("a:gridCol"))[-2])
        for tr in trs:
            tr.remove(tr.findall(qn("a:tc"))[-2])
    # 1ª coluna (o rótulo) mais larga; o resto divide o que sobra
    gcs = grid.findall(qn("a:gridCol"))
    primeira = int(forma.width * 0.40)
    for i, gc in enumerate(gcs):
        gc.set("w", str(primeira if i == 0 else
                        (forma.width - primeira) // (len(gcs) - 1)))

    # linhas: cabeçalho + uma por item, clonadas da 1ª linha de dados
    modelo_linha = deepcopy(trs[1])
    for tr in trs[1:]:
        tbl.remove(tr)
    for _ in linhas:
        tbl.append(deepcopy(modelo_linha))

    t = forma.table
    for j, nome in enumerate(colunas):
        _celula(t.cell(0, j), nome, centro=j > 0)
    for i, linha in enumerate(linhas, 1):
        forte = bool(linha.get("destaque"))
        _celula(t.cell(i, 0), linha["rotulo"], 11, forte)
        for j, v in enumerate(linha["valores"], 1):
            _celula(t.cell(i, j), _fmt(v), 11, forte, centro=True)


def slide_prevencao(slide, prev):
    """Tipo 'destaques' do modelo: três números e uma faixa de contexto."""
    cabecalho(slide, "Prevenção",
              prev.get("titulo", "O que fizemos para **evitar falhas**"),
              prev.get("subtitulo",
                       "Falhas detectadas e tratadas sem impacto na operação"))
    for i, d in enumerate(prev["destaques"][:3], 1):
        ps = achar(slide, "Texto Destaque %d" % i).text_frame._txBody.findall(qn("a:p"))
        rs = runs_de(ps[0])
        # no modelo o 1º run é azul e o último é branco
        escrever(ps[0], "**%s** %s" % (d["numero"], d["titulo"]),
                 deepcopy(rs[-1]), deepcopy(rs[0]))
        trocar_texto(ps[2], d.get("texto", ""))
    faixa = prev.get("faixa") or {}
    p = _p0(slide, "Faixa Titulo")
    rs = runs_de(p)
    escrever(p, faixa.get("titulo", "**Operação** protegida"),
             deepcopy(rs[-1]), deepcopy(rs[0]))
    trocar_texto(_p0(slide, "Faixa Texto"), faixa.get("texto", ""))


# ------------------------------------------------------------------ principal
def gerar(params, saida):
    cfg = json.load(open(params, encoding="utf-8"))
    prs = Presentation(TEMPLATE)
    papeis = identificar(prs)
    # s[...] mantém a ordem antiga para o miolo do código não mudar:
    # capa, resumo, indicadores, melhorias, próximas
    s = [papeis[k] for k in ("capa", "resumo", "indicadores", "melhorias",
                             "proximas")]

    # ---------------------------------------------------------- slide 1: capa
    # A capa do modelo oficial não tem logo de cliente: só o da Yank, que é
    # fixo. Muda apenas a competência, na segunda linha.
    capa = achar(s[0], "Capa")
    trocar_texto(capa.text_frame._txBody.findall(qn("a:p"))[1], cfg["competencia"])

    # ----------------------------------------- slide 2: resumo executivo
    p = achar(s[1], "Escopo").text_frame._txBody.findall(qn("a:p"))[0]
    r_normal, r_marca = (deepcopy(r) for r in runs_de(p)[:2])  # 2º run: azul
    escrever(p, cfg["escopo"], r_normal, r_marca)

    g = cfg["grafico_execucoes"]
    volume = (sum(sum(x["valores"]) for x in g["series"]) if g.get("series")
              else sum(g["execucoes"]))
    preencher_cartao(s[1], "Volume", milhar(volume), "itens processados",
                     "no trimestre")

    # Horas e economia são estimativa: itens entregues × tempo manual médio,
    # e horas × custo/hora. As duas entradas vêm do cliente; sem elas o
    # cartão diz "a confirmar" em vez de inventar um tempo padrão.
    v = cfg.get("valor_gerado") or {}
    itens = v.get("itens_entregues")
    minutos = v.get("minutos_por_item")
    custo = v.get("custo_hora")
    horas = itens * minutos / 60.0 if itens and minutos else None
    if horas is not None:
        casas = 0 if float(minutos).is_integer() else 1
        # o equivalente em dias úteis mora AQUI, junto das horas: é a mesma
        # grandeza em outra unidade (8 h/dia), e o cartão já diz a base
        preencher_cartao(s[1], "Horas", "%s h" % milhar(horas),
                         "horas de trabalho poupadas",
                         "≈ %s dias úteis · %s min por item"
                         % (milhar(horas / 8), decimal_br(minutos, casas)))
    else:
        preencher_cartao(s[1], "Horas", A_CONFIRMAR, "horas de trabalho poupadas",
                         "falta o tempo manual por item")
    if horas is not None and custo:
        preencher_cartao(s[1], "Economia", reais(horas * custo), "economia estimada",
                         "%s h × R$ %s/h de custo operacional"
                         % (milhar(horas), milhar(custo)))
    else:
        preencher_cartao(s[1], "Economia", A_CONFIRMAR, "economia estimada",
                         "falta o custo/hora da equipe" if horas is not None
                         else "depende das horas poupadas")

    # Disponibilidade: o montar.py estima pelos chamados de Sustentação do
    # GLPI; quem tiver número melhor (healthcheck) sobrescreve e diz a fonte.
    disp = cfg.get("disponibilidade") or {}
    if disp.get("percentual") is not None:
        pct_disp = pct_piso(disp["percentual"])
        h = disp.get("horas_indisponivel")
        if disp.get("fonte"):
            resumo_disp = detalhe_disp = disp["fonte"]
        else:
            resumo_disp = "pelos chamados de sustentação"
            detalhe_disp = ("%s h de parada no trimestre" % decimal_br(h) if h
                            else "nenhuma parada registrada")
        # Comparativo mês a mês no slide 3: o número grande é o do trimestre
        # e a linha de baixo mostra cada mês (mesma régua, piso de 1 casa).
        meses_disp = [m for m in disp.get("meses") or []
                      if m.get("percentual") is not None]
        if meses_disp and not disp.get("fonte"):
            detalhe_disp = " · ".join(
                "%s %s" % (m["mes"][:3], pct_piso(m["percentual"]))
                for m in meses_disp)
    else:
        pct_disp = A_CONFIRMAR
        resumo_disp = detalhe_disp = "sem fonte no período"
    preencher_cartao(s[1], "Disponibilidade", pct_disp, "disponibilidade estimada",
                     resumo_disp)

    montar_lista(achar(s[1], "Entregas"), v.get("entregas", []))

    if horas is None or not custo:
        nota = ("Horas e economia: falta o cliente informar o tempo manual "
                "médio por item e o custo/hora da equipe.")
    else:
        nota = ("Horas e economia estimadas com o tempo manual médio por item "
                "e o custo/hora %s." % (v.get("origem") or "informados pelo cliente"))
    if disp.get("percentual") is not None and not disp.get("fonte"):
        nota += (" Disponibilidade estimada pelo tempo dos chamados de "
                 "sustentação, 24x7.")
    trocar_texto(achar(s[1], "Nota").text_frame._txBody.findall(qn("a:p"))[0], nota)

    # ------------------------------------- slide 3: indicadores de operação
    # Execuções em dois formatos. O normal é uma barra por mês, com o TOTAL do
    # mês — a quebra por status serve só para a assertividade, não vira eixo.
    # O outro é o quebrado (por portal, cliente ou etapa): uma série por mês e
    # uma categoria por valor, que é a forma do gráfico no template.
    grafico = achar(s[2], "Grafico Execucoes").chart
    quebrado = bool(g.get("series"))
    if quebrado:
        escrever_grafico(grafico, g["categorias"],
                         [(x["nome"], x["valores"]) for x in g["series"]])
    else:
        escrever_grafico(grafico, g["meses"], [("Execuções", g["execucoes"])])
    # com série única a legenda só repetiria a palavra "Execuções"
    grafico.has_legend = quebrado
    if quebrado:
        grafico.legend.include_in_layout = False
    trocar_titulo(grafico, g["titulo"])

    ass = g.get("assertividade")
    if isinstance(ass, (int, float)):
        ass = pct_piso(ass)
    preencher_cartao(s[2], "Assertividade", ass or A_CONFIRMAR,
                     "assertividade do robô", "exceção de negócio conta como acerto")

    sla = cfg["grafico_sla"]
    total = sum(sla["chamados"])
    dentro = sum(sla["dentro_do_sla"])
    pct_dentro = round(dentro / total * 100) if total else 0

    # A linha de "Dentro do SLA" guarda uma fração, no eixo secundário; com o
    # padrão "#,##0" o rótulo saía arredondado para inteiro (0,5 virava "1").
    grafico = achar(s[2], "Grafico SLA").chart
    escrever_grafico(grafico, sla["meses"], [
        ("Total Chamados", sla["chamados"]),
        ("Dentro do SLA", [round(d / c, 10) if c else 0
                           for d, c in zip(sla["dentro_do_sla"], sla["chamados"])],
         "0%"),
    ])
    trocar_titulo(grafico, sla.get("titulo", "Chamados por Mês - SLA"))
    if total:
        preencher_cartao(s[2], "SLA", "%d%%" % pct_dentro, "chamados dentro do SLA",
                         "%d de %d chamados" % (dentro, total))
    else:
        preencher_cartao(s[2], "SLA", "—", "chamados dentro do SLA",
                         "nenhum chamado no período")
    preencher_cartao(s[2], "Disponibilidade", pct_disp, "disponibilidade estimada",
                     detalhe_disp)

    print("  SLA: total=%d  dentro=%d (%d%%)" % (total, dentro, pct_dentro))
    print("  valor: volume=%d  horas=%s  disponibilidade=%s"
          % (volume, "—" if horas is None else milhar(horas), pct_disp))

    # ------------------------- slides 4 e 5: colunas com tópicos numerados
    for idx, chave in ((3, "melhorias"), (4, "proximas_evolucoes")):
        bloco = cfg[chave]
        forma_esq = achar(s[idx], "Esquerda")
        proto_top, proto_item, proto_vazio = prototipos(forma_esq)
        if proto_item is None:
            proto_item = proto_top
        n = montar_coluna(forma_esq, bloco.get("esquerda", []),
                          bloco.get("numero_inicial", 1),
                          proto_top, proto_item, proto_vazio)
        montar_coluna(achar(s[idx], "Direita"), bloco.get("direita", []), n,
                      proto_top, proto_item, proto_vazio)

    # ------------------------------------------------ slides opcionais
    ocultar = set(cfg.get("ocultar") or [])
    fora = []
    if "valor" in papeis:
        if horas is not None and "valor" not in ocultar:
            slide_valor(papeis["valor"], itens, minutos, horas, custo,
                        pct_disp, detalhe_disp, disp)
        else:
            fora.append("valor")
    if "volume" in papeis:
        vol = cfg.get("volume_processado")
        if vol and vol.get("linhas") and "volume" not in ocultar:
            slide_volume(papeis["volume"], vol)
        else:
            fora.append("volume")
    if "prevencao" in papeis:
        prev = cfg.get("prevencao")
        if prev and prev.get("destaques") and "prevencao" not in ocultar:
            slide_prevencao(papeis["prevencao"], prev)
        else:
            fora.append("prevencao")
    for papel in fora:
        remover_slide(prs, papeis[papel])
    print("  slides: %d%s" % (len(prs.slides),
                              " (fora: %s)" % ", ".join(fora) if fora else ""))

    prs.save(saida)
    return saida


def _render_powerpoint(pptx, destino):
    """Windows com PowerPoint instalado."""
    try:
        import win32com.client as win32
    except ImportError:
        return False
    try:
        app = win32.Dispatch("PowerPoint.Application")
        pres = app.Presentations.Open(pptx, True, False, False)
        pres.Export(destino, "PNG", 1600, 900)
        pres.Close()
        app.Quit()
        return True
    except Exception as e:
        print("  (PowerPoint falhou: %s)" % e)
        return False


def _render_libreoffice(pptx, destino):
    """Linux/macOS/Windows com LibreOffice. Converte para PDF e fatia em PNG."""
    soffice = next((shutil.which(n) for n in ("soffice", "libreoffice")
                    if shutil.which(n)), None)
    if not soffice:
        return False
    import subprocess
    try:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf",
                        "--outdir", destino, pptx],
                       check=True, capture_output=True, timeout=300)
    except Exception as e:
        print("  (LibreOffice falhou: %s)" % e)
        return False
    pdf = os.path.join(destino, os.path.splitext(os.path.basename(pptx))[0] + ".pdf")
    if not os.path.exists(pdf):
        return False
    if shutil.which("pdftoppm"):
        try:
            subprocess.run(["pdftoppm", "-jpeg", "-r", "150", pdf,
                            os.path.join(destino, "slide")],
                           check=True, capture_output=True, timeout=300)
            os.remove(pdf)
        except Exception:
            pass  # sem pdftoppm dá pra conferir pelo PDF mesmo
    return True


def renderizar(caminho, pasta="conferencia"):
    """Exporta os slides para conferência visual.

    Tenta PowerPoint (Windows) e, se não houver, LibreOffice (qualquer SO).
    Nenhum dos dois é requisito para GERAR o .pptx — só para conferir.
    """
    pptx = os.path.abspath(caminho)
    destino = os.path.abspath(pasta)
    if os.path.isdir(destino):
        shutil.rmtree(destino)
    os.makedirs(destino)

    if _render_powerpoint(pptx, destino) or _render_libreoffice(pptx, destino):
        print("  conferência visual em %s" % destino)
        return destino

    shutil.rmtree(destino, ignore_errors=True)
    print("  (sem PowerPoint nem LibreOffice neste ambiente — pulei a\n"
          "   conferência visual. Instale o LibreOffice ou abra o .pptx\n"
          "   e confira na mão.)")
    return None


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    par = args[0] if args else "params.json"
    out = args[1] if len(args) > 1 else "ATE.pptx"
    print("gerando %s a partir de %s" % (out, par))
    gerar(par, out)
    print("pronto: %s" % out)
    if "--conferir" in sys.argv:
        renderizar(out)
