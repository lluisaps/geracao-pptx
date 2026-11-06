# -*- coding: utf-8 -*-
"""Monta o params.json a partir da planilha, do dossiê e dos dois scripts.

    python montar.py "<cliente>" <AAAA-MM inicial> <AAAA-MM final> [opções]
    python montar.py "<cliente>" 2026-04 2026-06
    python montar.py "<cliente>" 2026-04 2026-06 --robo <código>

    --robo <código|texto>   escolhe o robô quando o cliente tem mais de um;
                            sem isto o script lista as opções e para
    --robo 24,25            junta as linhas 24 e 25 num ATE só (o mesmo robô
                            em dois fluxos, por exemplo)
    --competencia <Mmm/AA>  padrão: o último mês do trimestre
    --planilha <caminho>    padrão: a única .xlsx ao lado deste script
    --vault <caminho>       padrão: o vault que o Obsidian registrou
    --saida <arquivo>       padrão: params.json, ao lado deste script
    --sem-banco             não consulta banco nem GLPI; monta só o que sai
                            da planilha e do dossiê (útil para conferir os
                            textos antes de gastar consulta)

Nenhum caminho é presumido. O projeto é onde este arquivo está; a planilha é
a .xlsx que estiver junto dele; o vault sai do registro do próprio Obsidian
(ou, na falta dele, da pasta que tiver um .obsidian dentro). Nada disso muda
o código de uma máquina para outra.

O que o script resolve sozinho:

    planilha  ->  tabela(s) do robô, se as linhas somam, se há quebra
    dossiê    ->  escopo do robô (faixa do slide 2)
    banco     ->  grafico_execucoes, assertividade e as entregas do
                  trimestre (status de sucesso), via execucoes.py
    GLPI      ->  grafico_sla, via glpi_sla.py --tudo, e a disponibilidade
                  estimada pelos chamados de Sustentação do robô
    vault     ->  automações do mesmo segmento em OUTROS clientes, sem nome
                  de cliente (slide 5, coluna da direita)
    valor-local.json -> tempo manual por item, custo/hora e a frase de cada
                  status de entrega, por robô (fora do git: é dado de cliente)

O que ele NÃO resolve, e marca com REVISAR no params.json:

    escopo              o corte para ~200 caracteres é resumo, não
                        truncagem; quem condensa é gente
    valor_gerado        sem o valor-local.json do robô, as entregas saem com
                        o texto cru do status e horas/economia ficam "a
                        confirmar" no slide
    melhorias           são do trimestre: o script só conta os chamados de
                        Melhoria e de Sustentação do robô, como pista
    proximas_evolucoes  a coluna da esquerda é do robô e não sai de fonte; a
                        da direita sai do vault e precisa virar oportunidade

Nada de valor de contrato, mensalidade, ROI ou contato sai do dossiê.
"""
import io
import json
import os
import re
import sys
import unicodedata
from collections import OrderedDict

# O console do Windows é cp1252 e os dossiês têm seta, travessão e ↔: sem
# isto um print do texto original derruba o script no meio do relatório.
try:
    sys.stdout.reconfigure(errors="replace")
except AttributeError:                                 # Python < 3.7
    pass

RAIZ = os.path.dirname(os.path.abspath(__file__))

ABREV = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
         "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

REVISAR = "REVISAR: "

MESES_NOME = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
              "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# Código de robô: duas a quatro letras e dois ou três dígitos. Não fixa o "R"
# inicial nem o tamanho porque cada gerente numera a carteira do seu jeito.
CODIGO_ROBO = re.compile(r"\b([A-Z]{2,4}\d{2,3})\b")

# Sinônimos de "essas linhas viram um robô só" e de "quebra o gráfico por uma
# coluna". Cada gerente escreve a OBS com as próprias palavras; acrescente
# aqui em vez de mexer na lógica.
SOMAR = ("pode somar", "podem somar", "somar", "soma", "somatorio",
         "juntar", "junta", "agrupar", "agrupado", "mesmo robo")
QUEBRAR = ("separar", "separado", "quebrar", "quebra", "dividir", "abrir",
           "agrupar por", "detalhar")
NAO_E_COLUNA = ("coluna", "colunas", "cada", "aqui", "essa", "esse", "por",
                "pela", "pelo", "as", "os", "a", "o", "em", "no", "na")


# ------------------------------------------------------------------- comuns
def normalizar(texto):
    """Sem acento, sem caixa, sem pontuação — para casar nomes que divergem.

    A planilha e o dossiê grafam a mesma razão social de formas diferentes: um
    escreve "&" onde o outro escreve "e", e um acentua onde o outro não acentua.
    Por isso o "&" vira " e " antes de qualquer comparação.
    """
    texto = (texto or "").replace("&", " e ")
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", texto.lower()).strip()


def mesmo_codigo(a, b):
    """O mesmo robô aparece com as letras do código embaralhadas entre a
    planilha e o dossiê. Casa pelo número e pelo conjunto de letras."""
    a, b = (a or "").upper(), (b or "").upper()
    if not a or not b:
        return False
    if a == b:
        return True
    ma, mb = re.match(r"^([A-Z]+)(\d+)$", a), re.match(r"^([A-Z]+)(\d+)$", b)
    if not ma or not mb:
        return False
    return (ma.group(2) == mb.group(2)
            and sorted(ma.group(1)) == sorted(mb.group(1)))


def rotulo_meses(ini, fim):
    """'Abr/26, Mai/26, Jun/26' a partir de 2026-04 e 2026-06."""
    ai, mi = [int(x) for x in ini.split("-")]
    af, mf = [int(x) for x in fim.split("-")]
    saida, a, m = [], ai, mi
    while (a, m) <= (af, mf):
        saida.append("%s/%02d" % (ABREV[m - 1], a % 100))
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)
    return saida


# ---------------------------------------------------------------- planilha
# O que a planilha precisa ter: uma coluna com o cliente e outra com a tabela
# dele no banco. Nome, posição, aba e quantidade de linhas mudam sem aviso —
# por isso as colunas são achadas pelo cabeçalho, não por índice.
CABECALHOS = {
    "cliente": ("cliente", "empresa", "conta"),
    "tabela": ("tabela", "banco", "base", "schema", "db"),
    "obs": ("obs", "observacao", "observacoes", "nota", "notas", "comentario"),
}


