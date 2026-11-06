const os = require('os');
const path = require('path');

/**
 * O "cérebro" do chat é o Claude Code rodando sem tela (-p) dentro do
 * repositório geracao-pptx — com o MESMO login/assinatura de quem o
 * instalou, sem chave de API à parte. Ele lê o CLAUDE.md e a base
 * conhecimento/ sozinho; o site só repassa mensagens e mostra os slides.
 *
 *   GERADOR_ATE_DIR     pasta do geracao-pptx (montar.py, gerar.py, .env,
 *                       planilha, -local.json)                 — obrigatória
 *   GERADOR_ATE_CLAUDE  executável do Claude Code              — padrão: "claude"
 *   GERADOR_ATE_VAULT   pasta do vault do Obsidian             — padrão: o que o
 *                       Obsidian registrou em %APPDATA%/obsidian/obsidian.json
 *   GERADOR_ATE_JOBS    pasta de trabalho de cada conversa     — padrão: temporária
 */
module.exports = {
    repositorio: process.env.GERADOR_ATE_DIR || '',
    claude: process.env.GERADOR_ATE_CLAUDE || 'claude',
    vault: process.env.GERADOR_ATE_VAULT || '',
    pastaTrabalhos: process.env.GERADOR_ATE_JOBS || path.join(os.tmpdir(), 'gerador-ate'),

    // uma resposta do agente pode buscar banco, GLPI e gerar o deck
    timeoutRespostaMs: 15 * 60 * 1000,

    // conversa (e a pasta dela) mais velha que isto é apagada
    validadeTrabalhoMs: 24 * 60 * 60 * 1000,

    limiteMensagem: 8000
};
