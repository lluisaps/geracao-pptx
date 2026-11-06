const os = require('os');
const path = require('path');

/**
 * O site não tem regra de ATE nenhuma: ele chama o montar.py e o gerar.py do
 * repositório geracao-pptx, que é onde as regras moram (e a base de
 * conhecimento do agente, em conhecimento/). Aqui só fica ONDE achar esse
 * repositório e como rodar o Python — tudo por variável de ambiente, porque
 * muda de máquina para máquina.
 *
 *   GERADOR_ATE_DIR     pasta do geracao-pptx (com montar.py, gerar.py, .env,
 *                       planilha e os -local.json)          — obrigatória
 *   GERADOR_ATE_PYTHON  executável do Python                — padrão python/python3
 *   GERADOR_ATE_JOBS    onde cada geração guarda params, .pptx e PNGs
 *                                                           — padrão: pasta temporária
 */
module.exports = {
    repositorio: process.env.GERADOR_ATE_DIR || '',
    python: process.env.GERADOR_ATE_PYTHON || (process.platform === 'win32' ? 'python' : 'python3'),
    pastaTrabalhos: process.env.GERADOR_ATE_JOBS || path.join(os.tmpdir(), 'gerador-ate'),

    // montar.py consulta banco e GLPI; o gerar.py com conferência abre o PowerPoint
    timeoutMontarMs: 6 * 60 * 1000,
    timeoutGerarMs: 5 * 60 * 1000,

    // trabalho mais velho que isto é apagado quando um novo começa
    validadeTrabalhoMs: 24 * 60 * 60 * 1000,

    limiteParamsBytes: 300 * 1024
};
