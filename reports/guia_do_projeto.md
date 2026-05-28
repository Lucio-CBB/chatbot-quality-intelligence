# Guia do Projeto — Chatbot Quality Intelligence
### Para quem quer entender tudo, do zero

---

## Antes de começar: o que é esse projeto?

Imagine que você tem uma loja online e um chatbot de atendimento — aquele robô que responde os clientes no chat. Você quer saber: **esse chatbot está funcionando bem ou mal?**

A resposta óbvia seria olhar a taxa de resolução: "quantos clientes tiveram o problema resolvido?". Se der 98%, parece ótimo. Mas esse número esconde muita coisa. É como avaliar um médico só pela taxa de alta hospitalar — não conta se o paciente ficou sofrendo desnecessariamente no meio do caminho.

Este projeto constrói uma forma mais inteligente de medir a qualidade do chatbot. Em vez de só saber *se* o problema foi resolvido, queremos saber *como* foi resolvido — e apontar exatamente onde o bot está falhando e o que fazer.

---

## Os Dados: de onde veio tudo isso?

Usamos um conjunto de dados público chamado **ABCD** (Action-Based Conversations Dataset), criado por uma empresa americana chamada ASAPP Research e publicado em 2021.

**O que tem nesse dataset?**
São **10.042 conversas reais de atendimento ao cliente** de uma loja de roupas online (fictícia). Cada conversa é entre um cliente e um atendente — como se fosse o WhatsApp da loja, mas em inglês.

**Por que é útil?**
Cada conversa vem com informações detalhadas:
- O **assunto** do atendimento (ex: "carrinho não atualiza", "cartão rejeitado", "rastrear pedido")
- **O que o atendente fez** a cada passo (ex: "buscou informação", "pediu para tentar de novo", "escalou para supervisor")
- **O que os dois lados disseram**, turno por turno

São 96 tipos diferentes de situações de atendimento. Chamamos cada tipo de **subfluxo** — pense como as "categorias de problema" que o chatbot sabe atender.

---

## Passo 1 — Exploração dos Dados (Notebook 01)

**O que fizemos:**
Antes de qualquer análise, precisávamos entender o que tínhamos nas mãos. É como receber uma caixa de papéis e primeiro organizar tudo antes de ler.

Fizemos perguntas básicas:
- Quantas conversas existem? **(10.042)**
- Quantos tipos de problema? **(96 subfluxos)**
- Em quantas conversas o problema foi resolvido?
- Existem conversas muito longas ou muito curtas?

**Uma decisão importante — o que é "resolvido"?**

O dataset não vem com um botão "resolvido/não resolvido". Tivemos que criar nossa própria definição. Decidimos assim:

> Uma conversa **não foi resolvida** quando o atendente precisou escalar o problema para outro time (`notify-team`) sem que isso fosse o desfecho esperado para aquele tipo de problema.

Também criamos o conceito de **fricção** — sinal de que a conversa foi difícil, mesmo que tenha se resolvido no final:

> Uma conversa tem **fricção** quando o atendente precisou pedir ao cliente para "tentar de novo" (`try-again`) ou quando verificou a identidade do cliente mais de uma vez.

**O que descobrimos:**
- Taxa de resolução geral: **98%** (parece ótimo!)
- Mas fricção geral: **9,2%** das conversas
- Um grupo específico de problemas, chamado `troubleshoot_site` (problemas técnicos no site), tinha **66% de fricção** — sete vezes acima da média

Isso é o primeiro sinal de problema: a maioria do chatbot vai bem, mas problemas técnicos do site são um pesadelo para o cliente.

---

## Passo 2 — Padrões de Falha (Notebook 02)

**O que fizemos:**
Agora que sabíamos *onde* o problema estava, queríamos entender *por que* estava acontecendo. Lemos as conversas de alto atrito para identificar o padrão.

**O que encontramos — o loop de tentativa-e-erro:**

Quase toda conversa do subfluxo `shopping_cart` (carrinho que não atualiza) seguia este roteiro:

```
Cliente:   "Meu carrinho não está atualizando"
Atendente: "Tente atualizar a página e adicionar o item novamente"
                [cliente tenta]
Cliente:   "Não funcionou"
Atendente: "Tente sair da conta e entrar de novo"
                [cliente tenta]
Cliente:   "Funcionou! Obrigado"
```

