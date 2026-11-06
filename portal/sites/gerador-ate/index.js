module.exports = {
    meta: {
        id: 'gerador-ate',
        permissao: 8,
        nome: 'Gerador de ATE',
        icone: '📑',
        cor: 'teal',
        url: '/gerador-ate'
    },
    register(app) {
        const router = require('./routes');
        app.use('/gerador-ate', router);
    }
};
