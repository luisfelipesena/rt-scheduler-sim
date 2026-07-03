# Apresentação - Simulador de Escalonamento de Tempo Real

Versão visual, em um arquivo só, feita para apresentar o **código** ao vivo e
mostrar o diagrama de Gantt colorido no fim.

## Conteúdo da pasta
- `main.py` - simulador completo (modelo, políticas, motor a eventos, Gantt matplotlib, menu).
- `dicionario.md` - glossário dos termos (também disponível no menu, opção `D`).
- `falas.md` - roteiro de 10 min, seção por seção do código + demo ao vivo.
- `gantt_*.png` - gráficos já gerados (plano B se a demo travar).

## Como rodar
O `main.py` traz as dependências no cabeçalho (PEP 723), então o `uv` instala o
matplotlib sozinho:

```bash
uv run main.py            # abre o menu interativo
uv run main.py 2 RM       # atalho: cenário 2 com Rate Monotonic (perde deadline)
uv run main.py 2 EDF      # atalho: cenário 2 com EDF (cumpre tudo)
```

Sem `uv`, roda com Python direto; se o matplotlib não estiver instalado, o Gantt
cai para ASCII e o programa continua funcionando.

## Menu
- **1)** Sucesso: três tarefas, todos cumprem.
- **2)** RM falha, EDF cumpre (o caso clássico, U=0,97).
- **3)** Sobrecarga (U=1,10): ninguém escapa.
- **D)** Dicionário de termos.

Cada execução imprime o veredito no terminal (✅ / ❌) e abre o Gantt: azul/verde/laranja
para execução no prazo, **vermelho** para o que vazou do deadline, **X** onde o prazo foi perdido.