def _mapear_colunas(linha):
    """{papel: índice} a partir de uma linha candidata a cabeçalho.

    Só vale como cabeçalho se tiver as duas colunas obrigatórias; a de OBS é
    opcional, porque planilha sem ela apenas significa nenhum robô com quebra
    nem "pode somar".
    """
    achado = {}
    for i, celula in enumerate(linha):
        nome = normalizar("" if celula is None else str(celula))
        if not nome:
            continue
        for papel, apelidos in CABECALHOS.items():
            if papel in achado:
                continue
            if any(nome == a or nome.startswith(a) for a in apelidos):
                achado[papel] = i
    return achado if "cliente" in achado and "tabela" in achado else None


def ler_planilha(caminho):
    """Linhas cruas da planilha, já com o cliente propagado para baixo.

    Linha com a coluna Cliente em branco pertence ao cliente da última linha
    preenchida acima — é assim que a planilha representa cliente com vários
    robôs.
    """
    try:
        import openpyxl
    except ImportError:
        sys.exit("falta o openpyxl. Instale com:\n\n"
                 "    python -m pip install openpyxl\n")
    if not os.path.exists(caminho):
        sys.exit("erro: não achei %s.\n"
                 "      A planilha fica na raiz do projeto e não vem no "
                 "clone (está no .gitignore)." % caminho)

    wb = openpyxl.load_workbook(caminho, data_only=True)
    for ws in wb.worksheets:
        colunas, cabecalho = None, 0
        for n, row in enumerate(ws.iter_rows(values_only=True), 1):
            colunas = _mapear_colunas(row)
            if colunas:
                cabecalho = n
                break
            if n > 20:          # cabeçalho não aparece depois disso: outra aba
                break
        if not colunas:
            continue

        def celula(row, papel):
            i = colunas.get(papel)
            if i is None or i >= len(row) or row[i] is None:
                return ""
            return str(row[i]).strip()

        linhas, atual = [], ""
        for n, row in enumerate(ws.iter_rows(values_only=True), 1):
            if n <= cabecalho:
                continue
            cliente, tabela = celula(row, "cliente"), celula(row, "tabela")
            if not tabela:
                continue
            if cliente:
                atual = cliente
            linhas.append({"linha": n, "cliente": atual, "tabela": tabela,
                           "obs": celula(row, "obs"), "aba": ws.title})
        if linhas:
            return linhas

    sys.exit("não achei em %s nenhuma aba com uma coluna de cliente e uma de\n"
             "      tabela. Procurei cabeçalho começando por: %s.\n"
             "      Renomeie o cabeçalho ou acrescente o apelido em "
             "CABECALHOS, no topo deste arquivo."
             % (os.path.basename(caminho),
                "; ".join("%s = %s" % (p, "/".join(a))
                          for p, a in CABECALHOS.items())))


def quebra_da_obs(obs):
    """A OBS pede quebra do gráfico? Devolve o apelido da coluna, ou "".

    Aceita "separar pela coluna Portal", "quebrar por etapa", "dividir por
    marketplace" e afins. O apelido devolvido é só uma pista: já houve OBS
    dizendo "coluna Portal" com os valores guardados em outra coluna, com
    outro nome, então quem procura a coluna de verdade é o execucoes.py.
    """
    n = normalizar(obs)
    if not any(v in n for v in QUEBRAR):
        return ""
    m = re.search(r"coluna\s+([a-z0-9_]+)", n)
    if m and m.group(1) not in NAO_E_COLUNA:
        return m.group(1)
    # Sem a palavra "coluna": pega o primeiro termo depois de "por"/"pela".
    for m in re.finditer(r"\bp(?:or|ela|elo)\s+([a-z0-9_]+)", n):
        if m.group(1) not in NAO_E_COLUNA:
            return m.group(1)
    return ""


def pode_somar(obs):
    """A OBS autoriza somar as linhas em branco abaixo num robô só?"""
    n = normalizar(obs)
    return any(re.search(r"\b%s\b" % re.escape(t), n) for t in SOMAR)


def agrupar_robos(linhas):
    """Agrupa as linhas de um cliente em robôs.

    Uma OBS preenchida abre um robô novo; as linhas de OBS vazia logo abaixo
    pertencem a ele. Isso só é legítimo quando a OBS diz "pode somar" — se
    vier linha em branco sem essa autorização, o script avisa em vez de somar
    calado, porque um ATE é de UM robô só.
    """
    robos = []
    for l in linhas:
        if l["obs"] or not robos:
            codigo = CODIGO_ROBO.search(l["obs"].upper())
            descricao = CODIGO_ROBO.sub("", l["obs"].upper()) if codigo else l["obs"]
            if codigo:                    # devolve a caixa original do resto
                descricao = re.sub(re.escape(codigo.group(1)), "", l["obs"],
                                   flags=re.I)
            for termo in SOMAR:
                descricao = re.sub(r"(?i)\b%s\b" % re.escape(termo), "",
                                   descricao)
            descricao = re.sub(r"\s{2,}", " ", descricao).strip(" -–—·|,.")
            robos.append({
                "codigo": codigo.group(1) if codigo else "",
                "descricao": descricao,
                "obs": l["obs"],
                "somavel": pode_somar(l["obs"]),
                "quebra": quebra_da_obs(l["obs"]),
                "tabelas": [l["tabela"]],
                "linhas": [l["linha"]],
            })
        else:
            robos[-1]["tabelas"].append(l["tabela"])
            robos[-1]["linhas"].append(l["linha"])
    return robos


def resolver_robos(caminho, cliente):
    """Todos os robôs do cliente pedido, na ordem da planilha."""
    linhas = ler_planilha(caminho)
    alvo = normalizar(cliente)
    clientes = OrderedDict()
    for l in linhas:
        clientes.setdefault(normalizar(l["cliente"]), []).append(l)

    achados = [k for k in clientes if k == alvo]
    if not achados:
        achados = [k for k in clientes if alvo in k or k in alvo]
    if not achados:
        sys.exit("o cliente %r não está na planilha. Clientes disponíveis:\n  %s"
                 % (cliente, "\n  ".join(sorted(
                     {l["cliente"] for l in linhas}))))
    if len(achados) > 1:
        sys.exit("o nome %r casa com mais de um cliente da planilha: %s.\n"
                 "      Seja mais específica." % (cliente, ", ".join(achados)))

    proprias = clientes[achados[0]]
    return proprias[0]["cliente"], agrupar_robos(proprias)


def etiqueta_do_robo(robo):
    """Como o robô é chamado no --robo. O número da linha é o desempate que
    sempre existe: código repete (o mesmo código em duas linhas) e OBS de
    quebra não tem código nenhum."""
    if robo["codigo"]:
        return robo["codigo"]
    return str(robo["linhas"][0])


