const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const cfg = require('../config');
const ex = require('./execucao');

/**
 * O agente do chat é o Claude Code em modo sem tela (-p), rodando dentro do
 * repositório geracao-pptx. Assim:
 *
 *  - usa o login/assinatura de quem instalou o Claude Code — sem chave de
 *    API e sem cobrança à parte;
 *  - lê o CLAUDE.md e a base conhecimento/ sozinho (é o mesmo agente que
 *    roda no terminal);
 *  - cada conversa é uma sessão do Claude Code (--session-id na 1ª mensagem,
 *    --resume nas seguintes), então ele lembra do que já foi dito.
 *
 * As ferramentas vão travadas por lista: ler arquivos, rodar só os scripts
 * do gerador (que consultam banco e GLPI em leitura), editar arquivos de
 * dados. Código, base de conhecimento, .env e template ficam protegidos, e
 * git/rede não entram. Em modo -p, ferramenta fora da lista é negada sem
 * perguntar.
 */

const SCRIPTS = ['montar.py', 'gerar.py', 'execucoes.py', 'glpi_sla.py', 'probe.py'];

const PERMITIDAS = ['Read', 'Glob', 'Grep', 'Edit', 'Write',
    ...SCRIPTS.map((s) => `Bash(python ${s}:*)`)];

const PROIBIDAS = ['WebFetch', 'WebSearch', 'Bash(git:*)', 'Bash(curl:*)', 'Bash(rm:*)',
    'Edit(**/*.py)', 'Write(**/*.py)', 'Edit(**/*.md)', 'Write(**/*.md)',
    'Edit(**/.env*)', 'Write(**/.env*)', 'Edit(**/*.pptx)', 'Write(**/*.pptx)',
    'Edit(**/*.xlsx)', 'Write(**/*.xlsx)'];

function vaultPadrao() {
    if (cfg.vault) return cfg.vault;
    try {
        const reg = path.join(process.env.APPDATA || '', 'obsidian', 'obsidian.json');
        const vaults = Object.values(JSON.parse(fs.readFileSync(reg, 'utf-8')).vaults || {});
        const v = vaults.find((x) => x.open) || vaults[0];
        return v ? v.path : '';
    } catch (_) {
        return '';
    }
}

function instrucoesDoChat(pasta) {
    const p = pasta.replace(/\\/g, '/');
    return `
VOCÊ ESTÁ NA TELA DE CHAT DO PORTAL (Gerador de ATE), não no terminal.

- Quem fala com você é a gestora de contas. Responda em português, curto,
  como num chat. Mostre o que o CLAUDE.md manda mostrar antes de gerar, em
  forma de lista enxuta — sem despejar o relatório inteiro do montar.py.
- Pasta desta conversa: ${p}
  * buscar dados:  python montar.py "<cliente>" <AAAA-MM> <AAAA-MM> [--robo X] --saida "${p}/params.json"
  * edite SÓ o ${p}/params.json (e, com aprovação explícita da gestora nesta
    conversa, o valor-local.json ou o status-local.json do repositório)
  * gerar:  python gerar.py "${p}/params.json" "${p}/ATE-<cliente>-<competência sem barra>.pptx" --conferencia "${p}/conferencia"
  Escreva os comandos exatamente assim, começando por "python <script>.py":
  outra forma é bloqueada. Não crie scripts auxiliares: altere o params.json
  com a ferramenta Edit.
- NÃO rode git nesta tela (nem fetch/pull): o repositório é atualizado por
  quem mantém o portal. Ignore o passo de git do CLAUDE.md aqui.
- Depois de gerar, diga quantos slides saíram e quais opcionais ficaram de
  fora; a tela mostra as miniaturas e o botão de baixar sozinha. Confira os
  PNGs da pasta conferencia (Read) para ver se algum texto estourou.
- Se faltar dado (tempo manual, custo/hora, textos dos slides 6 a 8, robô
  quando há mais de um), pergunte — uma pergunta objetiva por vez.`.trim();
}

const conversas = new Map();   // id -> { ocupada, iniciada }

function marcaIniciada(pasta) {
    return path.join(pasta, '.sessao-iniciada');
}

function rotuloFerramenta(nome, entrada) {
    const e = entrada || {};
    if (nome === 'Bash') {
        const cmd = String(e.command || '');
        if (/montar\.py/.test(cmd)) return '🗄️ Buscando dados na planilha, banco, GLPI e vault…';
        if (/gerar\.py/.test(cmd)) return '🎨 Gerando a apresentação e a conferência visual…';
        return '⚙️ Consultando: ' + cmd.split(/\s+/).slice(0, 2).join(' ');
    }
    const arq = path.basename(String(e.file_path || e.path || e.pattern || ''));
    if (nome === 'Read') return '📖 Lendo ' + (arq || 'arquivo');
    if (nome === 'Edit' || nome === 'Write') return '✏️ Ajustando ' + (arq || 'arquivo');
    if (nome === 'Grep' || nome === 'Glob') return '🔎 Procurando' + (arq ? ' ' + arq : '');
    return '⚙️ ' + nome;
}

