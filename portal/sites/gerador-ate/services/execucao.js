const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execFile } = require('child_process');
const cfg = require('../config');

/**
 * Ponte entre o portal e o repositório geracao-pptx.
 *
 * Cada pedido vira um "trabalho": uma pasta própria com o params.json, o
 * .pptx e os PNGs de conferência. Assim duas pessoas gerando ao mesmo tempo
 * não pisam uma na outra, e o params.json "de verdade" do repositório nunca é
 * tocado pelo portal.
 *
 * Python roda por execFile, SEM shell, com argumentos validados — nada do
 * formulário vira linha de comando interpretada.
 */

const RE_MES = /^\d{4}-(0[1-9]|1[0-2])$/;
const RE_ROBO = /^[A-Za-z0-9]{1,8}(,[A-Za-z0-9]{1,8}){0,4}$/;
const RE_COMPETENCIA = /^[A-Z][a-z]{2}\/\d{2}$/;
const RE_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const RE_SLIDE = /^(Slide\d{1,2}\.PNG|slide-\d{1,2}\.jpg)$/i;

class ErroDeEntrada extends Error {}

function verificarRepositorio() {
    if (!cfg.repositorio) {
        throw new ErroDeEntrada('GERADOR_ATE_DIR não está definida: o portal não sabe onde está o geracao-pptx.');
    }
    for (const arq of ['montar.py', 'gerar.py', 'template.pptx']) {
        if (!fs.existsSync(path.join(cfg.repositorio, arq))) {
            throw new ErroDeEntrada(`${arq} não encontrado em GERADOR_ATE_DIR (${cfg.repositorio}).`);
        }
    }
}

function validarPedido(corpo) {
    const cliente = String(corpo.cliente || '').trim();
    const ini = String(corpo.ini || '').trim();
    const fim = String(corpo.fim || '').trim();
    const robo = String(corpo.robo || '').trim();
    const competencia = String(corpo.competencia || '').trim();

    if (!cliente || cliente.length > 80 || /[\u0000-\u001f]/.test(cliente)) {
        throw new ErroDeEntrada('Cliente inválido: até 80 caracteres, sem quebra de linha.');
    }
    if (!RE_MES.test(ini) || !RE_MES.test(fim)) {
        throw new ErroDeEntrada('Meses no formato AAAA-MM.');
    }
    if (ini > fim) {
        throw new ErroDeEntrada('O 1º mês vem antes do 3º.');
    }
    if (robo && !RE_ROBO.test(robo)) {
        throw new ErroDeEntrada('Robô: código (ABC01), número da linha ou linhas separadas por vírgula.');
    }
    if (competencia && !RE_COMPETENCIA.test(competencia)) {
        throw new ErroDeEntrada('Competência no formato Mmm/AA (ex.: Jun/26).');
    }
    return { cliente, ini, fim, robo, competencia };
}

