# -*- coding: utf-8 -*-
"""
Gera o ATE em .pptx a partir do template institucional + params.json.

    python gerar.py params.json saida.pptx

Só o conteúdo muda: layout, fontes, cores e decoração vêm intactos do template.
Use **texto** dentro das strings para destacar (amarelo no slide 3, negrito nos
slides 6 e 7).
"""
import json
import os
import re
import shutil
import sys
import zipfile
from copy import deepcopy

try:
    from pptx import Presentation
    from pptx.oxml.ns import qn
    from pptx.util import Emu, Pt
except ImportError:
    sys.exit("falta a dependência python-pptx.  Instale com:\n\n"
             "    python -m pip install python-pptx\n")

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.pptx")
SEM_LOGO = "sem-logo.png"   # PNG transparente: a capa do ATE vai sempre sem logo
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
    return n


# --------------------------------------------------------------- gráficos
# Os gráficos do template apontam para uma planilha EXTERNA, então
# chart.replace_data() do python-pptx não funciona. O PowerPoint desenha a
# partir do cache embutido no próprio gráfico, então é ele que atualizamos.
CNS = "http://schemas.openxmlformats.org/drawingml/2006/chart"


def qc(tag):
    return "{%s}%s" % (CNS, tag)


def _regravar_cache(cache, valores):
    for pt in cache.findall(qc("pt")):
        cache.remove(pt)
    cnt = cache.find(qc("ptCount"))
    if cnt is None:
        cnt = cache.makeelement(qc("ptCount"), {})
        cache.insert(0, cnt)
    cnt.set("val", str(len(valores)))
    for i, v in enumerate(valores):
        pt = cache.makeelement(qc("pt"), {"idx": str(i)})
        el = cache.makeelement(qc("v"), {})
        el.text = str(v)
        pt.append(el)
        cache.append(pt)


def _cache_de(ser, campo):
    """Devolve o strCache/numCache de c:tx, c:cat ou c:val."""
    alvo = ser.find(qc(campo))
    if alvo is None:
        return None
    for ref in ("strRef", "numRef", "multiLvlStrRef"):
        r = alvo.find(qc(ref))
        if r is None:
            continue
        for cache in ("strCache", "numCache", "multiLvlStrCache"):
            c = r.find(qc(cache))
            if c is not None:
                return c
    return None


def escrever_grafico(chart, categorias, series):
    """series = lista de (nome, valores[, formato]) na ordem do XML.

    Se o gráfico do template tiver mais séries do que as informadas, as
    excedentes são removidas — é o que permite o gráfico de execuções passar
    de 4 portais x 3 meses para 3 meses x 1 série.

    O terceiro elemento é opcional e serve para a série que não é contagem:
    a linha de SLA guarda uma fração, e com o padrão "#,##0" o rótulo saía
    arredondado para inteiro (0,5 virava "1" e 0,43 virava "0").
    """
    sers = chart._chartSpace.findall(".//" + qc("ser"))
    if len(sers) < len(series):
        raise ValueError("o gráfico tem só %d séries e vieram %d"
                         % (len(sers), len(series)))
    for extra in sers[len(series):]:
        extra.getparent().remove(extra)
    sers = sers[:len(series)]
    for ser, item in zip(sers, series):
        nome, valores = item[0], item[1]
        formato = item[2] if len(item) > 2 else "#,##0"
        c = _cache_de(ser, "tx")
        if c is not None:
            _regravar_cache(c, [nome])
        c = _cache_de(ser, "cat")
        if c is not None:
            _regravar_cache(c, categorias)
        c = _cache_de(ser, "val")
        if c is not None:
            _regravar_cache(c, valores)
            # Cada série do template trazia seu próprio formatCode, e o rótulo
            # herda dele: sem isto uma série sai "12.765" e a vizinha "12964",
            # e o zero sai "-" numa e "0" na outra.
            fmt = c.find(qc("formatCode"))
            if fmt is None:
                fmt = c.makeelement(qc("formatCode"), {})
                c.insert(0, fmt)
            fmt.text = formato