def listar_robos(robos, motivo):
    print("%s Escolha com --robo:\n" % motivo)
    for r in robos:
        print("  --robo %-8s  linha%s %-8s  %s%s"
              % (etiqueta_do_robo(r),
                 "s" if len(r["linhas"]) > 1 else " ",
                 ",".join(str(n) for n in r["linhas"]),
                 ", ".join(r["tabelas"]),
                 "  [quebra por %s]" % r["quebra"] if r["quebra"] else ""))
        detalhe = r["descricao"] or (r["obs"] if not r["codigo"] else "")
        if detalhe:
            print("  %-17s %s" % ("", limpar(detalhe)[:90]))
    print("\n  o número é a linha da planilha — use quando o código repetir")
    sys.exit(2)


def escolher_robo(robos, pedido):
    """Um ATE é de um robô só: na dúvida o script para em vez de chutar.

    Aceita o código, o número da linha, ou código + descrição ("<código> <parte
    da descrição>") para quando o mesmo código aparece em mais de uma linha.
    """
    if pedido and "," in pedido:
        # Juntar linhas é decisão de quem pede ("os dois fluxos do ABC01"),
        # nunca do script: só acontece com a lista explícita.
        partes = [escolher_robo(robos, p) for p in pedido.split(",") if p.strip()]
        junto = dict(partes[0])
        junto["tabelas"] = [t for r in partes for t in r["tabelas"]]
        junto["linhas"] = [n for r in partes for n in r["linhas"]]
        junto["descricao"] = " + ".join(r["descricao"] for r in partes if r["descricao"])
        junto["somavel"] = True
        quebras = {r["quebra"] for r in partes}
        junto["quebra"] = partes[0]["quebra"] if len(quebras) == 1 else None
        codigos = {r["codigo"] for r in partes}
        if len(codigos) > 1:
            print("ATENÇÃO: juntando robôs de códigos diferentes (%s); a "
                  "disponibilidade e o valor usam só o %s."
                  % (", ".join(sorted(codigos)), partes[0]["codigo"]))
        return junto

    if not pedido:
        if len(robos) == 1:
            return robos[0]
        return listar_robos(robos, "esse cliente tem %d robôs na planilha."
                            % len(robos))

    if pedido.strip().isdigit():
        linha = int(pedido.strip())
        achados = [r for r in robos if linha in r["linhas"]]
        if not achados:
            sys.exit("a linha %d não é de nenhum robô desse cliente." % linha)
        return achados[0]

    alvo = normalizar(pedido)
    achados = [r for r in robos
               if mesmo_codigo(r["codigo"], pedido)
               or (r["codigo"] and normalizar(r["codigo"]) == alvo)]
    if not achados:
        achados = [r for r in robos if alvo and alvo in normalizar(r["obs"])]
    if not achados:
        sys.exit("não achei o robô %r nas linhas desse cliente." % pedido)
    if len(achados) > 1:
        # Mesmo código em mais de uma linha: só quem pediu sabe qual é.
        refinados = [r for r in achados
                     if alvo != normalizar(r["codigo"])
                     and alvo in normalizar(r["obs"])]
        if len(refinados) == 1:
            return refinados[0]
        return listar_robos(achados, "%r casa com %d linhas desse cliente."
                            % (pedido, len(achados)))
    return achados[0]


# ------------------------------------------------------------------ dossiê
def _registro_do_obsidian():
    """O arquivo onde o próprio Obsidian lista os vaults abertos.

    É a fonte certa para descobrir o caminho: quem escreve nele é o
    aplicativo, em cada máquina, com a pasta que aquele usuário escolheu.
    """
    casa = os.path.expanduser("~")
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.join(
            casa, "AppData", "Roaming")
        return [os.path.join(base, "obsidian", "obsidian.json")]
    if sys.platform == "darwin":
        return [os.path.join(casa, "Library", "Application Support",
                             "obsidian", "obsidian.json")]
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(casa, ".config")
    return [os.path.join(base, "obsidian", "obsidian.json")]


def _vaults_registrados():
    for caminho in _registro_do_obsidian():
        if not os.path.exists(caminho):
            continue
        try:
            dados = json.load(io.open(caminho, encoding="utf-8"))
        except (ValueError, OSError):
            continue
        achados = [v.get("path") for v in dados.get("vaults", {}).values()
                   if v.get("path") and os.path.isdir(v["path"])]
        if achados:
            return achados
    return []


def _vaults_na_casa(limite=4):
    """Procura pastas com .obsidian dentro, que é o que marca um vault.

    Só entra em cena se o registro do aplicativo não existir — vault movido à
    mão, Obsidian portátil, instalação nova. Anda poucos níveis e pula as
    pastas onde ninguém guarda vault, para não varrer o disco inteiro.
    """
    casa = os.path.expanduser("~")
    ignorar = {"appdata", "library", "node_modules", ".git", ".cache",
               "onedrive - temp", "windows", "program files", "$recycle.bin",
               "venv", ".venv", "__pycache__"}
    achados = []
    for pasta, subpastas, _ in os.walk(casa):
        nivel = pasta[len(casa):].count(os.sep)
        if nivel >= limite:
            subpastas[:] = []
            continue
        subpastas[:] = [s for s in subpastas
                        if s.lower() not in ignorar and not s.startswith("$")]
        if ".obsidian" in subpastas:
            achados.append(pasta)
            subpastas[:] = []            # vault não aninha dentro de vault
    return achados


def achar_vault(indicado=None):
    """Os vaults do Obsidian desta máquina. Nenhum caminho é presumido: ou
    vem do registro do próprio aplicativo, ou da marca .obsidian na pasta."""
    if indicado:
        if not os.path.isdir(indicado):
            sys.exit("erro: %r não é uma pasta." % indicado)
        return [indicado]
    achados = _vaults_registrados() or _vaults_na_casa()
    if not achados:
        sys.exit("não achei nenhum vault do Obsidian nesta máquina.\n"
                 "      Procurei no registro do aplicativo (%s) e por pastas\n"
                 "      com .obsidian dentro de %s.\n"
                 "      Se o vault estiver em outro lugar, passe --vault "
                 "<caminho>."
                 % (", ".join(_registro_do_obsidian()),
                    os.path.expanduser("~")))
    return achados


