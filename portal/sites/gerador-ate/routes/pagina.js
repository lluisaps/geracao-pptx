const express = require('express');
const router = express.Router();
const { isEmbedRequest } = require('../../../config/embedMode');
const { paginaGerador } = require('../views/pagina');

router.get('/', (req, res) => {
    res.send(paginaGerador({ embed: isEmbedRequest(req) }));
});

module.exports = router;
