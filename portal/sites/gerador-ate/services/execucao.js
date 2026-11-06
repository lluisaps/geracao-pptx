const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const cfg = require('../config');

/**
 * Pasta de trabalho de cada conversa: params.json, .pptx e os PNGs de
 * conferência que o agente gera. O id da pasta é o id da conversa (e da
 * sessão do Claude Code), sempre um UUID — nada vindo da URL vira caminho
 * sem passar pelo padrão.
 */

const RE_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const RE_SLIDE = /^(Slide\d{1,2}\.PNG|slide-\d{1,2}\.jpg)$/i;

class ErroDeEntrada extends Error {}

function verificarRepositorio() {
    if (!cfg.repositorio) {
        throw new ErroDeEntrada('GERADOR_ATE_DIR não está definida: o portal não sabe onde está o geracao-pptx.');
    }
    for (const arq of ['montar.py', 'gerar.py', 'CLAUDE.md']) {
        if (!fs.existsSync(path.join(cfg.repositorio, arq))) {
            throw new ErroDeEntrada(`${arq} não encontrado em GERADOR_ATE_DIR (${cfg.repositorio}).`);
        }
    }
}

function limparAntigos() {
    if (!fs.existsSync(cfg.pastaTrabalhos)) return;
    const agora = Date.now();
    for (const nome of fs.readdirSync(cfg.pastaTrabalhos)) {
        if (!RE_ID.test(nome)) continue;
        const p = path.join(cfg.pastaTrabalhos, nome);
        try {
            if (agora - fs.statSync(p).mtimeMs > cfg.validadeTrabalhoMs) {
                fs.rmSync(p, { recursive: true, force: true });
            }
        } catch (_) { /* outro pedido apagou antes */ }
    }
}

function novoTrabalho() {
    limparAntigos();
    const id = crypto.randomUUID();
    fs.mkdirSync(path.join(cfg.pastaTrabalhos, id), { recursive: true });
    return id;
}

function pastaDo(id) {
    if (!RE_ID.test(String(id))) throw new ErroDeEntrada('Conversa inválida.');
    const pasta = path.join(cfg.pastaTrabalhos, id);
    if (!fs.existsSync(pasta)) {
        throw new ErroDeEntrada('Conversa não encontrada (expirou?). Comece uma nova.');
    }
    return pasta;
}

function listarSlides(pasta) {
    const conf = path.join(pasta, 'conferencia');
    if (!fs.existsSync(conf)) return [];
    const num = (n) => parseInt((n.match(/\d+/) || ['0'])[0], 10);
    return fs.readdirSync(conf).filter((n) => RE_SLIDE.test(n)).sort((a, b) => num(a) - num(b));
}

/** O .pptx mais recente da conversa, ou null. */
function pptxAtual(pasta) {
    const lista = fs.readdirSync(pasta).filter((n) => /^ATE-.*\.pptx$/i.test(n))
        .map((n) => ({ n, t: fs.statSync(path.join(pasta, n)).mtimeMs }))
        .sort((a, b) => b.t - a.t);
    return lista.length ? lista[0].n : null;
}

/** Retrato do que a conversa já produziu, para a tela. */
function estado(id) {
    const pasta = pastaDo(id);
    const arquivo = pptxAtual(pasta);
    return {
        arquivo,
        versao: arquivo ? Math.round(fs.statSync(path.join(pasta, arquivo)).mtimeMs) : 0,
        slides: listarSlides(pasta)
    };
}

function caminhoSlide(id, arquivo) {
    if (!RE_SLIDE.test(String(arquivo))) throw new ErroDeEntrada('Slide inválido.');
    const p = path.join(pastaDo(id), 'conferencia', arquivo);
    if (!fs.existsSync(p)) throw new ErroDeEntrada('Slide não encontrado.');
    return p;
}

function caminhoPptx(id) {
    const pasta = pastaDo(id);
    const nome = pptxAtual(pasta);
    if (!nome) throw new ErroDeEntrada('Ainda não há .pptx nesta conversa.');
    return { caminho: path.join(pasta, nome), nome };
}

module.exports = {
    ErroDeEntrada, verificarRepositorio, novoTrabalho, pastaDo, estado,
    caminhoSlide, caminhoPptx
};
