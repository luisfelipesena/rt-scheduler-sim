# Roteiro de apresentação (10 min)

**Trabalho:** Simulador de escalonamento de tempo real por eventos discretos
**Dupla:** Luis Sena e Antoniel Magalhães
**Divisão:** Luis abre (fundamentos, slides 1 a 7), Antoniel fecha (simulador, demo e resultados, slides 8 a 15).

Dica: a fala abaixo é o texto base. Não precisa ler palavra por palavra, mas o tempo por slide já fecha em ~10 min. Setas de tempo aproximadas à direita.

---

## Parte 1 — LUIS (slides 1 a 7, ~5 min)

### Slide 1 — Título (15s)
"Boa tarde. Eu sou o Luis, esse é o Antoniel, e a gente desenvolveu um simulador de escalonamento de tarefas de tempo real. A ideia é simular, evento a evento, como diferentes algoritmos decidem qual tarefa roda na CPU, e mostrar quando cada um cumpre ou perde os deadlines."

### Slide 2 — Agenda (20s)
"A apresentação tem duas partes. Eu começo com os fundamentos: o que é um sistema de tempo real, o modelo de tarefas, como funciona a simulação a eventos discretos e os algoritmos que implementamos. Depois o Antoniel mostra a arquitetura do simulador, roda uma demonstração ao vivo e apresenta os resultados e a validação."

### Slide 3 — O problema (45s)
"Em sistemas de tempo real, estar correto não basta: tem que estar correto no tempo certo. Um resultado certo que chega atrasado é, na prática, um resultado errado. Pensa num airbag ou num marca-passo: a resposta tem prazo."
"A gente modela a carga como tarefas periódicas. Cada tarefa libera uma sequência infinita de jobs, e cada job tem um deadline. A pergunta central do trabalho é: esse conjunto de tarefas é escalonável, ou seja, dá para rodar tudo sem perder nenhum deadline? Existem dois caminhos para responder: testes analíticos e simulação. A gente faz os dois."

### Slide 4 — Modelo de tarefas (45s)
"Cada tarefa é definida por quatro números. C é o tempo de execução no pior caso. T é o período, o intervalo entre uma liberação e a próxima. D é o deadline relativo, e a gente usa deadline implícito, ou seja, D igual a T. E a fase, que é quando o primeiro job aparece."
"Desses números sai a métrica mais importante: a utilização U, que é o somatório de C sobre T. É a fração da CPU que as tarefas exigem. Guarda esse número, porque ele decide quase tudo. Se U passa de 1, é sobrecarga: nenhum algoritmo no mundo consegue escalonar."

### Slide 5 — Simulação a eventos discretos (55s)
"Aqui está o coração do trabalho. Em vez de avançar o relógio de um em um, a gente salta de evento em evento. Por quê? Porque entre dois eventos nada muda: o job de maior prioridade simplesmente executa direto."
"E quais são os eventos? Dois principais: a liberação de um job, quando uma tarefa cria um novo trabalho, e o término de um job, quando ele acaba de executar. O próximo evento é sempre o menor entre a próxima liberação e o término do job que está rodando agora."
"Uma coisa bonita é que a preempção surge sozinha: quando um job de maior prioridade é liberado, ele toma a CPU de quem estava rodando. E a perda de deadline a gente trata como uma observação, não como um evento que comanda o escalonador."

### Slide 6 — Os algoritmos (50s)
"A gente implementou três algoritmos. Rate Monotonic, ou RM, usa prioridade estática: quanto menor o período, maior a prioridade. É o clássico do Liu e Layland, de 1973. Deadline Monotonic é parecido, mas usa o deadline relativo no lugar do período. E o EDF, Earliest Deadline First, é dinâmico: a cada instante, quem tem o deadline absoluto mais próximo ganha a CPU."
"O detalhe de engenharia que a gente gosta: os três algoritmos são a mesma abstração. Toda política é só uma chave de prioridade, onde menor chave significa maior prioridade. O motor sempre roda o job de menor chave. RM, DM e EDF diferem apenas na definição dessa chave. Trocar de algoritmo é trocar uma função."

### Slide 7 — Testes de escalonabilidade (50s)
"Antes de simular, dá para prever no papel. Para RM existe o limite do Liu e Layland: se a utilização fica abaixo de n vezes 2 elevado a 1 sobre n, menos 1, o RM garante que ninguém perde deadline. Esse limite cai e estabiliza perto de 69 por cento."
"Para EDF o teste é exato e mais simples: com deadline implícito, basta U menor ou igual a 1. Por isso o EDF chega a 100 por cento de utilização, enquanto a prioridade fixa fica travada perto de 69 por cento no pior caso."
"Então a gente tem uma previsão teórica. O bom da simulação é confirmar, na prática, exatamente o que o teste diz. Passo a palavra pro Antoniel mostrar isso rodando."

---

## Parte 2 — ANTONIEL (slides 8 a 15, ~5 min)