Isso acontecia em **84% das conversas** desse tipo. O atendente sempre ia direto para uma solução genérica sem antes perguntar qual era o problema real.

**A pergunta natural:** e se o atendente perguntasse primeiro "qual navegador você está usando?" antes de sugerir qualquer solução? Muitos problemas de carrinho são específicos de um navegador (Chrome, Firefox, Safari) — uma pergunta poderia direcionar a solução certa de imediato, sem tentativa-e-erro.

**O experimento natural que confirmou a hipótese:**

Outro subfluxo, o `credit_card` (cartão de crédito rejeitado), tinha uma variação natural interessante: alguns atendentes faziam perguntas diagnósticas antes de sugerir solução ("a data de validade está correta?", "você digitou errado algum número?"), e outros não faziam.

Comparamos os dois grupos:

| Grupo | Resolveu de 1ª tentativa | Turnos médios na conversa |
|---|---|---|
| Sem pergunta diagnóstica | **13%** | 20,8 |
| Com pergunta diagnóstica | **35%** | 18,7 |
| **Diferença** | **+22 pontos percentuais** | **-2,1 turnos** |

Isso não prova causa e efeito (não foi um experimento controlado), mas é uma evidência forte de que a pergunta diagnóstica ajuda.

---

## Passo 3 — Métricas de Sentimento (Notebook 03)

**O que fizemos:**
Até aqui medíamos fricção em termos de ações do atendente. Mas como o *cliente* estava se sentindo durante a conversa?

Usamos uma ferramenta chamada **VADER** — um programa que lê um texto e estima se ele é positivo, negativo ou neutro. É como se você pudesse medir o "tom" de cada mensagem do cliente, numa escala de -1 (muito negativo) a +1 (muito positivo).

**Exemplo de como funciona o VADER:**
- "Funcionou! Muito obrigado!" → score: +0,66 (positivo)
- "Não funcionou de jeito nenhum" → score: -0,34 (negativo)
- "Ok" → score: 0,00 (neutro)

Calculamos o sentimento de cada mensagem do cliente ao longo da conversa.

**O que descobrimos:**

**1. A trajetória de sentimento:**
Dividimos cada conversa em 5 partes (início, quarto 1, meio, quarto 3, fim) e medimos o sentimento médio em cada ponto.

Para conversas de `shopping_cart`:

| Posição | Sem tentativa-e-erro | Com tentativa-e-erro |
|---|---|---|
| Início | +0,028 | +0,077 |
| Q1 | +0,089 | +0,110 |
| **Meio** | **+0,134** | **+0,096** ← queda aqui |
| Q3 | +0,186 | +0,208 |
| Fim | **+0,265** | **+0,194** |

A queda no meio da conversa é exatamente o momento em que o cliente diz "não funcionou". O cliente chega animado, fica frustrado quando a primeira solução falha, e depois se recupera quando a segunda funciona — mas termina menos satisfeito do que aquele cujo problema foi resolvido de primeira.

**2. O impacto final:**
- Conversas sem tentativa-e-erro terminam com sentimento **+0,265**
- Conversas com tentativa-e-erro terminam com sentimento **+0,225**
- Essa diferença é estatisticamente significativa (p < 0,0001 — em português: é improvável que seja coincidência)

**Por que isso importa para o experimento:**
Esse número (+0,225) se torna o **guardrail** do nosso experimento futuro. Se tentarmos uma intervenção e ela piorar o sentimento do cliente abaixo desse valor, sabemos que a intervenção foi ruim — mesmo que resolva mais rápido.

---

## Passo 4 — Padrões Estruturais (Notebook 04)

**O que fizemos:**
Nos passos anteriores focamos em 2 subfluxos (`shopping_cart` e `credit_card`). Agora queríamos catalogar sistematicamente os problemas nos **96 subfluxos** do dataset.

Criamos uma taxonomia de 5 padrões de falha:

| Código | Nome | O que significa |
|---|---|---|
| P1 | Try-again loop | Atendente pediu para tentar de novo pelo menos 1 vez |
| P2 | Loop de verificação | Atendente pediu confirmação de identidade mais de 1 vez |
| P3 | Escalação inesperada | Problema passou para outro time quando não deveria |
| P4 | Repetição de ação | A mesma ação foi executada 3 ou mais vezes |
| P5 | Conversa longa demais | Durou muito mais que o normal para aquele tipo de problema |