# posição da nota de assertividade no slide 4, em pontos (mesma unidade do
# painel "Formatar Forma" do PowerPoint). O gráfico termina em y=397.1 e a
# decoração do rodapé começa perto de y=453 — a faixa entre os dois é livre.
NOTA_X, NOTA_Y, NOTA_L, NOTA_A = 655.0, 404.0, 160.0, 34.9


def escrever_assertividade(slide, texto):
    if not texto:
        return None
    cx = slide.shapes.add_textbox(Emu(int(NOTA_X * 12700)), Emu(int(NOTA_Y * 12700)),
                                  Emu(int(NOTA_L * 12700)), Emu(int(NOTA_A * 12700)))
    cx.name = "Assertividade"
    tf = cx.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = texto
    r.font.size = Pt(11)
    r.font.bold = True
    return cx


def trocar_imagem(slide, nome, caminho):
    """Troca a figura mantendo a caixa reservada: encaixa e centraliza."""
    velha = achar(slide, nome)
    cx, cy = velha.left + velha.width // 2, velha.top + velha.height // 2
    cxa, cya = velha.width, velha.height

    nova = slide.shapes.add_picture(caminho, 0, 0)
    esc = min(cxa / nova.width, cya / nova.height)
    nova.width = int(nova.width * esc)
    nova.height = int(nova.height * esc)
    nova.left = int(cx - nova.width / 2)
    nova.top = int(cy - nova.height / 2)
    nova.name = nome

    velha._element.getparent().remove(velha._element)
    return nova


