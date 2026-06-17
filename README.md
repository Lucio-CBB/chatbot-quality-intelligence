# Chatbot Quality Intelligence

Pipeline de diagnóstico de qualidade de chatbot com design de experimento A/B — peça de portfólio para vagas de **Product Analyst / APM**.

---

## TL;DR

- **Dataset:** ABCD (ASAPP Research) — 10.042 conversas reais de atendimento ao cliente, 96 sub-fluxos
- **Problema encontrado:** 84% das conversas do sub-fluxo `shopping_cart` seguem um loop de trial-and-error sem diagnóstico — o agente sugere solução genérica, o cliente tenta, falha, e o ciclo se repete
- **Evidência de causa:** experimento natural em `credit_card` mostra +22pp de resolução de 1ª tentativa quando o agente faz 1 pergunta diagnóstica antes de sugerir solução
- **Priorização:** ICE scoring em 96 sub-fluxos coloca `shopping_cart` em #1 com folga de 52% sobre o 2º colocado
- **Ação:** experimento A/B desenhado com hipótese testável, cálculo de poder (n=141/braço, ~9 semanas) e regra de decisão ship/iterar/kill definida antes dos dados

---

## 1. O Problema

Chatbots de atendimento são avaliados por métricas agregadas — taxa de resolução geral, NPS, CSAT. Esses números escondem variação enorme entre sub-fluxos e, mais importante, escondem o **mecanismo** da falha.

Um bot com 98% de resolução geral pode ter 84% das conversas de um sub-fluxo específico passando por um loop desnecessário de tentativa-e-erro. O cliente resolve, mas com fricção — e essa fricção tem custo mensurável em sentimento de fechamento (closing sentiment -0,071 nas conversas com loop vs. sem loop).

O objetivo deste projeto é construir o pipeline que vai **da métrica agregada ao mecanismo de falha** — e desse mecanismo a um experimento A/B defensável.

---

## 2. Os Dados

**ABCD — Action-Based Conversations Dataset** (ASAPP Research, ACL-IJCNLP 2021)

| Atributo | Valor |
|---|---|
| Total de conversas | 10.042 |
| Sub-fluxos únicos | 96 |
| Flows pai | 10 |
| Domínio | Atendimento ao cliente — e-commerce |
| Rótulo de resolução | Derivado por regra (ver `data/DATA_DICTIONARY.md`) |
| Tamanho do arquivo raw | 121 MB |

**Limitação importante:** o ABCD é um dataset Wizard-of-Oz (agentes humanos treinados simulando um bot). As intervenções são portanto projetadas como mudanças de fluxo, não como ajustes de um modelo de ML existente. Isso é explicitado nas Limitações.

Ver [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md) para estrutura completa dos campos.

---

## 3. Metodologia

```
EDA → Padrões de Falha → Métricas → Padrões Estruturais → ICE → A/B Design
```

O pipeline tem 5 etapas, cada uma com notebook dedicado:

| Etapa | Notebook | Por quê esta etapa existe |
|---|---|---|
| EDA | `01_exploracao` | Entender volume, distribuição e taxa de fricção antes de qualquer hipótese |
| Padrões de Falha | `02_padroes_falha` | Identificar o **mecanismo** da fricção, não só o número |
| Métricas de Sentimento | `03_metricas_sentimento` | Quantificar o impacto na experiência e definir o guardrail do A/B |
| Padrões Estruturais | `04_padroes_estruturais` | Catalogar sistematicamente os 5 modos de falha em todos os 96 sub-fluxos |
| ICE Scoring | `05_priorizacao_ice` | Priorizar de forma defensável — não "escolher o mais bonito" |

**Definições operacionais:**

- **Resolução** = 1 quando a conversa termina sem escalação inesperada (última ação ≠ `notify-team`, exceto em `out_of_stock_general`)
- **Fricção** = conversa contém `try-again` OU `verify-identity` repetido >1x
- **Padrão P1 (try-again loop)** = principal modo de falha: solução genérica → falha → retry

---

## 4. Principais Achados

### 4.1 O sinal está concentrado

O flow `troubleshoot_site` tem **taxa de fricção 7x acima da média global**:

| Flow | Conversas | Fricção | Resolução |
|---|---|---|---|
| troubleshoot_site | 1.026 | **66,2%** | 95,0% |
| Média dos demais | ~900 | **9,4%** | 98,9% |

### 4.2 O mecanismo: trial-and-error sem diagnóstico

Em `shopping_cart`, **84,1% das 251 conversas** seguem este script:

```
Cliente:  "meu carrinho não atualiza"
Agente:   "atualize a página e tente novamente"    ← solução genérica imediata
           [ação: try-again]
Cliente:  "não funcionou"
Agente:   "tente sair e entrar na conta"           ← segunda tentativa
           [ação: log-out-in]
Cliente:  "funcionou, obrigado!"
```

Apenas **3% das conversas** têm alguma pergunta diagnóstica antes da primeira sugestão.

### 4.3 Evidência causal: o experimento natural do credit_card

O sub-fluxo `credit_card` tem variação natural de comportamento: 37% dos agentes fazem perguntas diagnósticas (validade do cartão? digitou errado?), 63% não fazem.

