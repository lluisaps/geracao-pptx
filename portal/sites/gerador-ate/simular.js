/**
 * Simulador do site Gerador de ATE, sem o resto do portal.
 *
 *   GERADOR_ATE_DIR=<pasta do geracao-pptx> node sites/gerador-ate/simular.js \
 *       "<cliente>" <AAAA-MM> <AAAA-MM> [--robo X]     -> roda o fluxo pela API
 *   GERADOR_ATE_DIR=... node sites/gerador-ate/simular.js --servir [porta]
 *                                                       -> sobe a tela para usar no navegador
 *
 * Monta só este site num express próprio: não sobe o server.js, não exige
 * login e, principalmente, NÃO roda a sincronização de permissões — que
 * gravaria em acp_permissao. O montar.py consulta banco e GLPI só em leitura.
 *
 * O fluxo pela API faz o que a gestora faz na tela: busca, preenche os textos
 * que ficaram com REVISAR (com marcação [SIMULAÇÃO], para ninguém confundir
 * com ATE de verdade), grava e gera.
 */
const express = require('express');
const path = require('path');

const app = express();
// o portal real responde isto; aqui a sessão está sempre "ativa"
app.get('/api/session/status', (req, res) => res.json({ ativa: true, aviso: null }));
app.get('/', (req, res) => res.redirect('/gerador-ate'));
require('./index').register(app);

const args = process.argv.slice(2);

if (args[0] === '--servir') {
    const porta = Number(args[1]) || 4790;
    app.listen(porta, () => {
        console.log(`Gerador de ATE (simulação) em http://localhost:${porta}/gerador-ate`);
        console.log(`repositório: ${process.env.GERADOR_ATE_DIR || '(GERADOR_ATE_DIR não definida!)'}`);
    });
} else {
    const servidor = app.listen(0, async () => {
        const base = `http://localhost:${servidor.address().port}/gerador-ate`;
        let falhou = false;
        const ok = (cond, msg) => { console.log(`${cond ? '  ok ' : '  FALHOU'} ${msg}`); if (!cond) falhou = true; };
        const json = async (metodo, url, corpo) => {
            const r = await fetch(base + url, { method: metodo,
                headers: { 'Content-Type': 'application/json' }, body: corpo ? JSON.stringify(corpo) : undefined });
            return { status: r.status, corpo: await r.json() };
        };
        try {
            const [cliente, ini, fim] = args;
            const robo = args.includes('--robo') ? args[args.indexOf('--robo') + 1] : '';

            console.log('1. página');
            const pag = await fetch(base);
            const html = await pag.text();
            ok(pag.status === 200 && html.includes('Gerador de <span>ATE</span>'), 'GET /gerador-ate responde a tela');

            console.log('2. validação');
            const ruim = await json('POST', '/api/montar', { cliente: 'x', ini: '2026-13', fim: '2026-06' });
            ok(ruim.status === 400, `mês inválido recusado (${ruim.corpo.erro})`);
            const inj = await json('POST', '/api/montar', { cliente: 'x', ini: '2026-04', fim: '2026-06', robo: 'A; rm -rf' });
            ok(inj.status === 400, 'robô com caractere estranho recusado');
            const trav = await fetch(base + '/api/trabalhos/..%2F..%2Fetc/download');
            ok(trav.status === 400, 'id de trabalho fora do padrão recusado');

            console.log(`3. buscar dados: ${cliente} ${ini}..${fim}`);
            const t0 = Date.now();
            const m = await json('POST', '/api/montar', { cliente, ini, fim, robo });
            ok(m.status === 200 && m.corpo.params, `montar.py em ${((Date.now() - t0) / 1000).toFixed(0)}s, código ${m.corpo.codigo}`);
            if (!m.corpo.params) { console.log(m.corpo.log || m.corpo.erro); throw new Error('sem params'); }
            const p = m.corpo.params;
            console.log(`     execuções=${(p.grafico_execucoes.execucoes || []).join('/')}  assertividade=${p.grafico_execucoes.assertividade}  REVISAR=${m.corpo.revisar}`);

            const bloqueio = await json('POST', `/api/trabalhos/${m.corpo.id}/gerar`);
            ok(m.corpo.revisar === 0 || bloqueio.status === 400, `com REVISAR pendente o gerar é bloqueado (${bloqueio.corpo.erro || 'nada pendente'})`);

            console.log('4. revisão (o que a gestora faria na tela)');
            const tira = (t) => String(t).replace(/^REVISAR: (condensar para ~200 caracteres\. )?/, '');
            p.escopo = tira(p.escopo);
            p.valor_gerado.entregas = p.valor_gerado.entregas.map(tira);
            if (p.prevencao) {
                p.prevencao.destaques.forEach((d) => { d.texto = tira(d.texto); });
                p.prevencao.faixa.texto = '[SIMULAÇÃO] texto da gestora sobre prevenção no trimestre.';
            }
            const SIM = '[SIMULAÇÃO] tópico que viria do pedido da gestora.';
            p.melhorias.esquerda = [{ topico: 'O que foi entregue no robô', itens: [SIM] }];
            p.melhorias.direita = [{ topico: 'O que fizemos para evitar falhas', itens: [SIM] }];
            p.proximas_evolucoes.esquerda = [{ topico: 'Próximas evoluções', itens: [SIM] }];
            const dir = p.proximas_evolucoes.direita[0];
            dir.topico = 'Oportunidades no segmento';
            dir.itens = dir.itens.filter((i) => !/REVISAR/.test(i));
            if (!dir.itens.length) dir.itens = ['[SIMULAÇÃO] oportunidade do segmento, a partir do vault.'];
            (p.volume_processado ? p.volume_processado.linhas : []).forEach((l) => { l.rotulo = tira(l.rotulo); });

            const s = await json('PUT', `/api/trabalhos/${m.corpo.id}/params`, { params: p });
            ok(s.status === 200 && s.corpo.revisar === 0, `params gravado, REVISAR restante: ${s.corpo.revisar}`);

            console.log('5. gerar');
            const g = await json('POST', `/api/trabalhos/${m.corpo.id}/gerar`);
            ok(g.status === 200 && g.corpo.arquivo, `gerou ${g.corpo.arquivo} com ${g.corpo.slides.length} slides`);
            console.log((g.corpo.log || '').split('\n').filter((l) => /slides:|valor:|SLA:/.test(l)).map((l) => '     ' + l.trim()).join('\n'));
            const sl = await fetch(`${base}/api/trabalhos/${m.corpo.id}/slides/${g.corpo.slides[0]}`);
            ok(sl.status === 200 && /image/.test(sl.headers.get('content-type')), 'PNG do slide 1 servido');
            const dl = await fetch(`${base}/api/trabalhos/${m.corpo.id}/download`);
            const buf = Buffer.from(await dl.arrayBuffer());
            ok(dl.status === 200 && buf.slice(0, 2).toString() === 'PK', `download do .pptx (${(buf.length / 1024).toFixed(0)} KB)`);
            console.log(`\npasta do trabalho: ${path.join(require('./config').pastaTrabalhos, m.corpo.id)}`);
        } catch (e) {
            falhou = true;
            console.error('erro:', e.message);
        }
        console.log(falhou ? '\nSIMULAÇÃO COM FALHA' : '\nSIMULAÇÃO OK');
        servidor.close();
        process.exitCode = falhou ? 1 : 0;
    });
}