# ------------------------------------------------------------------ principal
def gerar(params, saida):
    cfg = json.load(open(params, encoding="utf-8"))
    prs = Presentation(TEMPLATE)
    s = list(prs.slides)

    # ---------------------------------------------------------- slide 1: capa
    pilula = achar(s[0], "Retângulo: Cantos Arredondados 13")
    p = pilula.text_frame._txBody.findall(qn("a:p"))[0]
    rn = runs_de(p)[0]
    escrever(p, cfg["competencia"], rn, rn)

    # A capa vai SEM logo, sempre. O sem-logo.png é um PNG transparente que
    # cobre o logo que veio no template (o de OUTRO cliente). Não é opção nem
    # padrão de fallback: o gerador não lê logo de lugar nenhum, então ninguém
    # precisa pedir, procurar ou anexar logo de cliente.
    cam = os.path.join(os.path.dirname(os.path.abspath(__file__)), SEM_LOGO)
    if not os.path.exists(cam):
        sys.exit("erro: %s não está na raiz do projeto.\n"
                 "      Ele é o placeholder transparente da capa." % SEM_LOGO)
    trocar_imagem(s[0], "Imagem 7", cam)
    print("  logo: capa sem logo (%s)" % SEM_LOGO)

    # -------------------------------------------------------- slide 2: agenda
    txt0 = achar(s[1], "Text 0")
    p = txt0.text_frame._txBody.findall(qn("a:p"))[1]
    rn = runs_de(p)[0]
    escrever(p, cfg["resumo_escopo"], rn, rn)

    # -------------------------------------------------- slide 3: escopo/obj.
    corpo = achar(s[2], "CaixaDeTexto 1")
    txb = corpo.text_frame._txBody
    paras = txb.findall(qn("a:p"))
    p_titulo, p_corpo = paras[0], paras[1]
    r_normal = deepcopy(runs_de(p_corpo)[0])
    r_marca = deepcopy(runs_de(p_corpo)[1])          # run com realce amarelo
    for extra in paras[2:]:
        txb.remove(extra)
    escrever(p_corpo, cfg["escopo_objetivo"], r_normal, r_marca)

    # ------------------------------------------------- slide 4: execuções
    # Dois formatos. O normal é uma barra por mês, com o TOTAL do mês — a
    # quebra por status serve só para a assertividade, não vira eixo. O outro
    # é o quebrado (por portal, cliente ou etapa): uma série por mês e uma
    # categoria por valor, que é a forma original do gráfico no template.
    g = cfg["grafico_execucoes"]
    grafico = achar(s[3], "Gráfico 3").chart
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
    plot = grafico.plots[0]
    plot.has_data_labels = True
    plot.data_labels.show_value = True

    # A nota de assertividade vinha dentro do gráfico, ancorada no canto
    # superior direito da área de plotagem. Com uma barra por mês esse canto
    # passou a ser ocupado pela barra mais alta e pelo rótulo dela, então a
    # nota vira caixa de texto do slide, abaixo do gráfico.
    escrever_assertividade(s[3], g.get("assertividade"))

    pt = grafico.chart_title.text_frame._txBody.findall(qn("a:p"))[0]
    rt = runs_de(pt)[0]
    escrever(pt, g["titulo"], rt, rt)

    # ------------------------------------------------------- slide 5: SLA
    sla = cfg["grafico_sla"]
    total = sum(sla["chamados"])
    dentro = sum(sla["dentro_do_sla"])
    fora = total - dentro
    pct_dentro = round(dentro / total * 100) if total else 0
    pct_fora = 100 - pct_dentro

    grafico = achar(s[4], "Gráfico 1").chart
    escrever_grafico(grafico, sla["meses"], [
        ("Total Chamados", sla["chamados"]),
        ("Dentro do SLA", [round(d / c, 10) if c else 0
                           for d, c in zip(sla["dentro_do_sla"], sla["chamados"])],
         "0%"),
    ])
    pt = grafico.chart_title.text_frame._txBody.findall(qn("a:p"))[0]
    rt = runs_de(pt)[0]
    escrever(pt, sla["titulo"], rt, rt)

    cartoes = [
        ("Retângulo: Cantos Arredondados 16", str(total), "Total de Chamados"),
        ("Retângulo: Cantos Arredondados 17", "%d%%" % pct_dentro, "Dentro do SLA (%d)" % dentro),
        ("Retângulo: Cantos Arredondados 18", "%d%%" % pct_fora, "Fora do SLA (%d)" % fora),
    ]
    for nome, numero, legenda in cartoes:
        c = achar(s[4], nome)
        ps = c.text_frame._txBody.findall(qn("a:p"))
        rn = runs_de(ps[0])[0]
        escrever(ps[0], numero, rn, rn)
        rl = runs_de(ps[1])[0]
        escrever(ps[1], legenda, rl, rl)

    print("  SLA: total=%d  dentro=%d (%d%%)  fora=%d (%d%%)"
          % (total, dentro, pct_dentro, fora, pct_fora))

    # ----------------------------------- slides 6 e 7: colunas com tópicos
    for idx, chave, esq, dir_ in (
        (5, "dificuldades", "CaixaDeTexto 3", "CaixaDeTexto 10"),
        (6, "pontos_de_atencao", "CaixaDeTexto 3", "CaixaDeTexto 4"),
    ):
        bloco = cfg[chave]
        forma_esq = achar(s[idx], esq)
        proto_top, proto_item, proto_vazio = prototipos(forma_esq)
        if proto_item is None:
            proto_item = proto_top
        n = montar_coluna(forma_esq, bloco["esquerda"], bloco.get("numero_inicial", 1),
                          proto_top, proto_item, proto_vazio)
        montar_coluna(achar(s[idx], dir_), bloco["direita"], n,
                      proto_top, proto_item, proto_vazio)

    prs.save(saida)

    # O texto da assertividade que vinha embutido no desenho do gráfico
    # (drawing1.xml) é esvaziado: ele agora é uma caixa de texto do slide.
    limpar_desenho_do_grafico(saida)
    return saida


def limpar_desenho_do_grafico(caminho):
    """Zera ppt/drawings/drawing1.xml para não duplicar a nota no slide 4."""
    vazio = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<c:userShapes xmlns:c="http://schemas.openxmlformats.org/'
             'drawingml/2006/chart"/>')
    tmp = caminho + ".tmp"
    achou = False
    with zipfile.ZipFile(caminho) as zin, \
         zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            dados = zin.read(item.filename)
            if item.filename == "ppt/drawings/drawing1.xml":
                dados = vazio.encode("utf-8")
                achou = True
            zout.writestr(item, dados)
    os.replace(tmp, caminho)
    return achou


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
