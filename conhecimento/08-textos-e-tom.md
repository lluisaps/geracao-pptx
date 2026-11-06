# Textos e tom

Quem lê o ATE é a **diretoria do cliente**. Escreva resultado, não sistema.

## Regras

- Frase curta, verbo no começo ou número no começo.
- `**assim**` destaca: azul no escopo e nos títulos; negrito nas entregas e
  nos slides 7 e 8.
- **Não numere** tópicos (1., 2.) — a numeração é automática.
- Sem jargão de log: nada de "status code 500", "socket hang up", nome de
  tabela, nome de coluna, nome de função.
- Sem nome de pessoa do cliente, valor de contrato, mensalidade, ROI, contato.
- Sem nome de outro cliente. Nunca.

## Status → frase de entrega

| Status no banco | Frase no slide |
|---|---|
| `NOTA LANCADA COM SUCESSO` | notas fiscais lançadas no ERP, já conferidas com o pedido |
| `Arquivo enviado` | relatórios entregues à área de auditoria |
| `Request failed with status code 500` | (não é entrega — vai para "falhas de API detectadas") |

(exemplos fictícios)

A frase diz **só o que o status diz**. Não acrescente benefício que o dado não
sustenta.

## Prevenção (slide 6)

Destaque = número + o que ele mede + uma linha de contexto:

> **230** falhas de API detectadas
> Erros dos sistemas externos registrados automaticamente, sem parar a operação.

A faixa de baixo conta o que a equipe fez (vem do pedido): "Tratamento das
maiores causas de chamado: instabilidade de portal, queda da VPN…".

## Oportunidades (slide 8)

Reescreva o assunto do vault como oportunidade para este cliente:

| Vault | Slide |
|---|---|
| `Atendimento - NPS` | **NPS**: coleta e consolidação automática das notas de recomendação. |
| `Atendimento - pesquisa de satisfação` | **Pesquisa de satisfação** automatizada com os clientes atendidos. |

## Tamanhos que cabem

| Onde | Limite prático |
|---|---|
| escopo (slide 2) | ~200 caracteres |
| item de entrega (slide 2) | 1 linha (~90 caracteres) |
| legenda/pílula (slide 3) | 1 linha cada (~32 / ~16 caracteres) |
| rótulo da tabela (slide 5) | ~60 caracteres (quebra em 2 linhas) |
| texto do destaque (slide 6) | ~110 caracteres |
| tópico dos slides 7 e 8 | 2 linhas |

Estourou? Reescreva mais curto — não diminua fonte.