def achar_planilha(indicada=None):
    """A planilha de clientes e tabelas. Não tem nome fixo: o que vale é ser
    a única .xlsx ao lado do script (ou na pasta de onde ele foi chamado)."""
    if indicada:
        if not os.path.exists(indicada):
            sys.exit("erro: não achei a planilha %r." % indicada)
        return indicada
    for pasta in (RAIZ, os.getcwd()):
        achadas = sorted(
            os.path.join(pasta, n) for n in os.listdir(pasta)
            if n.lower().endswith((".xlsx", ".xlsm")) and not n.startswith("~$"))
        if len(achadas) == 1:
            return achadas[0]
        if len(achadas) > 1:
            sys.exit("há %d planilhas em %s. Diga qual com --planilha:\n  %s"
                     % (len(achadas), pasta,
                        "\n  ".join(os.path.basename(a) for a in achadas)))
    sys.exit("não achei nenhuma planilha (.xlsx) ao lado do %s nem em %s.\n"
             "      Ponha a planilha de clientes e tabelas numa das duas, ou\n"
             "      passe --planilha <caminho>."
             % (os.path.basename(__file__), os.getcwd()))


def frontmatter(texto):
    """O bloco --- ... --- do topo, como dicionário raso."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", texto, re.S)
    if not m:
        return {}
    dados = {}
    for linha in m.group(1).splitlines():
        if ":" in linha and not linha.startswith(" "):
            k, v = linha.split(":", 1)
            dados[k.strip()] = v.strip().strip('"').strip("'")
    return dados


def achar_dossies(raizes):
    """Todo .md com 'dossie' nas tags. É um arquivo por cliente."""
    dossies = []
    for raiz in raizes:
        for pasta, _, arquivos in os.walk(raiz):
            if os.path.basename(pasta).startswith("."):
                continue
            for nome in arquivos:
                if not nome.lower().endswith(".md"):
                    continue
                caminho = os.path.join(pasta, nome)
                try:
                    texto = io.open(caminho, encoding="utf-8").read()
                except (OSError, UnicodeDecodeError):
                    continue
                fm = frontmatter(texto)
                if "dossie" in fm.get("tags", "") and fm.get("cliente"):
                    dossies.append((caminho, fm, texto))
    return dossies


def casar_dossie(dossies, cliente):
    """Casa pelo campo 'cliente:' de dentro do arquivo, não pelo nome dele:
    o arquivo traz a razão social e a planilha, o nome curto."""
    alvo = normalizar(cliente)
    exatos = [d for d in dossies if normalizar(d[1]["cliente"]) == alvo]
    if len(exatos) == 1:
        return exatos[0]
    parciais = [d for d in dossies
                if alvo in normalizar(d[1]["cliente"])
                or normalizar(d[1]["cliente"]).startswith(alvo)]
    if len(parciais) == 1:
        return parciais[0]
    if not parciais:
        return None
    sys.exit("mais de um dossiê casa com %r:\n  %s\n"
             "      Desempate no nome do cliente."
             % (cliente, "\n  ".join(d[0] for d in parciais)))


def secao(texto, numero, *palavras):
    """Conteúdo de uma seção, até o próximo título.

    Procura primeiro pelo número ("### 2. ..."), porque é como os dossiês
    estão hoje; se não achar, procura pelo assunto no título, em qualquer
    nível. Assim um dossiê que numere diferente, ou que não numere, continua
    sendo lido.
    """
    tentativas = [r"^#{1,4}\s*%d[\.\)]" % numero]
    tentativas += [r"^#{1,4}\s*(?:\d+[\.\)]\s*)?[^\n]*%s" % re.escape(p)
                   for p in palavras]
    for inicio in tentativas:
        m = re.search(inicio + r"[^\n]*\n(.*?)(?=^#{1,4}\s|\Z)",
                      texto, re.S | re.M | re.I)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return ""


def blocos_de_robo(texto):
    """Os blocos de robô dos dossiês multi-robô.

    Formato de referência: '## 🤖 Robô 1 — <código>: <nome do robô>'. O emoji,
    a palavra "Robô", o número e o tipo de travessão variam entre dossiês, e o
    código não tem tamanho fixo — o que identifica o bloco é um título com um
    código de robô seguido do nome.
    """
    blocos = []
    padrao = (r"^#{2,4}\s*[^\n]*?\b([A-Z]{2,4}\d{2,3})\b\s*[:\-–—]\s*"
              r"([^\n*]+)")
    for m in re.finditer(padrao, texto, re.M):
        inicio = m.end()
        prox = re.search(r"^##\s", texto[inicio:], re.M)
        corpo = texto[inicio:inicio + prox.start()] if prox else texto[inicio:]
        obj = re.search(r"\*\*Objetivo:\*\*\s*(.+?)(?=\n\s*\n|\n\*\*|\Z)",
                        corpo, re.S)
        blocos.append({
            "codigo": m.group(1),
            "nome": re.sub(r"\*|_", "", m.group(2)).strip(" *·"),
            "objetivo": " ".join(obj.group(1).split()) if obj else "",
        })
    return blocos


def limpar(texto):
    """Uma linha só, sem quebra e sem espaço duplicado."""
    return " ".join((texto or "").split())


def encurtar_objetivo(texto):
    """Primeiro corte mecânico do slide 3: fora a enumeração de etapas.

    Não é o resumo final — é o texto do dossiê já sem o que a régua manda
    tirar, para quem for condensar não ter que garimpar. Corta em
    'Contempla:' porque é onde os dossiês passam a listar etapas separadas
    por ponto-e-vírgula, e tira as frases de volumetria e de processo
    anterior, que não descrevem o que o robô faz.
    """
    t = limpar(texto)
    t = re.split(r"(?i)\bcontempla\s*:", t)[0].strip()
    frases = re.split(r"(?<=\.)\s+", t)
    fora = re.compile(r"(?i)volume|lançamentos/m|substitui um processo|"
                      r"hoje 100% manual|24/7|horário|janela de execução")
    frases = [f for f in frases if not fora.search(f)]
    return " ".join(frases).strip(" ;,.") or t


def textos_do_dossie(dossie, robo):
    """(resumo_escopo, escopo_objetivo, origem) — só isso sai do dossiê."""
    caminho, fm, texto = dossie
    arquivo = os.path.basename(caminho)
    seg4 = limpar(secao(texto, 4))
    blocos = blocos_de_robo(texto)

    if blocos:
        # Dossiê multi-robô: não existe seção 1 nem seção 2. O título do
        # bloco faz o papel da seção 1 e o **Objetivo:** faz o da seção 2.
        escolhido, aviso = None, ""
        for b in blocos:
            if mesmo_codigo(b["codigo"], robo["codigo"]):
                escolhido = b
                if b["codigo"].upper() != (robo["codigo"] or "").upper():
                    aviso = ("código casado pelo número e pelas letras: %s na "
                             "planilha, %s no dossiê"
                             % (robo["codigo"], b["codigo"]))
                break
        if escolhido is None and robo["descricao"]:
            alvo = normalizar(robo["descricao"])
            escolhido = next((b for b in blocos
                              if alvo and alvo in normalizar(b["nome"])), None)
        if escolhido is None:
            return None, None, ("%s tem %d blocos de robô e nenhum casou com "
                                "%r. Blocos: %s"
                                % (arquivo, len(blocos), robo["codigo"] or
                                   robo["descricao"],
                                   ", ".join(b["codigo"] for b in blocos)))
        origem = "%s -> bloco %s: %s" % (arquivo, escolhido["codigo"],
                                         escolhido["nome"])
        if aviso:
            origem += "  (%s)" % aviso
        resumo = "%s — %s" % (escolhido["nome"], seg4) if seg4 else escolhido["nome"]
        return limpar(resumo), escolhido["objetivo"], origem

    seg1, seg2 = limpar(secao(texto, 1)), limpar(secao(texto, 2))
    if not seg2:
        return None, None, ("%s não tem '### 2. Objetivo do projeto' nem "
                            "blocos de robô." % arquivo)
    # Da seção 1 interessa o nome do projeto, não o id da proposta nem o
    # status do contrato — o que vier depois de "·" é contrato.
    nome = re.sub(r"\*", "", seg1.split("·")[0]).strip()
    resumo = "%s — %s" % (nome, seg4) if seg4 else nome
    return limpar(resumo), seg2, "%s -> seções 1, 2 e 4" % arquivo


# ------------------------------------------------------------------- dados
def dados_execucoes(tabelas, ini, fim, quebra, robo=None):
    """(grafico_execucoes, assertividade, {status: total}, {status: balde},
    {(ano, mês): {status: total}})."""
    import execucoes
    import status as status_mod
    linhas = execucoes.consultar(tabelas, ini, fim)
    print("linhas retornadas: %d\n" % len(linhas))
    buckets = execucoes.apurar(linhas, ini, fim)
    totais, pct = execucoes.relatorio(buckets, robo)
    soma = OrderedDict()
    for b in buckets.values():
        for st, n in b.items():
            soma[st] = soma.get(st, 0) + n
    baldes = status_mod.apurar(soma, robo)[2]
    if not quebra:
        return (execucoes.bloco_params(buckets, totais, pct), pct, soma,
                baldes, buckets)
    print()
    q = execucoes.apurar_quebra(
        execucoes.consultar_quebra(tabelas, ini, fim, quebra), ini, fim)
    categorias = execucoes.relatorio_quebra(q, quebra)
    # total da quebra em variável própria: "soma" é o {status: total} que o
    # valor gerado usa, e sobrescrevê-la com um int derrubava o script
    total_quebra = sum(sum(b.values()) for b in q.values())
    if total_quebra != sum(totais):
        print("\nATENÇÃO: a quebra soma %d e os status somam %d — não bate."
              % (total_quebra, sum(totais)))
    return (execucoes.bloco_params_quebra(q, categorias, pct), pct, soma,
            baldes, buckets)


VALOR_LOCAL = os.path.join(RAIZ, "valor-local.json")


def config_valor(codigo):
    """O bloco do robô no valor-local.json, ou {}.

    O arquivo fica fora do git (a chave é o código do robô e os números são
    do cliente). Formato:

        {"ABC01": {"minutos_por_item": 4, "custo_hora": 55,
                   "entregas": {"<status de sucesso>": "<frase do slide>"}}}
    """
    if not os.path.exists(VALOR_LOCAL):
        return {}
    dados = json.load(io.open(VALOR_LOCAL, encoding="utf-8"))
    for k, v in dados.items():
        if not k.startswith("_") and codigo and mesmo_codigo(k, codigo):
            return v
    return {}


def milhar(n):
    return "{:,}".format(int(n)).replace(",", ".")


def valor_gerado(soma, baldes, cfg):
    """itens entregues e a lista de entregas, a partir dos status de sucesso.

    Com "entregas" no valor-local.json, contam só os status mapeados, cada um
    com a frase de negócio dele. Sem isso, entra todo status de sucesso com o
    texto cru e um REVISAR — status de sistema não é frase de diretoria.
    """
    import status as status_mod
    frases = cfg.get("entregas") or {}
    alvo = {normalizar(k): v for k, v in frases.items()}
    entregas, itens = [], 0
    for st, n in sorted(soma.items(), key=lambda x: -x[1]):
        if baldes.get(st) != status_mod.SUCESSO or not n:
            continue
        if alvo:
            frase = alvo.get(normalizar(st))
            if frase is None:
                continue
            entregas.append("**%s** %s" % (milhar(n), frase))
        else:
            entregas.append("%s**%s** %s" % (REVISAR, milhar(n), st.lower()))
        itens += n
    if alvo and not entregas:
        print("ATENÇÃO: nenhum status do valor-local.json apareceu no período.")
    return OrderedDict([
        ("itens_entregues", itens),
        ("minutos_por_item", cfg.get("minutos_por_item")),
        ("custo_hora", cfg.get("custo_hora")),
        ("entregas", entregas),
    ])


def dados_glpi(cliente, ini, fim, codigos):
    """(grafico_sla, disponibilidade, pistas de melhoria) numa sessão só.

    O SLA sai sempre com --tudo: o gráfico é volume, e volume não se filtra.
    A linha de exclusões sai junto, para o ATE e o Dashboard Sustain não
    contarem histórias diferentes sem ninguém perceber."""
    import glpi_sla
    sess = glpi_sla.abrir_sessao()
    try:
        chamados = glpi_sla.buscar_chamados(sess, cliente)
        print("chamados lidos para %r: %d\n" % (cliente, len(chamados)))
        buckets = glpi_sla.apurar(chamados, ini, fim, True)
        glpi_sla.relatorio_exclusoes(
            glpi_sla.contar_exclusoes(chamados, buckets), True)
        print()
        glpi_sla.relatorio(buckets)
        disp, pistas = None, None
        if codigos:
            print()
            d = glpi_sla.disponibilidade(chamados, ini, fim, codigos)
            glpi_sla.relatorio_disponibilidade(d, codigos)
            disp = OrderedDict((k, v) for k, v in d.items()
                               if not k.startswith("_"))
            if d["percentual"] is not None:
                disp["percentual"] = round(d["percentual"], 3)
            pistas = pistas_de_melhoria(glpi_sla, chamados, buckets, codigos)
        return glpi_sla.bloco_params(buckets), disp, pistas
    finally:
        try:
            glpi_sla._req(glpi_sla.BASE + "/killSession",
                          {"App-Token": glpi_sla.APP, "Session-Token": sess})
        except Exception:                              # noqa: BLE001
            pass


def pistas_de_melhoria(glpi_sla, chamados, buckets, codigos):
    """Quantos chamados de Melhoria e de Sustentação o robô teve no período.

    Os títulos do GLPI repetem a categoria, então não dá para tirar dali O
    QUE foi feito — o número só lembra quem escreve de onde procurar."""
    alvo = {c.upper() for c in codigos}
    cont = OrderedDict([("Melhoria", 0), ("Sustenta", 0)])
    for t in chamados:
        if glpi_sla._no_do_chamado(t).upper() not in alvo:
            continue
        ab = glpi_sla._dt(t.get(str(glpi_sla.F_ABERTURA)))
        if not ab or (ab.year, ab.month) not in buckets:
            continue
        cat = t.get(str(glpi_sla.F_CATEG)) or ""
        for k in cont:
            if k in cat:
                cont[k] += 1
    return cont


# Status que são falha de SISTEMA EXTERNO (API, portal, rede) e não do robô.
# O robô detectou, registrou e seguiu — é o "falhas de API identificadas
# automaticamente" do slide 4. Só padrões inequívocos; o resto não conta.
EXTERNO = re.compile(
    r"status code 5\d\d|\b5\d\d\b.*(error|erro)|socket hang up|econnreset|"
    r"econnrefused|etimedout|timed? ?out|tempo esgotado|indisponivel|"
    r"fora do ar|instabilidade|bad gateway|service unavailable", re.I)


def grupo_do_status(st, balde):
    """sucesso | externo | negocio | falha — a régua do volume e da prevenção.

    "externo" é falha de API/portal/rede que o robô DETECTOU e registrou; no
    balde da assertividade ela continua onde o status-local.json pôs."""
    import status as status_mod
    if balde == status_mod.SUCESSO:
        return "sucesso"
    if EXTERNO.search(normalizar(st)):
        return "externo"
    return "negocio" if balde == status_mod.NEGOCIO else "falha"


def contagem_de_prevencao(soma, baldes):
    cont = OrderedDict((g, 0) for g in ("sucesso", "externo", "negocio", "falha"))
    for st, n in soma.items():
        cont[grupo_do_status(st, baldes.get(st))] += n
    print("prevenção: externo=%d  exceção de negócio=%d  falha do robô=%d"
          % (cont["externo"], cont["negocio"], cont["falha"]))
    return cont


def bloco_prevencao(cont, sla, disp, pct):
    """Slide 'O que fizemos para evitar falhas': três destaques com número.

    Os números saem do banco e do GLPI; as frases são genéricas de propósito
    e vêm com REVISAR — quem conhece o robô troca pelo que aconteceu. Nada
    aqui fala em reprocessamento: o banco guarda só o status final, não a
    retentativa."""
    candidatos = []
    if cont["externo"]:
        candidatos.append(OrderedDict([
            ("numero", milhar(cont["externo"])),
            ("titulo", "falhas de API detectadas"),
            ("texto", REVISAR + "Erros dos sistemas externos identificados e "
                      "registrados automaticamente, sem parar a operação.")]))
    if cont["negocio"]:
        candidatos.append(OrderedDict([
            ("numero", milhar(cont["negocio"])),
            ("titulo", "casos fora da regra"),
            ("texto", REVISAR + "Itens que não atendiam à regra de negócio, "
                      "separados automaticamente antes de seguir no processo.")]))
    total = sum(sla["chamados"]) if sla else 0
    if total:
        dentro = sum(sla["dentro_do_sla"])
        candidatos.append(OrderedDict([
            ("numero", "%d de %d" % (dentro, total)),
            ("titulo", "chamados no SLA"),
            ("texto", "Chamados do trimestre resolvidos dentro do prazo "
                      "acordado.")]))
    if pct is not None:
        candidatos.append(OrderedDict([
            ("numero", ("%.1f%%" % (int(pct * 10) / 10.0)).replace(".", ",")),
            ("titulo", "de assertividade"),
            ("texto", "Execuções sem falha do robô; exceção de negócio conta "
                      "como acerto.")]))
    if not candidatos:
        return None
    return OrderedDict([
        ("destaques", candidatos[:3]),
        ("faixa", OrderedDict([
            ("titulo", "**Operação** protegida"),
            ("texto", REVISAR + "o que a equipe fez no trimestre para evitar "
                      "falhas: causas de chamado tratadas, ajustes, "
                      "monitoramento.")])),
    ])


def bloco_volume(por_mes, baldes, cfg):
    """Slide 'Volume processado': uma linha por entrega, uma coluna por mês.

    As linhas de sucesso usam a frase do valor-local.json (sem número na
    frente — o número está nas colunas); depois vêm os casos barrados, as
    falhas externas detectadas e o total."""
    if not por_mes:
        return None
    meses = list(por_mes.keys())
    frases = {normalizar(k): v for k, v in (cfg.get("entregas") or {}).items()}

    def linha(rotulo, filtro, destaque=False):
        vals = [sum(n for st, n in por_mes[m].items() if filtro(st))
                for m in meses]
        d = OrderedDict([("rotulo", rotulo), ("valores", vals + [sum(vals)])])
        if destaque:
            d["destaque"] = True
        return d

    linhas = []
    todos = OrderedDict()
    for m in meses:
        for st, n in por_mes[m].items():
            todos[st] = todos.get(st, 0) + n
    for st, n in sorted(todos.items(), key=lambda x: -x[1]):
        if grupo_do_status(st, baldes.get(st)) != "sucesso" or not n:
            continue
        if frases and normalizar(st) not in frases:
            continue
        rotulo = frases.get(normalizar(st)) or REVISAR + st.lower()
        linhas.append(linha(rotulo[:1].upper() + rotulo[1:],
                            lambda x, st=st: x == st))
    for grupo, rotulo in (("negocio", "Casos fora da regra, separados automaticamente"),
                          ("externo", "Falhas de API detectadas e registradas"),
                          ("falha", "Falhas do robô")):
        l = linha(rotulo, lambda x, g=grupo: grupo_do_status(x, baldes.get(x)) == g)
        if l["valores"][-1]:
            linhas.append(l)
    linhas.append(linha("**Total processado**", lambda x: True, True))
    return OrderedDict([
        ("colunas", [MESES_NOME[m[1] - 1] for m in meses] + ["Trimestre"]),
        ("linhas", linhas),
    ])


# ------------------------------------------------------------------- vault
def notas_de_robo(raizes):
    """Todo .md do vault com 'tipo: robo' no frontmatter."""
    notas = []
    for raiz in raizes:
        for pasta, _, arquivos in os.walk(raiz):
            if os.path.basename(pasta).startswith("."):
                continue
            for nome in arquivos:
                if not nome.lower().endswith(".md"):
                    continue
                try:
                    texto = io.open(os.path.join(pasta, nome),
                                    encoding="utf-8").read()
                except (OSError, UnicodeDecodeError):
                    continue
                fm = frontmatter(texto)
                if fm.get("tipo") == "robo" and fm.get("segmento_projeto"):
                    fm["_texto"] = texto
                    notas.append(fm)
    return notas


def tabelas_da_nota(texto):
    """A lista 'tabelas:' do frontmatter (o frontmatter() é raso e pula
    listas, então esta lê os itens '  - x' logo abaixo da chave)."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", texto, re.S)
    if not m:
        return []
    bloco = re.search(r"^tabelas:\s*\n((?:[ \t]+-[^\n]*\n?)+)", m.group(1), re.M)
    if not bloco:
        return []
    return [i.strip().strip('"').strip("'") for i in
            re.findall(r"^[ \t]+-\s*(.+)$", bloco.group(1), re.M)]