function pastaDo(id) {
    if (!RE_ID.test(String(id))) {
        throw new ErroDeEntrada('Trabalho inválido.');
    }
    const pasta = path.join(cfg.pastaTrabalhos, id);
    if (!fs.existsSync(pasta)) {
        throw new ErroDeEntrada('Trabalho não encontrado (expirou?). Busque os dados de novo.');
    }
    return pasta;
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

function rodarPython(script, args, timeout) {
    return new Promise((resolve) => {
        execFile(cfg.python, ['-X', 'utf8', script, ...args], {
            cwd: cfg.repositorio,
            env: Object.assign({}, process.env, { PYTHONIOENCODING: 'utf-8' }),
            timeout,
            maxBuffer: 20 * 1024 * 1024,
            windowsHide: true
        }, (err, stdout, stderr) => {
            const saida = `${stdout || ''}${stderr ? '\n' + stderr : ''}`;
            if (err && err.killed) {
                return resolve({ codigo: -1, saida: saida + '\n[tempo esgotado]' });
            }
            const codigo = err ? (typeof err.code === 'number' ? err.code : 1) : 0;
            resolve({ codigo, saida });
        });
    });
}

function contarRevisar(params) {
    return (JSON.stringify(params).match(/REVISAR/g) || []).length;
}

async function montar(corpo) {
    verificarRepositorio();
    const pedido = validarPedido(corpo);
    const id = novoTrabalho();
    const arqParams = path.join(cfg.pastaTrabalhos, id, 'params.json');

    const args = [pedido.cliente, pedido.ini, pedido.fim, '--saida', arqParams];
    if (pedido.robo) args.push('--robo', pedido.robo);
    if (pedido.competencia) args.push('--competencia', pedido.competencia);

    const r = await rodarPython('montar.py', args, cfg.timeoutMontarMs);
    let params = null;
    if (fs.existsSync(arqParams)) {
        params = JSON.parse(fs.readFileSync(arqParams, 'utf-8'));
    }
    return {
        id,
        codigo: r.codigo,
        log: r.saida,
        // exit 2 = o cliente tem mais de um robô; o log traz as opções
        escolherRobo: r.codigo === 2,
        params,
        revisar: params ? contarRevisar(params) : null
    };
}

const CAMPOS_OBRIGATORIOS = ['cliente', 'competencia', 'escopo', 'grafico_execucoes',
    'grafico_sla', 'melhorias', 'proximas_evolucoes'];

function salvarParams(id, params) {
    const pasta = pastaDo(id);
    if (!params || typeof params !== 'object' || Array.isArray(params)) {
        throw new ErroDeEntrada('params precisa ser um objeto JSON.');
    }
    const faltando = CAMPOS_OBRIGATORIOS.filter((c) => !(c in params));
    if (faltando.length) {
        throw new ErroDeEntrada('Faltam campos no params: ' + faltando.join(', '));
    }
    const texto = JSON.stringify(params, null, 2);
    if (Buffer.byteLength(texto) > cfg.limiteParamsBytes) {
        throw new ErroDeEntrada('params grande demais.');
    }
    fs.writeFileSync(path.join(pasta, 'params.json'), texto + '\n', 'utf-8');
    return { revisar: contarRevisar(params) };
}

function nomeDoArquivo(params) {
    const limpo = (t) => String(t || '').normalize('NFD').replace(/[̀-ͯ]/g, '')
        .replace(/[^A-Za-z0-9]+/g, '-').replace(/^-|-$/g, '');
    const cliente = limpo(String(params.cliente || 'cliente').split(/\s+/)[0]) || 'cliente';
    // Jun/26 -> Jun26, como os ATEs gerados à mão
    const comp = limpo(String(params.competencia || '').replace(/\//g, ''));
    return `ATE-${cliente}-${comp || 'competencia'}.pptx`;
}

async function gerar(id) {
    verificarRepositorio();
    const pasta = pastaDo(id);
    const arqParams = path.join(pasta, 'params.json');
    const params = JSON.parse(fs.readFileSync(arqParams, 'utf-8'));
    const pendentes = contarRevisar(params);
    if (pendentes) {
        throw new ErroDeEntrada(`Ainda há ${pendentes} REVISAR no params — revise antes de gerar.`);
    }
    const nome = nomeDoArquivo(params);
    const saida = path.join(pasta, nome);
    const conf = path.join(pasta, 'conferencia');
    const r = await rodarPython('gerar.py', [arqParams, saida, '--conferencia', conf],
        cfg.timeoutGerarMs);
    return {
        codigo: r.codigo,
        log: r.saida,
        arquivo: fs.existsSync(saida) ? nome : null,
        slides: listarSlides(pasta)
    };
}

function listarSlides(pasta) {
    const conf = path.join(pasta, 'conferencia');
    if (!fs.existsSync(conf)) return [];
    const num = (n) => parseInt((n.match(/\d+/) || ['0'])[0], 10);
    return fs.readdirSync(conf).filter((n) => RE_SLIDE.test(n)).sort((a, b) => num(a) - num(b));
}

function caminhoSlide(id, arquivo) {
    if (!RE_SLIDE.test(String(arquivo))) throw new ErroDeEntrada('Slide inválido.');
    const p = path.join(pastaDo(id), 'conferencia', arquivo);
    if (!fs.existsSync(p)) throw new ErroDeEntrada('Slide não encontrado.');
    return p;
}

function caminhoPptx(id) {
    const pasta = pastaDo(id);
    const nome = fs.readdirSync(pasta).find((n) => /^ATE-.*\.pptx$/.test(n));
    if (!nome) throw new ErroDeEntrada('Ainda não há .pptx neste trabalho.');
    return { caminho: path.join(pasta, nome), nome };
}

module.exports = {
    ErroDeEntrada, montar, salvarParams, gerar, caminhoSlide, caminhoPptx,
    validarPedido, nomeDoArquivo, contarRevisar
};
