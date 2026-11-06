# Integração com o portal (plano)

O gerador vai ser exposto como um **site do portal Automation Control Plus**
(Node/Express, sites modulares). O guia do portal é o
`docs/COMO_ADICIONAR_SITES.md` daquele repositório — siga-o à risca.

## O que o guia exige (resumo)

- todo o código do site novo em `sites/<id>/` — nada em `core/`, `server.js`
  ou em outro site;
- `sites/<id>/index.js` exporta `meta` (`id`, `permissao` única, `nome`,
  `icone`, `url`) e `register(app)` com prefixo de URL próprio;
- tabelas e regras no `sites/<id>/config.js`; HTML em `sites/<id>/views/`;
- banco pelo `config/database.js` compartilhado (`pool`);
- testar local com `npm run dev` + `scripts/generate-dev-token.js`; conferir
  `[registry] Site registrado: ...` no log; deploy por `docker compose`.

## Desenho proposto: `sites/gerador-ate/`

```
sites/gerador-ate/
├── index.js        meta { id: 'gerador-ate', nome: 'Gerador de ATE', url: '/gerador-ate' }
├── config.js       caminho do repositório geracao-pptx no servidor, python
├── routes/
│   ├── index.js
│   ├── montar.js   POST /montar  -> roda montar.py, devolve o relatório + params
│   ├── gerar.js    POST /gerar   -> roda gerar.py, devolve o .pptx
│   └── params.js   GET/PUT /params -> edição dos textos com REVISAR
└── views/templates.js   formulário: cliente, trimestre, robô, tempo, custo,
                         textos dos slides 7 e 8; prévia dos PNGs
```

O site **não reimplementa** a lógica: chama `montar.py` e `gerar.py` deste
repositório (`child_process.execFile`, sem shell, argumentos validados). As
regras continuam num lugar só — aqui.

## Pontos em aberto (decidir antes de construir)

1. **Onde roda o Python** — no container do portal (instalar python3 +
   python-pptx) ou num serviço à parte.
2. **Planilha e arquivos locais** no servidor (`.xlsx`, `status-local.json`,
   `valor-local.json`) — volume montado, fora da imagem.
3. **Vault no servidor** — clone/sync do vault, já que lá não há Obsidian.
4. **Conferência visual** — no Linux só com LibreOffice (`soffice`).
5. **Revisão humana** — o fluxo de REVISAR precisa de tela de edição; o
   agente (Claude) pode ser chamado pelo site para propor os textos.
6. **Permissão** — `meta.permissao` novo, só para gestão de contas.