| Grupo | n | Resolve de 1ª | Try-again médio | Turnos médios |
|---|---|---|---|---|
| Sem diagnóstico | 167 | 13% | 0,90 | 20,8 |
| Com diagnóstico | 99 | **35%** | **0,65** | **18,7** |
| **Diferença** | | **+22pp** | **-0,25** | **-2,1** |

### 4.4 Impacto no sentimento do cliente

Conversas com loop de try-again têm **sentimento de fechamento significativamente mais baixo** (Mann-Whitney p < 0,0001):

| Grupo | Sentimento opening | Sentimento closing | Δ |
|---|---|---|---|
| Sem fricção | +0,088 | +0,255 | +0,167 |
| Com fricção | +0,049 | +0,220 | +0,171 |

Em `shopping_cart` especificamente, conversas sem try-again fecham em **+0,265** vs **+0,225** com try-again — e há um "dip" detectável no meio da conversa, exatamente quando a primeira solução falha.

### 4.5 ICE Ranking — os 4 candidatos a experimento

| Rank | Sub-fluxo | Impact | Confidence | Ease | ICE (norm.) |
|---|---|---|---|---|---|
| **#1** | **shopping_cart** | 213 | 99% | 2 | **100** |
| #2 | credit_card | 217 | 96% | 3 | 66 |
| #3 | slow_speed | 184 | 94% | 5 | 33 |
| #4 | search_results | 105 | 81% | 6 | 13 |

`shopping_cart` vence por combinação: maior Confidence (99% — um único padrão dominante), menor Ease (2 — adicionar 1 pergunta). O ranking é robusto: `shopping_cart` permanece #1 para qualquer premissa de Ease ≤ 5 na análise de sensibilidade.

---

## 5. Do Insight à Ação: Design de Experimento A/B

Ver o brief completo em [`experiments/ab_test_design.md`](experiments/ab_test_design.md).

**Hipótese:**
> Se o bot adicionar 1 pergunta diagnóstica antes de sugerir qualquer solução em `shopping_cart`, então a proporção de conversas sem ciclo try-again subirá de 16% para ≥30%, porque muitas falhas de carrinho são browser-específicas — uma pergunta direciona a solução correta imediatamente.

**Design:**

| | Controle (A) | Variante (B) |
|---|---|---|
| Após cliente descrever o problema | "Atualize a página e tente novamente" | "Qual navegador você está usando? Já tentou limpar o cache?" |
| Padrão esperado | try-again → log-out-in | Solução direcionada → (sem retry) |

**Parâmetros do teste:**

| Parâmetro | Valor |
|---|---|
| Métrica primária | % conversas com 0 try-again (resolução de 1ª tentativa) |
| Baseline | 15,9% |
| MDE | 14pp (target: 30%) |
| n por braço | **141 conversas** |
| Duração estimada | **~9 semanas** |
| Guardrail | Closing sentiment ≥ +0,196 (IC 95% lower bound do controle) |

**Regra de decisão (definida antes dos dados):**

| Resultado | Decisão |
|---|---|
| Δ ≥ 14pp, IC não toca zero, guardrail OK | **Ship** |
| 0 < Δ < 14pp, IC toca zero | **Iterar** |
| Δ ≤ 0 ou guardrail violado | **Kill** |

---

## 6. Impacto Projetado

Assumindo que o efeito observado no experimento natural de `credit_card` (+22pp) se replica com 80% de magnitude em `shopping_cart`:

- **Resolução de 1ª tentativa:** 16% → 30% (+14pp)
- **Turnos por conversa:** redução de ~2 turnos em 84% das conversas
- **Conversas sem fricção desnecessária:** de 40 para ~75 por semana (estimativa de produção)
- **Sentimento de fechamento:** sobe de +0,225 para próximo de +0,265

Backlog natural após `shopping_cart`: `credit_card` (#2), `slow_speed` (#3).

---

## 7. Stack e Reprodutibilidade

```bash
git clone https://github.com/Lucio-CBB/chatbot-quality-intelligence
cd chatbot-quality-intelligence
pip install -r requirements.txt
jupyter notebook
```

O dataset é baixado automaticamente no notebook 01 (célula de download).

**Stack:** Python 3.13, pandas, numpy, matplotlib, seaborn, scipy, NLTK (VADER), Jupyter

**Desenvolvido com auxílio de [Claude](https://claude.ai) (Anthropic)** para estruturação da análise, documentação e revisão de código.

---

## 8. Limitações e Próximos Passos

**Limitações:**
- Dataset Wizard-of-Oz: agentes são humanos simulando um bot. As intervenções são redesenhos de fluxo, não ajustes de ML
- Domínio e-commerce: o pipeline é agnóstico de domínio — o mesmo framework foi aplicado em atendimento WhatsApp no contexto profissional
- VADER treinado em reviews/redes sociais: scores de sentimento são usados de forma direcional, não literal
- Experimento natural de `credit_card` não é randomizado: evidência de suporte, não prova causal

**Próximos passos:**
1. Implementar o A/B em produção com um bot live
2. Após `shopping_cart`: replicar intervenção em `credit_card` (mesmo padrão, Ease=3)
3. Redesenho de fluxo diagnóstico para `slow_speed` (multi-causa: browser, rede, device)
4. Automatizar a detecção de padrões como monitor contínuo de qualidade
