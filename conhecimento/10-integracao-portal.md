# Integração com o portal

O gerador tem uma tela no **portal Automation Control Plus** (Node/Express,
sites modulares): o site `gerador-ate`. O código mora **neste repositório**,
em [`portal/sites/gerador-ate/`](../portal/sites/gerador-ate/), e é copiado
para `sites/gerador-ate/` do portal — o guia do portal
(`docs/COMO_ADICIONAR_SITES.md`) manda que todo o código do site fique só ali.

## O que a tela faz

1. **Cliente e trimestre** → roda `montar.py` (planilha, vault, banco e GLPI
   em leitura) e mostra o relatório do que conferir.
2. **Revisar** → cartões de resumo (itens, entregues, assertividade, SLA,
   disponibilidade) e os campos com texto: escopo, tempo manual, custo/hora,
   entregas, destaques e faixa do slide 6, slides 7 e 8, slides a ocultar,
   params.json completo. Campo com `REVISAR` fica amarelo e o botão de gerar
   fica **bloqueado** até não sobrar nenhum.
3. **Gerar** → roda `gerar.py --conferencia`, mostra os slides em miniatura e
   dá o download do .pptx.

Cada pedido é um **trabalho** numa pasta própria (params, .pptx, PNGs); o
`params.json` do repositório nunca é tocado. Trabalhos com mais de 24 h são
apagados quando um novo começa.

## Regras do site

- não reimplementa regra de ATE: chama `montar.py` e `gerar.py` daqui;
- Python por `execFile`, sem shell; cliente, meses, robô e competência
  validados; id de trabalho e nome de slide só no padrão (sem `../`);
- `meta.permissao: 8` (1–7 já usados no portal em 2026-11) — só gestão de
  contas deve receber;
- não grava `valor-local.json` nem `status-local.json`: tempo e custo vão só
  no params do trabalho. Gravar para os próximos trimestres continua sendo
  decisão da gestora, feita no repositório.

## Instalar no portal

1. copiar `portal/sites/gerador-ate/` para `sites/gerador-ate/` do portal;
2. no ambiente do portal:
   ```
   GERADOR_ATE_DIR=<pasta deste repositório, com .env, planilha e -local.json>
   GERADOR_ATE_PYTHON=python3            # opcional
   GERADOR_ATE_JOBS=/var/tmp/gerador-ate # opcional
   ```
3. Python 3 + `python-pptx` + `pymysql` no mesmo host/container; LibreOffice
   para as miniaturas no Linux (no Windows, PowerPoint);
4. o vault precisa estar acessível nesse host (o `montar.py` acha pelo
   registro do Obsidian ou por uma pasta com `.obsidian`; `--vault` não é
   exposto na tela — em servidor, deixe um `.obsidian` na raiz do vault);
5. reiniciar e conferir `[registry] Site registrado: Gerador de ATE`.

## Simular sem o portal

```
GERADOR_ATE_DIR=<repo> node sites/gerador-ate/simular.js "<cliente>" 2026-04 2026-06
```

Sobe só este site (sem `server.js`, sem login, **sem** a sincronização de
permissões que grava em `acp_permissao`), faz o fluxo pela API e confere
validação, bloqueio por REVISAR, geração, PNG e download. Os textos que a
simulação preenche saem marcados `[SIMULAÇÃO]`.

## Em aberto

- **Onde roda o Python** no servidor: container do portal ou serviço à parte.
- **Vault no servidor**: sync do vault, já que lá não há Obsidian.
- **Agente na tela**: botão "propor textos" chamando o Claude com a base de
  `conhecimento/` — hoje a revisão é manual.