### Slide 8 — Arquitetura do simulador (45s)
"Obrigado, Luis. O simulador é Python puro, só biblioteca padrão, sem nenhuma dependência externa. São poucas centenas de linhas, separadas por responsabilidade."
"O model tem Task, Job e TaskSet, que carrega os conjuntos de um JSON. O schedulers tem as três políticas como chaves de prioridade. O simulator é o laço de eventos que o Luis explicou. O metrics faz a utilização e os testes. O gantt desenha o diagrama, em ASCII pro terminal e em SVG pro navegador. E o cli amarra tudo em três comandos: run, compare e analyze."
"No fim, o laço inteiro cabe em duas linhas: escolhe o job de menor chave de prioridade e salta para o próximo evento."

### Slide 9 — Demonstração ao vivo (40s)
"Vou rodar de verdade agora. O conjunto tem duas tarefas: a primeira pede 2 de tempo a cada 5, a segunda pede 4 a cada 7. A utilização dá 0,97, ou seja, abaixo de 1. Pela teoria, o EDF deveria dar conta. Será que o RM também dá?"
"Esse comando roda os dois algoritmos lado a lado, na mesma carga, com o trace completo de eventos."
*(rodar o comando do slide; deixar o trace aparecer; comentar que a partir de t=5 os dois divergem)*
"Repara que até t=5 é igual. Aí o RM e o EDF tomam decisões diferentes. Vamos ver no diagrama o que acontece."

### Slide 10 — RM perde o deadline (45s)
"Esse é o Gantt que o próprio simulador gera. No RM, em t=5, a tarefa 1 tem prioridade maior porque tem período menor, então ela preempta a tarefa 2. O problema: a tarefa 2 ainda devia 1 unidade de execução, e o deadline dela era t=7. Quando chegou em 7, ela não tinha terminado. Esse bloco vermelho é a execução que vazou para depois do prazo. Pior tempo de resposta da tarefa 2: 8, contra um deadline de 7. RM falhou, mesmo com utilização abaixo de 1."

### Slide 11 — EDF cumpre todos (45s)
"Mesma carga, agora com EDF. A diferença está em t=2: o EDF olha o deadline absoluto. A tarefa 2 tem deadline em 7, a tarefa 1 tem deadline em 10. Então o EDF deixa a tarefa 2 terminar primeiro, e ela fecha em t=6, antes do prazo. Ninguém perde deadline. É o mesmo trabalho, com uma decisão melhor sobre a ordem. Isso é exatamente o que a teoria previa: na faixa entre 69 por cento e 100 por cento, o EDF cumpre onde o RM falha."

### Slide 12 — Resumo dos resultados (40s)
"Resumindo os três conjuntos de teste. Com utilização baixa, abaixo do limite, os dois cumprem, como o teste garante. Na faixa intermediária, o caso que acabamos de ver, o EDF cumpre e o RM perde. E na sobrecarga, com U acima de 1, nenhum dos dois salva. Os dois algoritmos perdem deadline, e isso também está certo: acima de 100 por cento de utilização não existe escalonamento possível. Teoria e simulação concordam nos três casos."

### Slide 13 — Validação (40s)
"Para garantir que não é só uma demo bonita, tem 17 testes automatizados, todos passando. Eles checam a utilização, o limite do Liu e Layland, o hiperperíodo, se o RM escolhe mesmo o menor período e o EDF o menor deadline. Tem também testes de sanidade física: o tempo total de CPU ocupada bate com a soma das execuções, e os blocos nunca se sobrepõem, porque só um job roda por vez. E tem o teste do caso âncora, fixando que o RM perde em t=7 e o EDF cumpre. A simulação e o teste analítico batem em todos os conjuntos."

### Slide 14 — Conclusão (35s)
"Concluindo: a gente entregou um simulador a eventos discretos que anda de evento em evento, com liberação e término de jobs, três algoritmos sob uma única abstração de prioridade, e saídas pensadas para ensino: o trace, o Gantt em ASCII e o SVG. Ele mostra na prática a fronteira clássica entre prioridade fixa e EDF. Como trabalho futuro, dá para somar recursos compartilhados, com eventos de entrada e saída de recurso, e protocolos de herança de prioridade."

### Slide 15 — Perguntas (15s)
"É isso. O código está no GitHub, no link do slide. Obrigado, e estamos abertos a perguntas."

---

## Plano B se a demo ao vivo falhar
Se algo der errado no terminal, os diagramas dos slides 10 e 11 já contam a história inteira. Basta dizer: "os diagramas que vocês estão vendo foram gerados por esse mesmo simulador" e seguir para o slide 12.

Comandos da demo (deixar copiados antes de começar):
```bash
python -m rtsim compare examples/rm_fails_edf_ok.json --algos RM EDF --verbose
python -m rtsim run examples/rm_fails_edf_ok.json --algo RM   # só RM, com Gantt ASCII
python -m unittest discover -s tests                          # mostra os 17 testes passando
```
