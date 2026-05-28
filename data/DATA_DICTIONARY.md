# Data Dictionary — ABCD Dataset

## Fonte
ASAPP Research — Action-Based Conversations Dataset (2021)
Artigo: "ABCD: A Dataset for Agent Behavior in Customer Dialogs" (ACL-IJCNLP 2021)

## Arquivos em `data/raw/`
| Arquivo | Descrição |
|---|---|
| `abcd_v1.1.json` | Dataset completo com splits train/dev/test |

## Estrutura de uma conversa

```json
{
  "convo_id": "...",
  "split": "train | dev | test",
  "original": [...],       // turnos brutos da conversa
  "delexed": [...],        // versão com PII substituído por placeholders
  "scene": {
    "subflow": "...",      // sub-fluxo (55 possíveis, ex: track_order)
    "flow": "...",         // fluxo pai (ex: order_issue)
    "kb": {...}            // item da base de conhecimento consultado
  },
  "targets": {
    "nextstep": [...],     // próxima ação esperada por turno
    "action": [...],       // ação tomada
    "value": [...]         // parâmetro da ação
  }
}
```

## Campos principais após processamento (`data/processed/`)

| Campo | Tipo | Descrição |
|---|---|---|
| `convo_id` | string | Identificador único da conversa |
| `split` | string | train / dev / test |
| `flow` | string | Fluxo pai (12 fluxos) |
| `subflow` | string | Sub-fluxo (55 categorias) |
| `n_turns` | int | Número total de turnos |
| `n_turns_customer` | int | Turnos do cliente |
| `n_turns_agent` | int | Turnos do agente |
| `resolution` | int | 1 = resolvido, 0 = não resolvido |
| `has_loop` | bool | Padrão de loop detectado (mesma pergunta repetida) |
| `has_kb_miss` | bool | Agente tentou consultar KB e não encontrou |
| `first_action_turn` | int | Turno em que a primeira ação concreta foi tomada |
| `sentiment_opening` | float | Sentimento do primeiro turno do cliente (-1 a 1) |
| `sentiment_closing` | float | Sentimento do último turno do cliente (-1 a 1) |
| `sentiment_delta` | float | Diferença closing − opening |

## Flows e Subflows

Os 55 sub-fluxos estão organizados em 12 fluxos pai:

- `account` → manage_account, verify_identity, ...
- `order` → track_order, cancel_order, modify_order, ...
- `shipping` → update_address, change_shipping, ...
- `refund` → refund_request, return_item, ...
- `product` → product_question, product_defect, ...
- (e outros)

## Limitações conhecidas
- Dataset de atendimento e-commerce (não WhatsApp)
- Agentes são humanos, não um bot real — intervenções são simuladas
- ~10% das conversas são no split dev/test (sem rótulo público completo)
- Ausência de metadados de usuário (idade, histórico de compras)
