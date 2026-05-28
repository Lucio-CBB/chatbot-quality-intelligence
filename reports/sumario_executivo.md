# Sumário Executivo — Chatbot Quality Intelligence

**Autor:** Wital  
**Dataset:** ABCD (ASAPP Research, 2021) — 10.042 conversas de atendimento ao cliente  
**Objetivo do projeto:** demonstrar o arco completo de um Product Analyst: diagnóstico → priorização → experimento A/B

---

## O Problema

Métricas agregadas de chatbot escondem falhas estruturais. Uma taxa de resolução de 98% pode coexistir com 84% das conversas de um sub-fluxo crítico passando por um loop desnecessário de tentativa-e-erro — e ninguém sabe onde intervir.

---

## O Que Foi Feito

Construí um pipeline de 5 etapas que transforma logs de conversa em decisão de produto:

**1. Diagnóstico de Fricção**  
Identifiquei que o flow `troubleshoot_site` concentra 7× mais fricção que a média global (66% vs. 9%). Dentro desse flow, o sub-fluxo `shopping_cart` tem 84% de conversas com loop de trial-and-error — o agente sugere solução genérica sem antes perguntar a causa.

**2. Análise de Mecanismo**  
Usei o sub-fluxo `credit_card` como experimento natural: agentes que fazem 1 pergunta diagnóstica antes de sugerir solução têm +22pp de resolução de 1ª tentativa e -2,1 turnos por conversa, comparado a agentes que não fazem.

**3. Impacto na Experiência**  
Medição de sentimento VADER mostra que conversas com loop fecham com sentimento significativamente mais baixo (+0,225 vs. +0,265, p < 0,0001). O "dip" de sentimento é detectável exatamente no turno em que a primeira solução falha.

**4. Priorização ICE**  
Apliquei ICE scoring em 96 sub-fluxos. `shopping_cart` ficou em #1 com folga de 52% sobre o segundo colocado — maior taxa de padrão (85%), Confidence quase perfeita (99%), intervenção mais simples do ranking (Ease=2: adicionar 1 pergunta).

**5. Design de Experimento A/B**  
Escrevi o experiment brief completo antes de qualquer dado de produção:

---

## O Experimento

| | Controle (A) | Variante (B) |
|---|---|---|
| **Fluxo** | Solução genérica imediata | 1 pergunta diagnóstica antes da solução |
| **Exemplo** | "Atualize a página e tente novamente" | "Qual navegador você usa? Já limpou o cache?" |

| Parâmetro | Valor |
|---|---|
| Métrica primária | % conversas sem retry (resolução de 1ª tentativa) |
| Baseline | 15,9% |
| Target (MDE) | 30% (+14pp) |
| n por braço | 141 conversas |
| Duração estimada | ~9 semanas |
| Guardrail | Closing sentiment ≥ +0,196 |

**Regra de decisão (escrita antes dos dados):**
- Δ ≥ 14pp e IC não toca zero → **Ship**
- Inconclusivo → **Iterar**
- Δ ≤ 0 ou guardrail violado → **Kill**

---

## Resultados-Chave

| Achado | Número |
|---|---|
| Conversas analisadas | 10.042 |
| Sub-fluxos mapeados | 96 |
| Taxa de fricção em shopping_cart | **84%** |
| Efeito do diagnóstico (experimento natural) | **+22pp** resolução de 1ª tentativa |
| Diferença de sentimento closing (com vs. sem loop) | **-0,040** (p < 0,0001) |
| ICE score normalizado do alvo | **100/100** — #1 do ranking |

---

## Por Que Este Projeto é Diferente

A maioria dos projetos de portfólio para de análise. Este não para:

```
Diagnóstico  →  Mecanismo  →  Priorização defensável  →  Experimento A/B  →  Regra de decisão
   (nb01-02)      (nb02-03)         (nb04-05)              (ab_test_design)
```

O ICE scoring torna a escolha do alvo auditável — não "escolhi o mais interessante", mas "cheguei aqui via ranking com critérios explicitados". O experiment brief com regra de decisão pré-definida é o que separa análise de decisão de produto.

---

## Stack

Python 3.13 · pandas · scipy · NLTK (VADER) · matplotlib/seaborn · Jupyter
