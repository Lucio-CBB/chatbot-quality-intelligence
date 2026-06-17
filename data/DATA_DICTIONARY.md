# Data Dictionary — ABCD Dataset

## Fonte
ASAPP Research — Action-Based Conversations Dataset (2021)
Artigo: "ABCD: A Dataset for Agent Behavior in Customer Dialogs" (ACL-IJCNLP 2021)

## Arquivos em `data/raw/`
| Arquivo | Descrição |
|---|---|
| `abcd_v1.1.json` | Dataset completo com splits train/dev/test (~121 MB descompactado) |

## Estrutura de uma conversa (JSON bruto)

```json
{
  "convo_id": "...",
  "original": [                 // turnos brutos: lista de [speaker, text]
    ["customer", "..."],
    ["agent",    "..."]
  ],
  "delexed": [                  // turnos com PII delexicalizado + anotações
    {
      "speaker": "agent",
      "text":    "...",
      "turn_count": 1,
      "targets": [intent, action_type, action_value, ..., nextstep]
    }
  ],
  "scenario": {                 // (NÃO "scene")
    "subflow": "...",           // 96 subflows possíveis
    "flow":    "...",           // 10 flows pai
    "personal": {...},
    "order":    {...},
    "product":  {...}
  }
}
```

**Notas sobre `targets` (lista, não dict):**
O código acessa por índice posicional:
- `targets[1]` — tipo da ação (ex: `"take_action"`, `"retrieve_utterance"`)
- `targets[2]` — valor da ação (ex: `"try-again"`, `"verify-identity"`)

Ver uso em `src/run_patterns_ice.py` e `src/run_sentiment.py`.

---

## Campos gerados em `data/processed/`

### `conversations_patterns.parquet`
Saída de `src/run_patterns_ice.py` — uma linha por conversa.

| Campo | Tipo | Descrição |
|---|---|---|
| `convo_id` | string | Identificador único da conversa |
| `split` | string | `train` / `dev` / `test` |
| `flow` | string | Flow pai (10 categorias) |
| `subflow` | string | Subflow (96 categorias) |
| `n_turns` | int | Número total de turnos |
| `n_actions` | int | Número de ações `take_action` |
| `n_try_again` | int | Quantas vezes `try-again` foi acionada |
| `n_verify` | int | Quantas vezes `verify-identity` foi acionada |
| `n_logout` | int | Quantas vezes `log-out-in` foi acionada |
| `last_action` | string | Última ação tomada na conversa |
| `resolution` | int | `1` = resolvido; `0` = escalado (`notify-team` fora de contexto esperado) |
| `p_try_again` | int (0/1) | Padrão P1: pelo menos 1 `try-again` |
| `p_verify_loop` | int (0/1) | Padrão P2: `verify-identity` >1x |
| `p_escalation` | int (0/1) | Padrão P3: escalação inesperada |
| `p_action_rep` | int (0/1) | Padrão P4: alguma ação repetida >=3x |
| `p_long_outlier` | int (0/1) | Padrão P5: `n_turns` > média + 1,5·desvio do subflow |
| `any_pattern` | int (0/1) | Qualquer um dos 5 padrões |
| `turns_mean` | float | Média de turnos do subflow (referência para P5) |
| `turns_std` | float | Desvio-padrão de turnos do subflow |

### `conversations_sentiment.parquet`
Saída de `src/run_sentiment.py` — uma linha por conversa.

| Campo | Tipo | Descrição |
|---|---|---|
| `convo_id` | string | Identificador único |
| `split` | string | `train` / `dev` / `test` |
| `flow` | string | Flow pai |
| `subflow` | string | Subflow |
| `n_turns` | int | Número total de turnos |
| `n_try_again` | int | Quantas vezes `try-again` foi acionada |
| `resolution` | int | `1` = resolvido; `0` = escalado |
| `has_friction` | int (0/1) | `1` se contém `try-again` ou `verify-identity` >1x |
| `sent_opening` | float | VADER compound médio dos 2 primeiros turnos do cliente (-1 a +1) |
| `sent_closing` | float | VADER compound médio dos 2 últimos turnos do cliente |
| `sent_delta` | float | `sent_closing − sent_opening` |
| `sent_mean` | float | VADER compound médio em todos os turnos do cliente |

### `subflow_patterns_ice.csv`
Agregado por `(flow, subflow)` — 96 linhas.