Aplicamos esses 5 detectores em todas as 10.042 conversas.

**O que descobrimos:**

| Padrão | % das conversas afetadas |
|---|---|
| P1 — Try-again loop | 7,0% (704 conversas) |
| P5 — Conversa longa | 7,9% (792 conversas) |
| P2 — Loop de verificação | 2,3% (227 conversas) |
| P3 — Escalação | 2,0% (198 conversas) |
| P4 — Repetição | 1,6% (156 conversas) |
| **Qualquer padrão** | **17,7% (1.779 conversas)** |

**O achado mais importante:**
96% de todo o P1 (try-again loop) está concentrado em **um único flow**: `troubleshoot_site`. E dentro desse flow, os subfluxos `shopping_cart` e `credit_card` juntos respondem por 60% de todos os loops do dataset inteiro.

O problema não está espalhado — está concentrado. Isso é ótimo para quem precisa decidir onde agir primeiro.

---

## Passo 5 — Priorização ICE (Notebook 05)

**O que fizemos:**
Com vários subfluxos problemáticos identificados, como decidir qual atacar primeiro? Usamos um framework chamado **ICE** (Impact, Confidence, Ease — Impacto, Confiança, Facilidade).

A lógica é: não basta um problema ser grande. Ele também precisa ser bem entendido (confiança alta na causa) e ter uma solução viável (fácil de implementar). Um problema enorme mas difícil de resolver pode ser menos prioritário que um problema médio com solução simples.

**A fórmula:**
```
Score ICE = (Impacto × Confiança) ÷ Facilidade
```

Onde:
- **Impacto** = número de conversas afetadas × taxa de problema
- **Confiança** = quão claro é o padrão de falha (quanto mais dominante um único padrão, maior a confiança)
- **Facilidade** = quão difícil é implementar a solução (escala 1-10, onde 10 é o mais difícil)

**O resultado:**

| Rank | Subfluxo | Impacto | Confiança | Dificuldade | Score ICE |
|---|---|---|---|---|---|
| **#1** | **shopping_cart** | 213 | 99% | 2 (muito fácil) | **10.559** |
| #2 | credit_card | 217 | 96% | 3 (fácil) | 6.969 |
| #3 | slow_speed | 184 | 94% | 5 (médio) | 3.441 |
| #4 | search_results | 105 | 81% | 6 (médio) | 1.416 |

**Por que `shopping_cart` ganhou?**

- **Impacto:** 84,9% das 251 conversas têm o problema — maior taxa do dataset inteiro
- **Confiança 99%:** quase toda conversa problemática tem um único padrão (P1: try-again). Não é ambíguo — sabemos exatamente o que está errado
- **Dificuldade 2/10:** a solução proposta é adicionar **1 pergunta** no início da conversa. Não é uma mudança de tecnologia, é uma mudança de roteiro

E o mais importante: mesmo que a gente errasse na estimativa de dificuldade (digamos que fosse 5 em vez de 2), `shopping_cart` ainda seria #1 no ranking. A decisão é robusta.

---

## O Experimento A/B — A Peça Central do Projeto

**O que é um experimento A/B?**

Imagine que você tem uma loja física e quer saber se trocar a vitrine atrai mais clientes. Você poderia fazer a mudança e ver se as vendas aumentam — mas talvez as vendas aumentassem de qualquer jeito por causa de outra coisa (feriado, promoção, etc.).

A solução é dividir os clientes em dois grupos aleatórios: metade vê a vitrine antiga (Grupo A, o Controle), metade vê a vitrine nova (Grupo B, a Variante). Se o Grupo B comprar mais, a vitrine nova foi o motivo — porque tudo o mais era igual.

Em chatbots funciona igual: alguns clientes recebem o fluxo atual, outros recebem o fluxo com a pergunta diagnóstica. Comparamos os resultados.

**O experimento que desenhamos:**

| | Grupo A (Controle) | Grupo B (Variante) |
|---|---|---|
| O que recebe | Fluxo atual — solução genérica imediata | Fluxo novo — 1 pergunta diagnóstica antes |
| Exemplo de abertura | "Tente atualizar a página" | "Qual navegador você está usando?" |

**A hipótese:**
> Se o bot perguntar "qual navegador você usa?" antes de sugerir qualquer solução, mais clientes vão resolver o problema na primeira tentativa — porque a solução vai ser direcionada ao problema real deles, não uma tentativa no escuro.