def codigo_pelas_tabelas(notas, cliente, tabelas):
    """Códigos de robô cujas notas listam a tabela da planilha — igual ou
    com o mesmo prefixo (a planilha traz 'yank_000123', a nota traz
    'yank_000123_filtros'). Só notas do mesmo cliente."""
    meu = chave_cliente(cliente)
    # nome de tabela não passa pelo normalizar(): ele troca "_" por espaço
    alvos = [t.strip().lower() for t in tabelas if t]
    achados = []
    for n in notas:
        if not n.get("codigo") or chave_cliente(n.get("cliente", "")) != meu:
            continue
        for t in tabelas_da_nota(n["_texto"]):
            t = t.strip().lower()
            if any(t == a or t.startswith(a + "_") for a in alvos):
                if n["codigo"] not in achados:
                    achados.append(n["codigo"])
                break
    return achados


def chave_cliente(nome):
    """Primeira palavra do nome: "Fulano (cliente final X)" e "Fulano" são o
    mesmo cliente para efeito de 'não mostrar o que ele já tem'."""
    p = normalizar(nome).split()
    return p[0] if p else ""


def automacoes_do_segmento(notas, cliente, codigo, limite=6):
    """Automações da mesma área (o que vem antes do " - " no
    segmento_projeto) em OUTROS clientes, que este cliente ainda não tem.

    Sai só o assunto e em quantos clientes roda — nunca o nome do cliente:
    o slide vai para fora e a carteira dos outros não é assunto dele."""
    proprio = [n for n in notas if codigo and n.get("codigo")
               and mesmo_codigo(n["codigo"], codigo)]
    if not proprio:
        return None, "nenhuma nota de robô com código %r no vault" % codigo
    area = proprio[0]["segmento_projeto"].split(" - ")[0].strip()
    meu = chave_cliente(cliente)
    ja_tem = {normalizar(n["segmento_projeto"]) for n in notas
              if chave_cliente(n.get("cliente", "")) == meu}
    por_assunto = OrderedDict()
    for n in notas:
        seg = n["segmento_projeto"]
        if seg.split(" - ")[0].strip() != area or " - " not in seg:
            continue
        outro = chave_cliente(n.get("cliente", ""))
        if not outro or outro == meu or "confirmar" in normalizar(n.get("cliente", "")):
            continue
        if normalizar(seg) in ja_tem:
            continue
        assunto = seg.split(" - ", 1)[1].strip()
        por_assunto.setdefault(assunto, set()).add(outro)
    ranking = sorted(por_assunto.items(), key=lambda x: (-len(x[1]), x[0]))
    itens = ["**%s** — em operação em %d cliente%s do segmento"
             % (a[:1].upper() + a[1:], len(c), "s" if len(c) > 1 else "")
             for a, c in ranking[:limite]]
    return itens, "área %r, %d assunto(s) em outros clientes" % (area, len(ranking))


