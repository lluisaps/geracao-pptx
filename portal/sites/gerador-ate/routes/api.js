const express = require('express');
const router = express.Router();
const cfg = require('../config');
const ex = require('../services/execucao');

router.use(express.json({ limit: cfg.limiteParamsBytes }));

function responderErro(res, err, onde) {
    if (err instanceof ex.ErroDeEntrada) {
        return res.status(400).json({ erro: err.message });
    }
    console.error(`[gerador-ate] ${onde}`, err);
    return res.status(500).json({ erro: 'Erro interno: ' + err.message });
}

// 1. busca os dados: planilha, vault, banco (leitura) e GLPI (leitura)
router.post('/montar', async (req, res) => {
    try {
        res.json(await ex.montar(req.body || {}));
    } catch (err) {
        responderErro(res, err, 'montar');
    }
});

// 2. grava o params revisado
router.put('/trabalhos/:id/params', (req, res) => {
    try {
        res.json(ex.salvarParams(req.params.id, req.body && req.body.params));
    } catch (err) {
        responderErro(res, err, 'params');
    }
});

// 3. gera o .pptx e a conferência visual
router.post('/trabalhos/:id/gerar', async (req, res) => {
    try {
        res.json(await ex.gerar(req.params.id));
    } catch (err) {
        responderErro(res, err, 'gerar');
    }
});

router.get('/trabalhos/:id/slides/:arquivo', (req, res) => {
    try {
        res.setHeader('Cache-Control', 'no-store');
        res.sendFile(ex.caminhoSlide(req.params.id, req.params.arquivo));
    } catch (err) {
        responderErro(res, err, 'slide');
    }
});

router.get('/trabalhos/:id/download', (req, res) => {
    try {
        const { caminho, nome } = ex.caminhoPptx(req.params.id);
        res.download(caminho, nome);
    } catch (err) {
        responderErro(res, err, 'download');
    }
});

module.exports = router;
