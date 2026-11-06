# Integração com o portal: o chat do Gerador de ATE

O gerador tem uma tela de **chat** no portal Automation Control Plus: o site
`gerador-ate`. O código mora **neste repositório**, em
[`portal/sites/gerador-ate/`](../portal/sites/gerador-ate/), e é copiado
para `sites/gerador-ate/` do portal — o guia do portal
(`docs/COMO_ADICIONAR_SITES.md`) manda que todo o código do site fique só ali.

## Como funciona

A gestora conversa; quem responde é **o Claude Code** rodando sem tela
(`claude -p`) dentro deste repositório — o mesmo agente do terminal:

- usa o **login/assinatura de quem instalou o Claude Code** na máquina — sem
  chave de API e sem cobrança à parte;
- lê o `CLAUDE.md` e esta base sozinho;
- cada conversa é uma sessão (`--session-id` na 1ª mensagem, `--resume`
  depois), então ele lembra do que já foi dito;
- a resposta chega na tela em tempo real; as ferramentas que ele usa
  aparecem como linhas cinza ("Buscando dados…", "Gerando…");
- quando um .pptx novo aparece na pasta da conversa, o painel da direita
  mostra as miniaturas e o botão de baixar.

Cada conversa tem uma pasta própria (params.json, .pptx, PNGs); o
`params.json` do repositório não é tocado. Pastas com mais de 24 h somem.

## O que o agente pode e não pode na tela

`services/agente.js` passa listas fixas ao Claude Code (em `-p`, o que
estiver fora da lista é negado sem perguntar):

| Pode | Não pode |
|---|---|
| Read, Glob, Grep (repositório, pasta da conversa, vault) | WebFetch, WebSearch |
| `python montar.py / gerar.py / execucoes.py / glpi_sla.py / probe.py` | git, curl, rm, qualquer outro comando |
| Edit/Write de dados (params da conversa; `-local.json` com aprovação da gestora) | editar `.py`, `.md`, `.env`, `.pptx`, `.xlsx` |

Instruções extras só da tela (`--append-system-prompt`): responder curto,
uma pergunta por vez, sem git (o repositório é atualizado por quem mantém o
portal), comandos sempre na forma `python <script>.py ...`, sem scripts
auxiliares.

## Instalar no portal

1. copiar `portal/sites/gerador-ate/` para `sites/gerador-ate/`;
2. no ambiente do portal:
   ```
   GERADOR_ATE_DIR=<pasta deste repositório, com .env, planilha e -local.json>
   GERADOR_ATE_CLAUDE=<caminho do claude, se não estiver no PATH>
   GERADOR_ATE_VAULT=<pasta do vault>          # opcional se houver Obsidian
   GERADOR_ATE_JOBS=/var/tmp/gerador-ate       # opcional
   ```
3. Claude Code instalado **e logado** nesse host; Python 3 + `python-pptx`
   + `pymysql`; LibreOffice para as miniaturas no Linux;
4. reiniciar e conferir `[registry] Site registrado: Gerador de ATE`
   (`meta.permissao: 8`).

## Simular sem o portal

```
GERADOR_ATE_DIR=<repo> GERADOR_ATE_CLAUDE=<claude> node sites/gerador-ate/simular.js [porta]
```

Sobe só o chat em `127.0.0.1` (sem `server.js`, sem login, **sem** a
sincronização de permissões que grava em `acp_permissao`).

## Atenção: assinatura

O chat consome a assinatura de quem está logado no Claude Code daquela
máquina. Para uso da própria gestora, na máquina dela, é o caso de uso
normal. Para **várias pessoas** usando pelo portal num servidor, confirme
antes se o plano contratado permite esse uso compartilhado (plano de equipe
ou empresa) — senão, cada pessoa usa o chat na própria máquina.
