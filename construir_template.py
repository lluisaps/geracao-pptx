# -*- coding: utf-8 -*-
"""Acrescenta ao template.pptx os slides opcionais do ATE, copiados do
MODELO OFICIAL de apresentação (o .pptx de 11 tipos de slide).

    python construir_template.py "<caminho do MODELO OFICIAL .pptx>"

Roda uma vez, quando o modelo oficial mudar. O caminho do modelo é sempre
argumento — ele mora na máquina de quem tem o arquivo, não no repositório.

Os slides do modelo são copiados forma por forma para um slide novo com o
MESMO layout (template e modelo têm o mesmo master), e as formas que o
gerar.py preenche ganham nome estável. Nada de imagem nem gráfico é copiado:
os três tipos usados aqui são só caixas, grupos e tabela.

    tipo do modelo        vira                               posição
    8  números        ->  Horas e Valor Financeiro            3
    9  tabelas        ->  Volume Processado                   5
    6  destaques      ->  O que fizemos para evitar falhas    6

Cada slide opcional sai do .pptx final quando o params.json não tem o bloco
dele — o ATE mínimo continua com os 6 slides de sempre.
"""
import os
import sys
from copy import deepcopy

from pptx import Presentation
from pptx.oxml.ns import qn

RAIZ = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(RAIZ, "template.pptx")

# marca que o gerar.py usa para reconhecer cada slide opcional
MARCA = {"valor": "Slide Valor", "volume": "Slide Volume",
         "prevencao": "Slide Prevencao"}


def copiar_slide(destino, origem_slide):
    """Slide novo no destino, com o layout de mesmo nome e as formas da origem."""
    nome = origem_slide.slide_layout.name
    layout = next(l for l in destino.slide_layouts if l.name == nome)
    novo = destino.slides.add_slide(layout)
    arvore = novo.shapes._spTree
    for el in list(arvore):                     # tira os placeholders do layout
        if el.tag not in (qn("p:nvGrpSpPr"), qn("p:grpSpPr")):
            arvore.remove(el)
    for el in origem_slide.shapes._spTree:
        if el.tag in (qn("p:nvGrpSpPr"), qn("p:grpSpPr")):
            continue
        arvore.append(deepcopy(el))
    return novo


def mover(prs, slide, posicao):
    """Move o slide para a posição (1 = primeiro)."""
    lista = prs.slides._sldIdLst
    for sid in lista:
        if prs.slides.get(int(sid.get("id"))) is slide or \
                prs.part.related_part(sid.rId) is slide.part:
            lista.remove(sid)
            lista.insert(posicao - 1, sid)
            return


def renomear(shape, nome):
    shape._element.xpath("./*[1]/p:cNvPr")[0].set("name", nome)


def por_texto(shapes, comeco):
    for sh in shapes:
        if sh.has_text_frame and sh.text_frame.text.strip().startswith(comeco):
            return sh
    raise KeyError(comeco)


def grupos(slide):
    """Grupos do slide da esquerda para a direita, de cima para baixo."""
    gs = [sh for sh in slide.shapes if str(sh.shape_type).startswith("GROUP")]
    return sorted(gs, key=lambda g: (round(g.top / 300000), g.left))


def cabecalho(slide, marca):
    renomear(por_texto(slide.shapes, "Tema do slide"), "Tag")
    renomear(por_texto(slide.shapes, "Slide para"), "Titulo")
    renomear(por_texto(slide.shapes, "Espaço para"), "Subtitulo")
    # forma invisível que identifica o slide para o gerar.py
    sp = slide.shapes.add_textbox(0, 0, 1, 1)
    renomear(sp, marca)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__.split("\n\n")[1].strip())
    modelo = Presentation(sys.argv[1])
    prs = Presentation(TEMPLATE)
    if any(sh.name in MARCA.values() for s in prs.slides for sh in s.shapes):
        sys.exit("o template.pptx já tem os slides opcionais. Use o template "
                 "da branch/commit anterior se quiser reconstruir.")
    if len(modelo.slides) < 9:
        sys.exit("o modelo tem %d slides; esperava o modelo oficial de 11."
                 % len(modelo.slides))

    # 3 — números: três colunas (horas, economia, disponibilidade)
    valor = copiar_slide(prs, modelo.slides[7])
    cabecalho(valor, MARCA["valor"])
    for nome, g in zip(("Horas", "Economia", "Disponibilidade"), grupos(valor)):
        renomear(g, "Coluna " + nome)
        caixas = sorted([sh for sh in g.shapes if sh.has_text_frame
                         and sh.text_frame.text.strip()], key=lambda x: x.top)
        # de cima para baixo: cabeçalho, número, legenda, pílula
        for papel, sh in zip(("Cabecalho", "Numero", "Legenda", "Pilula"), caixas):
            renomear(sh, "%s %s" % (papel, nome))

    # 5 — tabela
    volume = copiar_slide(prs, modelo.slides[8])
    cabecalho(volume, MARCA["volume"])
    tabela = next(sh for sh in volume.shapes if sh.has_table)
    renomear(tabela, "Tabela Volume")
    faixa = next(sh for sh in volume.shapes if sh.name.startswith("Ret")
                 and not sh.has_table and sh.name != "Tag"
                 and not sh.text_frame.text.strip())
    renomear(faixa, "Faixa Tabela")

    # 6 — destaques: três cartões em cima e uma faixa embaixo
    prev = copiar_slide(prs, modelo.slides[5])
    cabecalho(prev, MARCA["prevencao"])
    gs = grupos(prev)
    for i, g in enumerate(gs[:3], 1):
        renomear(g, "Destaque %d" % i)
        renomear(next(sh for sh in g.shapes if sh.has_text_frame
                      and sh.text_frame.text.strip()), "Texto Destaque %d" % i)
    faixa = gs[3]
    renomear(faixa, "Faixa")
    caixas = sorted([sh for sh in faixa.shapes if sh.has_text_frame
                     and sh.text_frame.text.strip()], key=lambda x: x.left)
    renomear(caixas[0], "Faixa Titulo")
    renomear(caixas[1], "Faixa Texto")

    # ordem final: capa, resumo, VALOR, indicadores, VOLUME, PREVENÇÃO,
    # melhorias, próximas, encerramento
    mover(prs, valor, 3)
    mover(prs, volume, 5)
    mover(prs, prev, 6)
    prs.save(TEMPLATE)
    print("template.pptx agora tem %d slides." % len(prs.slides))


if __name__ == "__main__":
    main()
