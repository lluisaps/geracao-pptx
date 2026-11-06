const express = require('express');
const router = express.Router();
const ex = require('../services/execucao');
const agente = require('../services/agente');

router.use(express.json({ limit: '64kb' }));

function responderErro(res, err, onde) {
    if (err instanceof ex.ErroDeEntrada) return res.status(400).json({ erro: err.message });
    console.error(`[gerador-ate] ${onde}`, err);
    return res.status(500).json({ erro: 'Erro interno: ' + err.message });
}

// nova conversa = nova pasta de trabalho + nova sessão do agente
router.post('/conversas', (req, res) => {
    try {
        res.json({ id: agente.novaConversa() });
    } catch (err) {
        responderErro(res, err, 'conversas');
    }
});

// mensagem: a resposta volta em pedaços (uma linha JSON por evento)
router.post('/conversas/:id/mensagens', async (req, res) => {
    let aberto = false;
    const enviarLinha = (ev) => {
        if (!aberto) {
            res.status(200).set({
                'Content-Type': 'application/x-ndjson; charset=utf-8',
                'Cache-Control': 'no-store',
                'X-Accel-Buffering': 'no'
            });
            res.flushHeaders();
            aberto = true;
        }
        res.write(JSON.stringify(ev) + '\n');
    };
    try {
        await agente.enviar(req.params.id, req.body && req.body.texto, enviarLinha);
        res.end();
    } catch (err) {
        if (!aberto) return responderErro(res, err, 'mensagem');
        enviarLinha({ tipo: 'erro', erro: err.message });
        res.end();
    }
});

router.get('/conversas/:id/slides/:arquivo', (req, res) => {
    try {
        res.setHeader('Cache-Control', 'no-store');
        res.sendFile(ex.caminhoSlide(req.params.id, req.params.arquivo));
    } catch (err) {
        responderErro(res, err, 'slide');
    }
});

router.get('/conversas/:id/download', (req, res) => {
    try {
        const { caminho, nome } = ex.caminhoPptx(req.params.id);
        res.download(caminho, nome);
    } catch (err) {
        responderErro(res, err, 'download');
    }
});

module.exports = router;