# ---------------------------------------------------------------- programa
def opcao(nome, padrao=None):
    if nome in sys.argv:
        i = sys.argv.index(nome)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        sys.exit("erro: %s precisa de um valor." % nome)
    return padrao


def main():
    sem_banco = "--sem-banco" in sys.argv
    robo_pedido = opcao("--robo")
    competencia = opcao("--competencia")
    vault = opcao("--vault")
    planilha = opcao("--planilha")
    saida = opcao("--saida", os.path.join(RAIZ, "params.json"))

    com_valor = ("--robo", "--competencia", "--vault", "--planilha", "--saida")
    livres, pulando = [], False
    for a in sys.argv[1:]:
        if pulando:
            pulando = False
            continue
        if a in com_valor:
            pulando = True
        elif not a.startswith("--"):
            livres.append(a)
    if len(livres) < 3:
        sys.exit(__doc__.split("\n\n")[1].strip())
    cliente_pedido, ini, fim = livres[0], livres[1], livres[2]

    meses = rotulo_meses(ini, fim)
    competencia = competencia or meses[-1]

    print("=" * 68)
    print("PLANILHA")
    print("=" * 68)
    planilha = achar_planilha(planilha)
    print("arquivo: %s" % planilha)
    cliente, robos = resolver_robos(planilha, cliente_pedido)
    robo = escolher_robo(robos, robo_pedido)
    if len(robo["tabelas"]) > 1 and not robo["somavel"]:
        print("ATENÇÃO: %d tabelas neste robô e a OBS não diz 'pode somar'.\n"
              "         Confira as linhas %s antes de aceitar a soma."
              % (len(robo["tabelas"]),
                 ", ".join(str(n) for n in robo["linhas"])))
    print("cliente: %s" % cliente)
    print("robô:    %s" % (robo["codigo"] or robo["descricao"] or "(único)"))
    print("linha%s:  %s" % ("s" if len(robo["linhas"]) > 1 else " ",
                            ", ".join(str(n) for n in robo["linhas"])))
    print("tabela%s: %s" % ("s" if len(robo["tabelas"]) > 1 else " ",
                            ", ".join(robo["tabelas"])))
    print("quebra:  %s" % (robo["quebra"] or "não"))
    if robo["obs"]:
        print("OBS:     %s" % robo["obs"])

    print()
    print("=" * 68)
    print("DOSSIÊ")
    print("=" * 68)
    dossies = achar_dossies(achar_vault(vault))
    print("dossiês encontrados no vault: %d" % len(dossies))
    notas = notas_de_robo(achar_vault(vault))
    if not robo["codigo"]:
        # OBS sem código: o vault diz de quem é a tabela. Só vale se UM
        # código casar — dois seriam dois robôs, e aí quem escolhe é gente.
        codigos_vault = codigo_pelas_tabelas(notas, cliente, robo["tabelas"])
        if len(codigos_vault) == 1:
            robo["codigo"] = codigos_vault[0]
            print("código:  %s (a OBS não tem código; achado pelas tabelas "
                  "da nota do robô no vault)" % robo["codigo"])
        elif codigos_vault:
            print("ATENÇÃO: as tabelas casam com mais de uma nota de robô: %s.\n"
                  "         Repita com --robo <código> para escolher."
                  % ", ".join(codigos_vault))
    dossie = casar_dossie(dossies, cliente)
    resumo = objetivo = None
    if dossie is None:
        origem = ("nenhum dossiê com cliente %r. Passe os dois textos à mão."
                  % cliente)
    else:
        resumo, objetivo, origem = textos_do_dossie(dossie, robo)
    if not objetivo and robo["codigo"]:
        # Sem dossiê do cliente, o objetivo sai da nota do próprio robô.
        nota = next((n for n in notas if n.get("codigo")
                     and mesmo_codigo(n["codigo"], robo["codigo"])), None)
        if nota:
            objetivo = limpar(secao(nota["_texto"], 3, "Objetivo"))
            origem += "\n         escopo pela nota do robô %s" % nota["codigo"]
    print("origem:  %s" % origem)
    if objetivo:
        curto = encurtar_objetivo(objetivo)
        print()
        print("--- escopo, original (%d caracteres) ---" % len(objetivo))
        print(objetivo)
        print()
        print("--- escopo, sem a enumeração de etapas (%d caracteres) ---"
              % len(curto))
        print(curto)
        print("    a régua são ~200 caracteres, numa faixa do slide 2. %s"
              % ("cabe." if len(curto) <= 200 else
                 "AINDA PRECISA CONDENSAR — resumir, não truncar."))
    else:
        curto = None

    bloco_exec, pct, bloco_sla = None, None, None
    soma, baldes, disp, pistas, por_mes = {}, {}, None, None, None
    codigos = [robo["codigo"]] if robo["codigo"] else []
    if not sem_banco:
        print()
        print("=" * 68)
        print("EXECUÇÕES (banco)")
        print("=" * 68)
        bloco_exec, pct, soma, baldes, por_mes = dados_execucoes(
            robo["tabelas"], ini, fim, robo["quebra"], etiqueta_do_robo(robo))
        print()
        print("=" * 68)
        print("CHAMADOS (GLPI, com --tudo)")
        print("=" * 68)
        bloco_sla, disp, pistas = dados_glpi(cliente, ini, fim, codigos)

    print()
    print("=" * 68)
    print("SEGMENTO (vault)")
    print("=" * 68)
    segmento, origem_seg = automacoes_do_segmento(notas, cliente, robo["codigo"])
    print("origem:  %s" % origem_seg)
    for item in segmento or []:
        print("  - %s" % item.replace("**", ""))

    params = OrderedDict()
    params["cliente"] = cliente
    params["competencia"] = competencia
    params["escopo"] = ((REVISAR + "condensar para ~200 caracteres. ") + curto
                        if curto else REVISAR + "objetivo do robô, do dossiê")
    params["grafico_execucoes"] = bloco_exec or OrderedDict([
        ("titulo", "Execuções - %s" % ", ".join(meses)),
        ("meses", meses),
        ("execucoes", [0] * len(meses)),
    ])
    # número, não frase: o gerar.py formata o cartão (com piso, 99,96 -> 99,9)
    params["grafico_execucoes"]["assertividade"] = (
        round(pct, 2) if pct is not None else None)
    params["grafico_sla"] = bloco_sla or OrderedDict([
        ("meses", meses),
        ("chamados", [0] * len(meses)),
        ("dentro_do_sla", [0] * len(meses)),
    ])

    cfg_valor = config_valor(robo["codigo"])
    params["valor_gerado"] = valor_gerado(soma, baldes, cfg_valor)
    if not cfg_valor:
        print("\nsem bloco de %r no valor-local.json: entregas com o texto "
              "do status e horas/economia 'a confirmar'." % robo["codigo"])
    params["disponibilidade"] = disp
    if por_mes:
        cont = contagem_de_prevencao(soma, baldes)
        params["volume_processado"] = bloco_volume(por_mes, baldes, cfg_valor)
        params["prevencao"] = bloco_prevencao(cont, bloco_sla, disp, pct)

    pista = ("o GLPI tem %d chamado(s) de Melhoria e %d de Sustentação deste "
             "robô no trimestre" % (pistas["Melhoria"], pistas["Sustenta"])
             if pistas else "confira os chamados de Melhoria do robô no GLPI")
    params["melhorias"] = OrderedDict([
        ("esquerda", [OrderedDict([
            ("topico", REVISAR + "o que foi entregue no robô"),
            ("itens", [REVISAR + pista])])]),
        ("direita", [OrderedDict([
            ("topico", REVISAR + "o que fizemos para evitar falhas"),
            ("itens", [REVISAR + "ajustes, prevenções, causas de chamado "
                                 "tratadas"])])]),
    ])
    params["proximas_evolucoes"] = OrderedDict([
        ("esquerda", [OrderedDict([
            ("topico", REVISAR + "próximas evoluções do robô"),
            ("itens", [REVISAR + "escreva na mensagem do pedido"])])]),
        ("direita", [OrderedDict([
            ("topico", REVISAR + "Oportunidades no segmento"),
            ("itens", segmento or [REVISAR + origem_seg])])]),
    ])

    with io.open(saida, "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)
        f.write("\n")

    pendentes = [k for k, v in params.items()
                 if REVISAR in json.dumps(v, ensure_ascii=False)]
    print()
    print("=" * 68)
    print("escrito: %s" % saida)
    if sem_banco:
        print("(--sem-banco: gráficos zerados, sem entregas nem "
              "disponibilidade, de propósito)")
    print("ainda com REVISAR: %s" % (", ".join(pendentes) or "nada"))
    print()
    print("depois de revisar:")
    print("    python gerar.py %s ATE-%s-%s.pptx --conferir"
          % (os.path.basename(saida), cliente.split()[0],
             competencia.replace("/", "")))


if __name__ == "__main__":
    main()
