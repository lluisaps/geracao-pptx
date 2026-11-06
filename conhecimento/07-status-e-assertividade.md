# Status e assertividade

Cada `status_execucao` cai em um de três baldes (`status.py`):

| Balde | Significa | Conta como |
|---|---|---|
| `sucesso` | o robô entregou o item | acerto, e item entregue (valor gerado) |
| `excecao_negocio` | o caso foi barrado pela regra, dado faltando no cliente, portal/API externa fora | **acerto** — o robô fez o que devia |
| `falha_robo` | o **robô** errou | erro |

```
assertividade = (total − falha_robo) / total
```

## Onde a classificação mora

1. `status-local.json` (local, chave = código do robô) — manda;
2. `status.json` (versionado, vazio de propósito — só documenta o formato);
3. `PADROES` no `status.py` — regras genéricas ("com sucesso", "não
   cadastrado", "já processado"…).

Status que nenhuma casa → o `montar.py` **para** e imprime o bloco pronto para
colar. O agente propõe os baldes, **mostra para a gestora** e só grava depois
do ok. A régua: na dúvida entre negócio e falha, pergunte "o robô poderia ter
feito diferente?". Se não, é negócio.

A chave do bloco é o **código do robô**. Bloco antigo gravado pelo número da
linha da planilha precisa ser renomeado quando o robô ganhar código.

## Grupos para volume e prevenção

Por cima dos baldes, o `montar.py` separa:

| Grupo | Regra | Vai para |
|---|---|---|
| externo | status casa `EXTERNO` (HTTP 5xx, socket hang up, timeout, indisponível, fora do ar…) | "falhas de API detectadas" |
| negócio | `excecao_negocio` que não é externo | "casos fora da regra" |
| falha | `falha_robo` | linha "Falhas do robô" do volume |

O grupo externo **não muda a assertividade** — é só como o número é contado
para os slides 5 e 6.
