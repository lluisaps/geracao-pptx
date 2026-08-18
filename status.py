# -*- coding: utf-8 -*-
"""Classifica cada status_execucao em sucesso / exceção de negócio / falha do
robô — a única fonte da assertividade do ATE.

    assertividade = (total − falha do robô) / total

Exceção de negócio conta como ACERTO: quando o robô recusa uma nota porque o
depositante não está cadastrado, ele fez exatamente o que devia. Punir a
automação por cadastro faltando no cliente é o que derrubava o número.

Três fontes, nesta ordem de precedência:

  1. status-local.json — onde as classificações realmente moram. Está no
     .gitignore: a chave do bloco é o CÓDIGO DO ROBÔ, que é dado de cliente e
     não entra no repositório. É este arquivo que cada máquina precisa ter.
  2. status.json — versionado, mas vazio de propósito, só com a nota de
     formato. Existe para documentar o esquema e para receber, se um dia
     houver, classificação que não seja identificável por cliente.
  3. PADROES, aqui embaixo — regras genéricas para o que se repete entre
     clientes.

O mapa é chaveado pelo texto do status, sem separar por robô: cada robô tem o
seu próprio vocabulário de mensagens, então as frases não colidem. Se um dia
dois robôs usarem a mesma frase com sentidos diferentes, é aí que vira
necessário separar por robô.

Status que não casa com nenhuma das três NÃO é chutado: quem chama recebe a
lista e para. É isso que faz a mesma base gerar o mesmo número em qualquer
máquina — a classificação deixa de ser julgamento de quem está rodando.
"""
import json
import io
import os
import re
import unicodedata
from collections import OrderedDict

SUCESSO = "sucesso"
NEGOCIO = "excecao_negocio"
FALHA = "falha_robo"
BALDES = (SUCESSO, NEGOCIO, FALHA)

RAIZ = os.path.dirname(os.path.abspath(__file__))
VERSIONADO = os.path.join(RAIZ, "status.json")
LOCAL = os.path.join(RAIZ, "status-local.json")

# Só padrões de alta confiança. Na dúvida NÃO se inventa regra genérica: o
# status cai como desconhecido e vai para o status-local.json, onde a decisão
# fica registrada por escrito em vez de virar chute do script.
PADROES = [
    (r"com sucesso", SUCESSO),
    (r"\bsucesso\b", SUCESSO),

    (r"erro desconhecido", FALHA),
    (r"desconhecido ao efetuar", FALHA),

    (r"nao cadastrad", NEGOCIO),
    (r"nao ha registros", NEGOCIO),
    (r"ja (foi )?processad", NEGOCIO),
]


def normalizar(texto):
    """Sem acento, sem caixa, sem espaço sobrando."""
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", texto or "")
                         if unicodedata.category(c) != "Mn")
    return " ".join(sem_acento.lower().split())


def _ler(caminho):
    """{robô: {status normalizado: balde}} de um dos arquivos, ou {}."""
    if not os.path.exists(caminho):
        return {}
    nome = os.path.basename(caminho)
    with io.open(caminho, encoding="utf-8") as f:
        try:
            bruto = json.load(f)
        except ValueError as e:
            raise SystemExit("o %s não é JSON válido: %s" % (nome, e))

    mapa = {}
    for robo, statuses in bruto.items():
        if robo.startswith("_"):       # JSON não tem comentário: "_nota" serve
            continue
        if not isinstance(statuses, dict):
            raise SystemExit(
                "no %s, %r devia ser um bloco de robô com os status dentro.\n"
                "      O formato é {\"<robô>\": {\"<status>\": \"<balde>\"}}."
                % (nome, robo))
        interno = {}
        for st, balde in statuses.items():
            if st.startswith("_"):
                continue
            if balde not in BALDES:
                raise SystemExit(
                    "no %s, o status %r do robô %r está marcado como %r.\n"
                    "      Os baldes válidos são: %s."
                    % (nome, st, robo, balde, ", ".join(BALDES)))
            interno[normalizar(st)] = balde
        mapa[normalizar(robo)] = interno
    return mapa


def carregar(robo):
    """As duas camadas de mapa exato para ESTE robô: (local, versionado)."""
    chave = normalizar(robo or "")
    return (_ler(LOCAL).get(chave, {}), _ler(VERSIONADO).get(chave, {}))


def classificar(status, camadas=None, robo=None):
    """O balde do status, ou None se ninguém souber dizer."""
    n = normalizar(status)
    local, versionado = carregar(robo) if camadas is None else camadas
    if n in local:                      # a válvula de escape manda
        return local[n]
    if n in versionado:                 # depois a decisão versionada
        return versionado[n]
    for padrao, balde in PADROES:       # por último o que vale para todos
        if re.search(padrao, n):
            return balde
    return None


def classificar_todos(status, robo=None):
    """({status: balde}, [status sem classificação])."""
    camadas = carregar(robo)
    baldes, desconhecidos = OrderedDict(), []
    for s in status:
        b = classificar(s, camadas, robo)
        if b is None:
            desconhecidos.append(s)
        else:
            baldes[s] = b
    return baldes, desconhecidos


def texto_desconhecidos(desconhecidos, quantidades=None, robo=None):
    """A mensagem de parada, já com o JSON pronto para colar."""
    rotulo = robo or "<robô>"
    modelo = OrderedDict([
        (rotulo, OrderedDict((s, "excecao_negocio") for s in desconhecidos))])
    linhas = [
        "%d status sem classificação — a assertividade não sai assim."
        % len(desconhecidos),
        "",
        "      Cada um precisa virar sucesso, excecao_negocio ou falha_robo.",
        "      Lembre da régua: falha_robo é só quando o ROBÔ errou. Dado que",
        "      falta no cliente, portal fora do ar e regra de negócio que",
        "      barrou o caso são excecao_negocio — contam como acerto.",
        "",
        "      Classifique no bloco %r do %s (versionado — vai para o repo,"
        % (rotulo, os.path.basename(VERSIONADO)),
        "      é o que faz todo mundo chegar no mesmo número):",
        "",
    ]
    for s in desconhecidos:
        n = quantidades.get(s, 0) if quantidades else 0
        linhas.append("        %-7d %s" % (n, s))
    linhas += ["", "      Modelo para colar (troque o balde onde precisar):", ""]
    linhas.append(json.dumps(modelo, ensure_ascii=False, indent=2))
    return "\n".join(linhas)


def apurar(soma_status, robo=None):
    """(pct, {balde: total}) pela convenção do ATE.

    Levanta SystemExit se algum status não estiver classificado.
    """
    baldes, desconhecidos = classificar_todos(soma_status.keys(), robo)
    if desconhecidos:
        raise SystemExit(texto_desconhecidos(desconhecidos, soma_status, robo))
    totais = OrderedDict((b, 0) for b in BALDES)
    for s, n in soma_status.items():
        totais[baldes[s]] += n
    geral = sum(totais.values())
    pct = (geral - totais[FALHA]) / geral * 100.0 if geral else None
    return pct, totais, baldes
