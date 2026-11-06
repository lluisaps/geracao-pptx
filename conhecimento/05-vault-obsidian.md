# Vault do Obsidian

Fonte **obrigatória** dos textos: escopo (slide 2) e oportunidades no
segmento (slide 8). O caminho não é fixo: o `montar.py` lê o registro do
Obsidian (`%APPDATA%/obsidian/obsidian.json`) ou procura uma pasta com
`.obsidian` dentro. Nada do vault é copiado para o repositório.

## Organização

```
<vault>/02 - Vault dos Robôs/
  Vault dos Robôs MOC.md     índice: robôs por cliente, com objetivo e IA
  Sistemas.md · Artefatos.md · Pendências.md
  Projetos/<CÓDIGO> - <repositório>.md    uma nota por robô (~240)
```

O vault é levantado a partir dos repositórios da org no GitHub, na branch com
commit mais recente — por isso é "sempre atualizado": quando o código muda,
a nota é regerada.

## Nota de robô (`tipo: robo`)

Frontmatter:

| Campo | Uso |
|---|---|
| `cliente` | casamento com o cliente do pedido (1ª palavra, sem acento) |
| `codigo` | código do robô; casa com a planilha |
| `segmento_empresa` | ramo do cliente |
| `segmento_projeto` | `Área - assunto`; base das oportunidades |
| `sistemas` | sistemas que o robô toca (bom para o escopo) |
| `tabelas` | tabelas do banco; **descobre o código** quando a OBS da planilha não tem |
| `ia`, `status_projeto`, `ultimo_commit` | contexto, não vai para o slide |

Seções fixas: `## 1. Cliente` … `## 3. Objetivo` … `## 9. Segmento do
projeto`, `## Tecnologia`, `## Acessos`. **O escopo sai da `## 3. Objetivo`.**

## Dossiê de cliente (`tags: dossie`)

Quando existe, tem precedência sobre a nota do robô: `### 2. Objetivo do
projeto` (ou o `**Objetivo:**` do bloco `## Robô N — <código>: <nome>` em
dossiê de vários robôs). Hoje o vault pode não ter dossiês — aí vale a nota.

## Escopo: como condensar

- original da nota → ~200 caracteres, no máximo 2 linhas;
- fica: **ação + o que processa + sistema**;
- sai: etapas, volumetria, horário, "substitui processo manual";
- pode **resumir**; não pode acrescentar fato que não está na nota;
- mostre original e resumido lado a lado, com o arquivo e a seção de origem.

## Oportunidades no segmento

1. pega a área do robô (antes do ` - ` em `segmento_projeto`);
2. junta notas da **mesma área em outros clientes**;
3. tira os assuntos que este cliente já tem;
4. conta em quantos clientes cada assunto roda.

Sai só o assunto. **Nome de outro cliente nunca vai para o slide.**

Quando a área não tem nada em outros clientes, o agente pode olhar a área
**vizinha** que faça sentido para o ramo do cliente (ex.: integração de
atendimento → área "Atendimento") — mas tem que **dizer de onde tirou** e o
que descartou, e o item precisa existir como nota no vault.

## Código do robô pelo vault

Planilha cuja OBS não tem código: o `montar.py` procura a nota do mesmo
cliente cujas `tabelas` sejam a tabela da planilha ou comecem com ela
(`yank_000000` casa `yank_000000_filtros`). Um código → usa. Dois → avisa e
pede `--robo`.
