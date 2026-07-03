# Roteiro de apresentação (10 min) - foco no código

**Trabalho:** Simulador de escalonamento de tempo real por eventos discretos
**Dupla:** Luis Sena e Antoniel Magalhães
**Formato:** apresentamos o arquivo `main.py` na tela, seção por seção, e rodamos a demo ao vivo.

**Antes de começar (deixar pronto):**
- `main.py` aberto no editor, com o minimapa/índice de seções à vista.
- Terminal na pasta `apresentacao/`, com este comando já digitado: `uv run main.py`
- Timing à direita de cada bloco. Total ~10 min.

---

## 0. Abertura (40s)
"Boa tarde. Eu sou o Luis, esse é o Antoniel. A gente construiu um simulador de escalonamento de tarefas de tempo real. Em vez de slides cheios de teoria, vamos mostrar o código rodando: um arquivo Python só, que simula evento a evento e desenha o resultado num diagrama de Gantt. No fim vocês veem, no mesmo gráfico, quando um algoritmo cumpre e quando ele perde um prazo."

## 1. O problema, em uma frase (40s)
"Em tempo real, resultado certo atrasado é resultado errado. A correção depende do tempo. A pergunta central do trabalho é: dado um conjunto de tarefas periódicas, dá para rodar tudo sem perder nenhum deadline? A gente responde de duas formas, teste no papel e simulação, e o código faz as duas."

## 2. Seção 1 do código: o modelo (1min)
*(mostrar `class Tarefa` e `class Job`)*
"Toda a carga é descrita por duas estruturas. A `Tarefa` tem três números: `C`, o tempo de CPU no pior caso; `T`, o período, de quanto em quanto tempo ela libera trabalho; e `D`, o deadline. A propriedade `utilizacao` já devolve `C` sobre `T`, a fração de CPU que ela pede."
"O `Job` é uma instância concreta dessa tarefa. Guarda o `tempo_restante` de CPU e o `deadline` absoluto, que é a liberação mais `D`. Esse deadline absoluto vai ser a chave do EDF daqui a pouco."

## 3. Seção 2: cenários prontos (30s)
*(mostrar o dicionário `CENARIOS`)*
"A gente deixou três cargas embutidas para a demo: uma que todo mundo cumpre, o caso clássico onde o RM falha e o EDF salva, e uma de sobrecarga onde ninguém escapa. É só escolher no menu."

## 4. Seção 3: as políticas de prioridade (1min)
*(mostrar `prioridade_rm`, `prioridade_dm`, `prioridade_edf`)*
"Aqui está a ideia mais bonita do trabalho. Cada algoritmo é só uma função que devolve uma chave, e a regra é: menor chave, maior prioridade."
"O RM ordena pelo período. O DM, pelo deadline relativo. O EDF, pelo deadline absoluto, que muda a cada instante. Três linhas, três algoritmos. Trocar de política é trocar essa função, o resto do motor é idêntico."

## 5. Seção 5: o motor a eventos discretos (2min)
*(mostrar `SimuladorEventosDiscretos.executar`, apontar os PASSOs)*
"Esse é o coração. O relógio não anda de um em um: ele salta de evento em evento. Por quê? Porque entre dois eventos nada muda, o job de maior prioridade só executa."
"Segue os passos comentados. PASSO 1, no arranque, agenda a primeira liberação de cada tarefa. O laço então tira o próximo evento de um heap, sempre o menor tempo. PASSO 2: salta o relógio até ali e desconta do job ativo o tempo que ele executou no intervalo. PASSO 3: se o job zerou, ele terminou agora. PASSO 4: se o evento foi uma liberação, nasce um job novo. PASSO 5 marca quem estourou o prazo. E o PASSO 6 reescolhe o job de maior prioridade e agenda quando ele terminaria."
"Repara que a preempção não tem código especial: ela aparece sozinha. Quando um job de prioridade maior é liberado, no próximo passo ele é escolhido no PASSO 6 e assume a CPU."

## 6. Demo ao vivo: RM perde (1min30)
*(rodar `uv run main.py`, escolher cenário `2`, algoritmo `RM`)*
"Vamos ver de verdade. Cenário 2: duas tarefas, `T1` pede 2 a cada 5, `T2` pede 4 a cada 7. Utilização 0,97, abaixo de 1. Pela teoria o EDF dá conta. E o RM?"
*(apontar a saída no terminal)*
"O terminal já diz: falha, o job `T2.1` perdeu o deadline, pior tempo de resposta 8 contra um prazo de 7."
*(apontar o Gantt)*
"E o gráfico mostra por quê. Em `t=5`, `T1` tem período menor, então preempta `T2`. Quando o deadline de `T2` chega em `t=7`, ainda faltava uma unidade. Esse bloco vermelho é a execução que vazou para depois do prazo, e o X marca a perda. RM falhou mesmo com a CPU sobrando."

## 7. Demo ao vivo: EDF cumpre (1min)
*(voltar ao menu, cenário `2`, algoritmo `EDF`)*
"Mesma carga, agora EDF. A diferença nasce lá em `t=2`: o EDF olha o deadline absoluto. `T2` vence em 7, `T1` vence em 10, então o EDF deixa `T2` terminar primeiro, em `t=6`, antes do prazo."
*(apontar o Gantt verde)*
"Nenhum bloco vermelho, nenhum X. O título fica verde: cumpre todos os deadlines. Mesmo trabalho, decisão melhor sobre a ordem."

## 8. Os outros dois cenários (45s)
*(cenário `1` com `RM`, depois cenário `3` com `EDF`)*
"Fechando o quadro: no cenário 1, utilização baixa, três tarefas, todos cumprem, como o teste garante. No cenário 3, sobrecarga, utilização acima de 1: aí não tem algoritmo que salve, os dois perdem. Teoria e simulação concordam nos três casos."

## 9. Dicionário e fechamento (45s)
*(menu opção `D`, ou abrir `dicionario.md`)*
"Para quem quiser revisar os termos, o próprio programa tem um dicionário na opção D: tarefa, job, utilização, hiperperíodo, preempção, os três algoritmos."
"Resumindo: um simulador a eventos discretos, num arquivo só, com três algoritmos sob a mesma abstração de chave de prioridade, e um Gantt que deixa a perda de deadline óbvia. É isso. Obrigado, e estamos abertos a perguntas."

---

## Comandos da demo (deixar copiados)
```bash
uv run main.py            # abre o menu; escolher 2 -> RM, depois 2 -> EDF
uv run main.py 2 RM       # atalho: cenário 2 direto com RM (perde)
uv run main.py 2 EDF      # atalho: cenário 2 direto com EDF (cumpre)
uv run main.py 1 RM       # sucesso, três tarefas
uv run main.py 3 EDF      # sobrecarga
```

## Plano B se a demo travar
Os PNGs já estão gerados na pasta: `gantt_rm_falha.png` (RM perde) e `gantt_edf_ok.png` (EDF cumpre).
Basta abri-los e dizer: "esses gráficos foram gerados por esse mesmo `main.py`."
