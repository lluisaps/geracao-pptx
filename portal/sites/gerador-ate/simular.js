/**
 * Sobe só o chat do Gerador de ATE, sem o resto do portal:
 *
 *   GERADOR_ATE_DIR=<pasta do geracao-pptx> \
 *   GERADOR_ATE_CLAUDE=<caminho do claude, se não estiver no PATH> \
 *   node sites/gerador-ate/simular.js [porta]
 *
 * Escuta só em 127.0.0.1. Não sobe o server.js, não exige login e não roda
 * a sincronização de permissões (que gravaria em acp_permissao). O agente é
 * o Claude Code desta máquina, com o login dela.
 */
const express = require('express');

const app = express();
// o portal real responde isto; aqui a sessão está sempre "ativa"
app.get('/api/session/status', (req, res) => res.json({ ativa: true, aviso: null }));
app.get('/', (req, res) => res.redirect('/gerador-ate'));
require('./index').register(app);

const porta = Number(process.argv[2]) || 4790;
app.listen(porta, '127.0.0.1', () => {
    console.log(`Gerador de ATE (simulação) em http://127.0.0.1:${porta}/gerador-ate`);
    console.log(`repositório: ${process.env.GERADOR_ATE_DIR || '(GERADOR_ATE_DIR não definida!)'}`);
});