| Campo | Tipo | Descrição |
|---|---|---|
| `flow`, `subflow` | string | Chave de agrupamento |
| `n` | int | Conversas no subflow |
| `resolution` | float | % conversas resolvidas |
| `p_try_again` … `p_long_outlier` | float | % conversas que disparam cada padrão |
| `any_pattern` | float | % conversas com qualquer padrão |
| `turns_mean` | float | Média de turnos |
| `impact` | float | `n × any_pattern / 100` |
| `confidence` | float | % do padrão dominante sobre `any_pattern` (0–100) |
| `ease` | int | Dificuldade da intervenção (1=trivial, 10=muito complexa) |
| `ice_score` | float | `impact × confidence / ease` |
| `ice_norm` | float | `ice_score` normalizado para 0–100 |

### `subflow_stats.csv`
Resumo descritivo por subflow.

| Campo | Tipo | Descrição |
|---|---|---|
| `flow`, `subflow` | string | Chave |
| `n` | int | Conversas |
| `resolucao_pct` | float | % resolvidas |
| `friccao_pct` | float | % com fricção |
| `try_again_pct` | float | % com `try-again` |
| `loop_pct` | float | % com qualquer loop detectado |
| `turnos_med` | float | Média de turnos |

---

## Flows e Subflows

São **10 flows pai** organizando **96 subflows**:

| Flow | # subflows | Exemplos |
|---|---|---|
| `account_access` | 3 | `recover_password`, `recover_username`, `reset_2fa` |
| `manage_account` | 7 | `manage_change_address`, `manage_payment_method`, `status_credit_missing` |
| `order_issue` | 9 | `manage_cancel`, `manage_create`, `status_delivery_date`, `status_payment_method` |
| `product_defect` | 6 | `refund_initiate`, `refund_status`, `return_color`, `return_size` |
| `purchase_dispute` | 8 | `bad_price_competitor`, `out_of_stock_general`, `promo_code_invalid` |
| `shipping_issue` | 4 | `cost`, `manage`, `missing`, `status` |
| `single_item_query` | 32 | `boots_how_1` … `shirt_other_4` (queries por produto × tipo × variante) |
| `storewide_query` | 16 | `membership_1` … `timing_4` (queries por tema × variante) |
| `subscription_inquiry` | 6 | `manage_dispute_bill`, `manage_extension`, `status_due_amount` |
| `troubleshoot_site` | 4 | `credit_card`, `search_results`, `shopping_cart`, `slow_speed` |

> Os 48 subflows de `single_item_query` + `storewide_query` são variantes paramétricas (produto × tema × número) com volume baixo por subflow. Os flows operacionais — `troubleshoot_site`, `order_issue`, `manage_account`, `account_access` — concentram a maior parte das conversas com fricção e são o foco da análise.

---

## Definições operacionais

| Termo | Definição |
|---|---|
| **Resolução** | Conversa termina sem escalação inesperada — `last_action ≠ "notify-team"`, exceto em `out_of_stock_general` (onde notificar o time é o desfecho esperado) |
| **Fricção** | Conversa contém `try-again` >=1x OU `verify-identity` >1x |
| **Padrão P1 (try-again loop)** | Solução genérica → falha → retry. Operacionalizado como `n_try_again >= 1` |
| **Padrão P2 (verify loop)** | `verify-identity` aparece >1x na mesma conversa |
| **Padrão P3 (escalação inesperada)** | `last_action == "notify-team"` e `subflow != "out_of_stock_general"` |
| **Padrão P4 (repetição de ação)** | Alguma ação tomada >=3x na conversa |
| **Padrão P5 (outlier de comprimento)** | `n_turns > média_subflow + 1,5 × desvio_subflow` |

---

## Limitações conhecidas

- **Wizard-of-Oz:** agentes são humanos treinados simulando um bot. Intervenções derivadas são redesenhos de fluxo, não ajustes de modelo de ML
- **Domínio:** e-commerce em inglês. VADER (treinado em reviews/redes sociais) é usado direcionalmente, não como score literal — ver `src/sentiment.py`
- **Sem metadados de usuário:** ausência de idade, histórico de compras, dispositivo, browser
- **Splits dev/test:** ~10% das conversas; usados como uma única base agregada nesta análise
- **Subflows paramétricos:** os 48 subflows de `single_item_query` + `storewide_query` têm volume baixo; conclusões sobre eles devem ser tratadas com cautela
