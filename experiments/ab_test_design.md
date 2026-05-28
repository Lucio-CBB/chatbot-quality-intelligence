# Experiment Brief — A/B Test: shopping_cart Diagnostic-First

**Subflow alvo:** `shopping_cart` (flow: `troubleshoot_site`)  
**ICE Score:** 10.559 / 10.559 (normalizado: 100/100 — #1 do ranking)  
**Status:** Design finalizado — pronto para implementação

---

## 1. Contexto e Motivação

O pipeline de diagnóstico identificou que **84,9% das conversas** do subflow `shopping_cart`
contêm o padrão P1 (try-again loop): o agente sugere uma solução genérica ("atualize a página e tente novamente")
sem antes investigar a causa, o cliente tenta, falha, e o agente sugere uma segunda solução.

Esse loop ocorre em 211 das 251 conversas do subflow — com 0% de variação no padrão dominante
(Confidence = 99%).

**Evidência de suporte (experimento natural em `credit_card`):**  
O subflow `credit_card` tem variação natural de comportamento: 37% dos agentes fazem
1–2 perguntas diagnósticas antes de sugerir solução. Esse grupo tem:
- Resolução de 1ª tentativa: **35%** vs **13%** sem diagnóstico (+22pp)
- Turnos médios: **18,7** vs **20,8** (-2,1 turnos)

Essa evidência, embora não randomizada, sustenta a hipótese de que diagnóstico antes de solução
reduz ciclos de retry também em `shopping_cart`.

---

## 2. Hipótese Testável

> **Se** o bot adicionar 1 pergunta diagnóstica antes de sugerir qualquer solução em `shopping_cart`  
> **então** a proporção de conversas sem ciclo try-again (resolução de 1ª tentativa) subirá de **16%** para **≥30%**  
> **porque** muitas falhas de carrinho são browser-específicas; uma pergunta direciona a solução correta imediatamente, eliminando o ciclo de tentativa-e-erro.

---

## 3. Intervenção

| | Controle (A) | Variante (B) |
|---|---|---|
| **Turno de abertura** | "Como posso ajudar?" | "Como posso ajudar?" |
| **Após cliente descrever o problema** | Imediatamente: "Por favor, atualize a página e tente adicionar novamente" | **Antes de sugerir:** "Qual navegador você está usando? Já tentou limpar o cache do navegador?" |
| **Sequência de ação** | `try-again` → `log-out-in` | Diagnóstico → solução direcionada → (sem try-again, idealmente) |
| **Mudança de implementação** | — | 1 turno adicional com pergunta diagnóstica; solução condicional ao browser reportado |

**Nota:** a pergunta diagnóstica deve ser natural, não burocratica. Exemplo de formulação da variante:
> "Entendo! Antes de tentar algumas soluções, você consegue me dizer qual navegador está usando? Chrome, Firefox, Safari...?"

---

## 4. Unidade de Randomização

**Unidade:** conversa/sessão (session-level randomization)

**Justificativa:** o subflow `shopping_cart` é tipicamente acionado por usuários anônimos
ou sessões independentes. Não há evidência de que o mesmo usuário retorne com o mesmo
problema dentro de uma janela de teste razoável (< 4 semanas). Risco de contaminação: baixo.

**Implementação:** hash do `session_id` mod 2 → braço A ou B.

---

## 5. Métricas

| Tipo | Métrica | Definição | Direção desejada |
|---|---|---|---|
| **Primária** | Resolução de 1ª tentativa | % conversas com `n_try_again = 0` | ↑ de 16% para ≥30% |
| Secundária | Número de turnos | Média de turnos por conversa | ↓ |
| Secundária | Sentimento closing | VADER compound score médio no fechamento | ↑ de +0,225 |
| **Guardrail** | Sentimento closing (floor) | Closing da variante ≥ baseline do controle | ≥ +0,196 (IC 95% lower bound) |
| **Guardrail** | Taxa de resolução geral | % conversas com `resolution = 1` | Não degradar (<98%) |

---

## 6. Cálculo de Tamanho de Amostra e Poder

**Parâmetros:**
- α = 0,05 (dois lados), poder = 80%
- z_α/2 = 1,96 ; z_β = 0,84
- p̄ (baseline) = 0,16 (resolução de 1ª tentativa atual)
- p_B (target)  = 0,30 (hipótese conservadora — 80% do efeito observado no credit_card)
- MDE (δ)       = 0,30 − 0,16 = **0,14** (14 pp)
- p̄_pooled      = (0,16 + 0,30) / 2 = 0,23

**Fórmula:**

    n ≈ 2 · (z_α/2 + z_β)² · p̄(1−p̄) / δ²
    n ≈ 2 · (1,96 + 0,84)² · 0,23 · 0,77 / 0,14²
    n ≈ 2 · 7,84 · 0,177 / 0,0196
    n ≈ **141 conversas por braço**

**Volume histórico:** ~251 conversas no dataset de treino (estimativa: ~32 conv/semana em produção)

**Duração estimada:** 141 conv/braço ÷ 32 conv/semana = **~4,4 semanas por braço → ~9 semanas total**

| Parâmetro | Valor |
|---|---|
| n por braço | **141** |
| Total de conversas necessárias | **282** |
| Volume semanal estimado | ~32 conv/semana |
| Duração estimada | **~9 semanas** |

---

## 7. Plano de Análise

**Teste estatístico:**
- Métrica primária (proporção): teste z de duas proporções, dois lados
- Métricas secundárias (turnos, sentimento): Mann-Whitney U (distribuições não-normais)

**Leitura de resultados:**
- Reportar **intervalo de confiança de 95%**, não apenas p-valor
- Interpretar: "o efeito estimado é [IC_low, IC_high] pp — compatível ou não com o MDE?"

**Análise por segmento (heterogeneidade de efeito):**
- Por dia da semana (sazonalidade intra-semana)
- Por duração da sessão (clientes que já tentaram antes de entrar no chat)
- Por dispositivo/browser, se disponível no log

**Data de leitura:** definida no dia 0 do teste — **sem early stopping**.

---

## 8. Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|---|---|---|
| **Efeito novidade** — clientes respondem diferente só por ser novo | Média | Excluir primeira semana de dados (warm-up period) |
| **Peeking** — olhar resultados antes do prazo e interromper cedo | Alta | Dashboard bloqueado até data de leitura definida |
| **Sazonalidade** — volume diferente entre dias/semanas | Baixa | Randomização garante que A e B recebem mesmo mix temporal |
| **Contaminação** — usuário experimenta ambos os braços | Baixa | Randomização por sessão; mesma sessão sempre cai no mesmo braço |
| **Pergunta diagnóstica aumenta abandono** | Média | Guardrail de sentimento closing detecta isso antes de ship |

---

## 9. Regra de Decisão (definida antes dos dados)

| Resultado | Decisão |
|---|---|
| Δ ≥ 14pp E IC 95% não toca zero E guardrails OK | **Ship** — implementar variante B em 100% do tráfego |
| 0 < Δ < 14pp E IC toca zero (inconclusivo) | **Iterar** — refinar a pergunta diagnóstica, re-testar com novo design |
| Δ ≤ 0 OU guardrail de sentimento violado | **Kill** — descartar variante B; investigar por que o diagnóstico não ajudou |

**Nota de integridade:** esta regra de decisão foi escrita **antes** de qualquer coleta de dados do experimento.
Alterações post-hoc requerem aprovação explícita e devem ser documentadas com justificativa.

---

## Apêndice: Números de Referência

| Indicador | Valor |
|---|---|
| Conversas `shopping_cart` no dataset | 251 |
| Taxa try-again (baseline) | 84,1% |
| Resolução de 1ª tentativa (baseline) | 15,9% |
| Sentimento closing (controle) | +0,225 (IC 95%: [+0,196, +0,255]) |
| ICE Score (normalizado) | 100/100 — #1 do ranking |
| Evidência de suporte | Experimento natural em `credit_card`: +22pp com diagnóstico |
