# Base de conhecimento do gerador de ATE

Cada arquivo responde a uma pergunta. O agente abre **só o do assunto** —
é assim que a base funciona como RAG sem encher o contexto.

| Arquivo | Responde | Abra quando |
|---|---|---|
| [01-estrutura-dos-slides.md](01-estrutura-dos-slides.md) | o que vai em cada slide, padrões, limites de texto | sempre que for preencher ou revisar um slide |
| [02-valor-gerado.md](02-valor-gerado.md) | horas poupadas, dias úteis, economia, disponibilidade | slides 2 e 3, ou pergunta sobre "valor" |
| [03-banco-de-execucoes.md](03-banco-de-execucoes.md) | onde ficam as execuções e como consultar | número de execução estranho, robô novo, quebra |
| [04-glpi.md](04-glpi.md) | chamados, SLA, entidades, categorias | SLA, disponibilidade, chamado que não apareceu |
| [05-vault-obsidian.md](05-vault-obsidian.md) | notas de robô, dossiês, segmento | escopo, oportunidades no segmento, código do robô |
| [06-planilha-de-robos.md](06-planilha-de-robos.md) | cliente → robô → tabela, OBS | cliente não achado, vários robôs, tabela somada |
| [07-status-e-assertividade.md](07-status-e-assertividade.md) | baldes de status e a régua | status sem classificação, assertividade baixa |
| [08-textos-e-tom.md](08-textos-e-tom.md) | como escrever para diretoria | qualquer texto que vai para o slide |
| [09-limites-e-seguranca.md](09-limites-e-seguranca.md) | o que o agente nunca faz | antes de qualquer consulta ou commit |
| [10-integracao-portal.md](10-integracao-portal.md) | como isto vira um site do portal | quando for integrar ao terminal/portal |

## Fontes, de relance

```
Planilha (.xlsx local) ─┐
                        ├─> montar.py ─> params.json ─> gerar.py ─> ATE.pptx
Banco MySQL (leitura) ──┤        ▲              ▲
GLPI API (leitura) ─────┤        │              └── revisão do agente (REVISAR)
Obsidian vault ─────────┘   status-local.json, valor-local.json (locais)
```

Ordem de confiança quando duas fontes discordam:

1. o **cabeçalho do pedido** (cliente, trimestre, competência, tempo, custo);
2. a **planilha** (tabela e robô);
3. o **banco** e o **GLPI** (números);
4. o **vault** (textos: escopo e segmento).

## Regra desta pasta

Nada de dado de cliente aqui: sem nome de cliente, código de robô, nome de
tabela ou número real. Exemplo é sempre fictício (`Cliente Exemplo`,
`ABC01`, `yank_000000`). O que é de cliente mora nos arquivos locais
listados em [09-limites-e-seguranca.md](09-limites-e-seguranca.md).
