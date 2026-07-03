# Dicionário de termos - Escalonamento de Tempo Real

Referência rápida dos conceitos usados no `main.py`. Os mesmos termos aparecem no
programa pela opção `D` do menu.

## Modelo de tarefas

| Termo | O que é |
|---|---|
| **Tarefa** | Trabalho periódico que libera um job a cada período `T`. No código: `class Tarefa`. |
| **Job** | Uma instância concreta de uma tarefa. `T2.1` é o 1º job de `T2`. No código: `class Job`. |
| **C (WCET)** | *Worst-Case Execution Time*: quanto de CPU o job pede no pior caso. |
| **T (período)** | Intervalo entre duas liberações da mesma tarefa. |
| **D (deadline relativo)** | Prazo após a liberação para o job terminar. Usamos `D = T` (deadline implícito). |
| **Fase** | Instante da primeira liberação (aqui sempre 0). |
| **Deadline absoluto** | `liberação + D`: o instante-limite real daquele job. É a chave do EDF. |

## Métricas

| Termo | O que é |
|---|---|
| **Utilização `U`** | Soma de `C/T` de todas as tarefas. Fração da CPU exigida. `U > 1` é impossível de escalonar. |
| **Hiperperíodo** | MMC dos períodos. Simular um hiperperíodo basta para ver todo o padrão de execução. |
| **Limite de Liu & Layland** | Se `U <= n(2^(1/n) - 1)`, o RM **garante** cumprir (teste suficiente). Tende a `ln 2 ≈ 0,693`. |
| **Teste do EDF** | Com deadline implícito, `U <= 1` **se e somente se** é escalonável (teste exato). |

## Simulação a eventos discretos

| Termo | O que é |
|---|---|
| **Evento discreto** | O relógio salta direto para o próximo instante em que algo muda, nunca de 1 em 1. |
| **LIBERACAO_JOB** | Evento: uma tarefa cria um novo job (entra na fila de prontos). |
| **TERMINO_JOB** | Evento: marca quando o job ativo terminaria de executar. |
| **Fila de prontos** | Jobs já liberados esperando (ou usando) a CPU. No código: `fila_prontos`. |
| **Preempção** | Um job de maior prioridade toma a CPU de quem estava rodando. Surge sozinha na simulação. |
| **Deadline miss (perda)** | O job não terminou até o deadline. Observação derivada, não comanda o escalonador. |

## Algoritmos (cada um é só uma chave de prioridade: menor chave = maior prioridade)

| Sigla | Nome | Prioridade | Chave |
|---|---|---|---|
| **RM** | Rate Monotonic | estática | menor **período** `T` |
| **DM** | Deadline Monotonic | estática | menor **deadline relativo** `D` |
| **EDF** | Earliest Deadline First | dinâmica | menor **deadline absoluto** |

RM e DM decidem a prioridade uma vez (fixa). EDF reavalia a cada instante (dinâmica),
por isso alcança 100% de utilização enquanto a prioridade fixa trava perto de 69%.