**Quanto tempo e quantos clientes precisamos?**

Isso é calculado com estatística. A lógica é: quanto maior o efeito que esperamos ver, menos clientes precisamos para ter certeza de que o resultado não é coincidência.

No nosso caso:
- Hoje: 16% das conversas resolvem de primeira (sem tentativa-e-erro)
- Meta: 30% (uma melhoria de 14 pontos percentuais)
- Resultado: precisamos de **141 conversas por grupo** (282 no total)
- Com o volume histórico do dataset: isso levaria **~9 semanas**

**Como vamos decidir se funcionou?**

Definimos a regra **antes** de ver os resultados (isso é crucial — se você olhar o resultado primeiro e depois decidir como interpretar, pode se enganar):

| Resultado | Decisão |
|---|---|
| Melhora ≥ 14pp e o intervalo de confiança não inclui zero | **Implementar** — a pergunta diagnóstica vai para 100% dos clientes |
| Melhora pequena mas inconclusiva | **Iterar** — ajustar a pergunta e testar de novo |
| Piora ou sentimento do cliente piorou | **Descartar** — o diagnóstico não ajudou, investigar por quê |

---

## Resumo de Todos os Resultados

| O que medimos | Resultado |
|---|---|
| Conversas analisadas | 10.042 |
| Subfluxos mapeados | 96 |
| Taxa de resolução geral | 98% |
| Taxa de fricção geral | 9,2% |
| Fricção em `troubleshoot_site` | **66%** (7x acima da média) |
| Fricção em `shopping_cart` | **84%** |
| Resolve de 1ª tentativa (hoje) | **16%** |
| Efeito do diagnóstico (evidência do credit_card) | **+22pp** de resolução |
| Queda de sentimento com fricção | -0,040 (estatisticamente significativa) |
| Subfluxo #1 do ICE | **shopping_cart** (score 100/100) |
| Clientes necessários para o teste | 282 (141 por grupo) |
| Duração estimada do teste | ~9 semanas |

---

## O Que Torna Este Projeto Diferente

A maioria das análises de chatbot para no diagnóstico. Alguém faz um dashboard, mostra que `troubleshoot_site` está ruim, e para por aí. A equipe olha, concorda que é ruim, e não sabe o que fazer.

Este projeto vai além em três passos extras:

**1. Do diagnóstico ao mecanismo**
Não dissemos só "shopping_cart tem 84% de fricção". Explicamos *por que*: o atendente nunca pergunta a causa antes de sugerir solução. Isso transforma o achado em ação.

**2. Da intuição à prioridade defensável**
Em vez de "vamos atacar o maior problema", usamos o ICE para mostrar que `shopping_cart` é #1 por três razões independentes (impacto, confiança, facilidade) — e que o resultado é robusto mesmo se errarmos nas premissas.

**3. Da análise ao experimento**
Em vez de implementar direto e torcer para funcionar, desenhamos um teste que vai nos dizer com confiança estatística se a mudança funciona — e definimos de antemão o que "funciona" significa.

Esse arco completo (problema → mecanismo → prioridade → experimento → regra de decisão) é a diferença entre uma análise descritiva e uma análise que gera decisões de produto.

---

## Glossário Rápido

| Termo | O que significa |
|---|---|
| **Subfluxo** | Um tipo específico de problema de atendimento (ex: "carrinho não atualiza") |
| **Fricção** | Quando a conversa teve dificuldade desnecessária, mesmo que resolvida |
| **Try-again** | Quando o atendente pediu para o cliente tentar de novo |
| **Sentimento (VADER)** | Medida de tom positivo/negativo do texto (-1 a +1) |
| **ICE** | Framework de priorização: Impacto × Confiança ÷ Dificuldade |
| **A/B test** | Experimento com dois grupos aleatórios para comparar duas versões |
| **MDE** | Mínima Diferença Detectável — o menor efeito que vale detectar |
| **Guardrail** | Limite mínimo aceitável de uma métrica secundária — impede que a melhora num ponto piore outro |
| **Intervalo de confiança** | Faixa de valores prováveis para o efeito real (95% IC = 95% de certeza que o valor verdadeiro está nessa faixa) |
| **p-valor** | Probabilidade de ver o resultado por coincidência — quanto menor, mais confiança |
