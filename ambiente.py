# -*- coding: utf-8 -*-
"""Lê o .env local (se existir) para dentro de os.environ.

Sem dependência externa: um .env aqui é só LINHA=valor, com # de comentário.
Variáveis já definidas no ambiente têm prioridade sobre o arquivo, para dar
para sobrescrever pontualmente sem editar o .env.
"""
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))


def carregar(caminho=None):
    caminho = caminho or os.path.join(RAIZ, ".env")
    if not os.path.exists(caminho):
        return {}
    lidas = {}
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            chave, valor = chave.strip(), valor.strip().strip('"').strip("'")
            lidas[chave] = valor
            os.environ.setdefault(chave, valor)
    return lidas


def exigir(*chaves):
    """Devolve os valores, ou aborta dizendo o que falta preencher."""
    carregar()
    faltando = [c for c in chaves if not os.environ.get(c)]
    if faltando:
        raise SystemExit(
            "faltam variáveis: %s\n"
            "Preencha o .env (copie de .env.exemplo) ou defina no ambiente."
            % ", ".join(faltando))
    return [os.environ[c] for c in chaves]