function novaConversa() {
    ex.verificarRepositorio();
    const id = ex.novoTrabalho();
    conversas.set(id, { ocupada: false });
    return id;
}

/**
 * Manda uma mensagem e repassa a resposta em pedaços:
 *   aoEvento({tipo: 'texto', texto}) | {tipo: 'ferramenta', rotulo}
 *   | {tipo: 'slides', ...estado} | {tipo: 'fim'} | {tipo: 'erro', erro}
 */
function enviar(id, texto, aoEvento) {
    ex.verificarRepositorio();
    const pasta = ex.pastaDo(id);
    const msg = String(texto || '').trim();
    if (!msg) throw new ex.ErroDeEntrada('Mensagem vazia.');
    if (msg.length > cfg.limiteMensagem) throw new ex.ErroDeEntrada('Mensagem longa demais.');

    const c = conversas.get(id) || { ocupada: false };
    conversas.set(id, c);
    if (c.ocupada) throw new ex.ErroDeEntrada('O agente ainda está respondendo a mensagem anterior.');
    c.ocupada = true;

    const iniciada = fs.existsSync(marcaIniciada(pasta));
    const args = ['-p', '--output-format', 'stream-json', '--verbose', '--include-partial-messages',
        iniciada ? '--resume' : '--session-id', id,
        '--append-system-prompt', instrucoesDoChat(pasta),
        '--add-dir', pasta];
    const vault = vaultPadrao();
    if (vault) args.push('--add-dir', vault);
    args.push('--allowedTools', ...PERMITIDAS, '--disallowedTools', ...PROIBIDAS);

    const antes = ex.estado(id).versao;
    const proc = spawn(cfg.claude, args, {
        cwd: cfg.repositorio,
        env: Object.assign({}, process.env, { PYTHONIOENCODING: 'utf-8' }),
        windowsHide: true
    });
    const limite = setTimeout(() => proc.kill(), cfg.timeoutRespostaMs);

    let buffer = '', erroTexto = '', viuTexto = false, resultado = null;
    proc.stdout.on('data', (d) => {
        buffer += d.toString('utf-8');
        let i;
        while ((i = buffer.indexOf('\n')) >= 0) {
            const linha = buffer.slice(0, i).trim();
            buffer = buffer.slice(i + 1);
            if (!linha) continue;
            let ev;
            try { ev = JSON.parse(linha); } catch (_) { continue; }
            if (ev.type === 'system' && ev.subtype === 'init') {
                fs.writeFileSync(marcaIniciada(pasta), String(ev.session_id || id));
            } else if (ev.type === 'stream_event' && ev.event && ev.event.type === 'content_block_delta'
                && ev.event.delta && ev.event.delta.type === 'text_delta') {
                viuTexto = true;
                aoEvento({ tipo: 'texto', texto: ev.event.delta.text });
            } else if (ev.type === 'stream_event' && ev.event && ev.event.type === 'message_start' && viuTexto) {
                // novo trecho de resposta depois de usar ferramenta: separa
                aoEvento({ tipo: 'texto', texto: '\n\n' });
            } else if (ev.type === 'assistant' && ev.message && Array.isArray(ev.message.content)) {
                for (const b of ev.message.content) {
                    if (b.type === 'tool_use') aoEvento({ tipo: 'ferramenta', rotulo: rotuloFerramenta(b.name, b.input) });
                }
            } else if (ev.type === 'result') {
                resultado = ev;
            }
        }
    });
    proc.stderr.on('data', (d) => { erroTexto += d.toString('utf-8'); });

    return new Promise((resolve) => {
        const terminar = (falha) => {
            clearTimeout(limite);
            c.ocupada = false;
            try {
                const agora = ex.estado(id);
                if (agora.versao !== antes) aoEvento(Object.assign({ tipo: 'slides' }, agora));
            } catch (_) { /* pasta sumiu */ }
            if (falha) aoEvento({ tipo: 'erro', erro: falha });
            else if (!viuTexto && resultado && resultado.result) aoEvento({ tipo: 'texto', texto: resultado.result });
            aoEvento({ tipo: 'fim' });
            resolve();
        };
        proc.on('error', (e) => terminar(e.code === 'ENOENT'
            ? `Não achei o Claude Code ("${cfg.claude}"). Defina GERADOR_ATE_CLAUDE com o caminho do executável.`
            : e.message));
        proc.on('close', (codigo) => {
            if (resultado && resultado.is_error) {
                return terminar('O agente parou com erro: ' + (resultado.result || resultado.subtype));
            }
            if (codigo !== 0 && !resultado) {
                const dica = /login|auth|401|credential/i.test(erroTexto)
                    ? ' — o Claude Code desta máquina precisa estar logado (rode "claude" uma vez e faça /login).' : '';
                return terminar(`O Claude Code saiu com código ${codigo}${dica}\n${erroTexto.slice(-800)}`);
            }
            terminar(null);
        });
        proc.stdin.end(msg, 'utf-8');
    });
}

module.exports = { novaConversa, enviar };
