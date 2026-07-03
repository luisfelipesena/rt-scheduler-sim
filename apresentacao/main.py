# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib"]
# ///
"""Simulador de escalonamento de tempo real por eventos discretos.

Arquivo único, em português. Roda por menu (TUI) e desenha um diagrama de Gantt
colorido no fim, deixando claro quando cada algoritmo CUMPRE ou PERDE deadlines.

Como rodar (o matplotlib é instalado sozinho pelo uv):
    uv run main.py                 # abre o menu interativo
    uv run main.py 2 RM            # cenário 2 com Rate Monotonic (atalho)

Sistemas de Tempo Real (UFBA / IC) - Luis Sena e Antoniel Magalhães.
"""
import heapq
import sys
from dataclasses import dataclass
from math import gcd
from typing import Callable, List, Optional, Tuple

# matplotlib é opcional: se faltar, caímos no Gantt em ASCII (o programa sempre roda).
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


# =====================================================================
# 1. MODELO: tarefa periódica e o job (uma instância dela)
# =====================================================================
@dataclass(frozen=True)
class Tarefa:
    id: int
    nome: str
    C: int          # tempo de execução no pior caso (WCET)
    T: int          # período: intervalo entre duas liberações
    D: int          # deadline relativo (usamos D = T, deadline implícito)

    @property
    def utilizacao(self) -> float:
        return self.C / self.T          # fração de CPU que a tarefa exige


@dataclass
class Job:
    tarefa: Tarefa
    indice: int                 # T2.1 -> indice 1 (primeiro job de T2)
    liberacao: int              # instante em que o job ficou pronto
    tempo_restante: int         # CPU que ainda falta; zera ao terminar
    deadline: int               # deadline absoluto = liberação + D
    fim: Optional[int] = None
    perdido: bool = False

    @property
    def nome(self) -> str:
        return f"{self.tarefa.nome}.{self.indice}"

    @property
    def id_tarefa(self) -> int:
        return self.tarefa.id


# =====================================================================
# 2. CENÁRIOS: conjuntos de tarefas prontos para demonstrar cada caso
# =====================================================================
CENARIOS = {
    "1": ("Sucesso: todos cumprem", [
        Tarefa(1, "T1", 1, 4, 4),
        Tarefa(2, "T2", 1, 5, 5),
        Tarefa(3, "T3", 2, 8, 8),
    ]),
    "2": ("RM falha, EDF cumpre (caso clássico)", [
        Tarefa(1, "T1", 2, 5, 5),
        Tarefa(2, "T2", 4, 7, 7),
    ]),
    "3": ("Sobrecarga: todos perdem", [
        Tarefa(1, "T1", 3, 5, 5),
        Tarefa(2, "T2", 5, 10, 10),
    ]),
}


# =====================================================================
# 3. POLÍTICAS DE PRIORIDADE: cada uma é só uma chave (menor = mais prioritário)
# =====================================================================
def prioridade_rm(job: Job) -> Tuple:
    return (job.tarefa.T, job.tarefa.id)        # RM: menor período vence (estático)


def prioridade_dm(job: Job) -> Tuple:
    return (job.tarefa.D, job.tarefa.id)        # DM: menor deadline relativo vence (estático)


def prioridade_edf(job: Job) -> Tuple:
    return (job.deadline, job.tarefa.id)        # EDF: menor deadline absoluto vence (dinâmico)


POLITICAS = {
    "RM": ("Rate Monotonic", prioridade_rm),
    "DM": ("Deadline Monotonic", prioridade_dm),
    "EDF": ("Earliest Deadline First", prioridade_edf),
}


# =====================================================================
# 4. MÉTRICAS: hiperperíodo e limite de escalonabilidade do RM
# =====================================================================
def hiperperiodo(tarefas: List[Tarefa]) -> int:
    h = 1
    for t in tarefas:
        h = h // gcd(h, t.T) * t.T              # MMC dos períodos (T1=5,T2=7 -> 35)
    return h


def utilizacao(tarefas: List[Tarefa]) -> float:
    return sum(t.utilizacao for t in tarefas)   # U = soma de C/T


def limite_liu_layland(n: int) -> float:
    return n * (2 ** (1 / n) - 1)               # n=2 -> 0,828; tende a ln2 ~= 0,693


# =====================================================================
# 5. MOTOR: simulador a eventos discretos
# =====================================================================
class SimuladorEventosDiscretos:
    """Avança de evento em evento (nunca de 1 em 1 unidade de tempo).

    Eventos que movem o relógio: LIBERACAO_JOB (nasce um job) e TERMINO_JOB
    (marco de quando o job ativo deveria acabar). Entre dois eventos, o job de
    maior prioridade executa sem interrupção. A preempção surge sozinha; a perda
    de deadline é observação derivada, não comanda o escalonador.
    """

    def __init__(self, tarefas: List[Tarefa], prioridade: Callable[[Job], Tuple],
                 horizonte: int):
        self.tarefas = tarefas
        self.mapa_tarefas = {t.id: t for t in tarefas}
        self.prioridade = prioridade            # troca RM/DM/EDF = troca esta função
        self.horizonte = horizonte
        self.lista_eventos: List[Tuple] = []    # heap de (tempo, ordem, tipo, dados)
        self._seq = 0                           # desempate estável no heap
        self.tempo_atual = 0
        self.job_ativo: Optional[Job] = None
        self.fila_prontos: List[Job] = []       # jobs liberados esperando/na CPU
        self.contador_jobs = {t.id: 0 for t in tarefas}
        self.historico: List[Tuple] = []        # (inicio, fim, id_tarefa, deadline) p/ Gantt
        self.deadlines_perdidas: List[Tuple] = []   # (deadline, nome_job)
        self.jobs_terminados: List[Job] = []

    def agendar_evento(self, tempo: int, tipo: str, dados) -> None:
        heapq.heappush(self.lista_eventos, (tempo, self._seq, tipo, dados))
        self._seq += 1

    def obter_prioridade(self, job: Job) -> Tuple:
        return self.prioridade(job)

    def reordenar_fila_prontos(self) -> None:
        self.fila_prontos.sort(key=self.obter_prioridade)   # menor chave fica em [0]

    def executar(self) -> None:
        # PASSO 1 (arranque): agenda a 1ª liberação de cada tarefa em t = 0.
        for t in self.tarefas:
            self.agendar_evento(0, "LIBERACAO_JOB", t.id)

        # Laço principal: enquanto houver evento agendado dentro do horizonte.
        while self.lista_eventos:
            tempo_evento, _, tipo, dados = heapq.heappop(self.lista_eventos)
            if tempo_evento > self.horizonte:
                break

            # PASSO 2: "salta" o relógio; o job ativo ocupou a CPU nesse intervalo.
            passo = tempo_evento - self.tempo_atual
            if passo > 0 and self.job_ativo is not None:
                self.historico.append((self.tempo_atual, tempo_evento,
                                       self.job_ativo.id_tarefa, self.job_ativo.deadline))
                self.job_ativo.tempo_restante -= passo      # desconta o que executou
            self.tempo_atual = tempo_evento

            # PASSO 3: se o job que rodava chegou a 0, ele terminou agora.
            if (self.job_ativo is not None and self.job_ativo.tempo_restante == 0
                    and self.job_ativo.fim is None):
                self._finalizar(self.job_ativo)
                self.job_ativo = None

            # PASSO 4: LIBERACAO cria job; TERMINO já foi tratado no passo 3.
            if tipo == "LIBERACAO_JOB":
                self._liberar(dados)

            # PASSO 5: marca deadlines vencidos entre os prontos (observação derivada).
            self._marcar_perdas()

            # PASSO 6: escolhe o job de maior prioridade e agenda quando ele terminaria.
            self.reordenar_fila_prontos()
            self.job_ativo = self.fila_prontos[0] if self.fila_prontos else None
            if self.job_ativo is not None:
                self.agendar_evento(self.tempo_atual + self.job_ativo.tempo_restante,
                                    "TERMINO_JOB", self.job_ativo)

    def _liberar(self, id_tarefa: int) -> None:
        t = self.mapa_tarefas[id_tarefa]
        self.contador_jobs[id_tarefa] += 1
        job = Job(tarefa=t, indice=self.contador_jobs[id_tarefa], liberacao=self.tempo_atual,
                  tempo_restante=t.C, deadline=self.tempo_atual + t.D)
        self.fila_prontos.append(job)
        prox = self.tempo_atual + t.T           # próxima liberação desta tarefa (+T)
        if prox <= self.horizonte:
            self.agendar_evento(prox, "LIBERACAO_JOB", id_tarefa)

    def _finalizar(self, job: Job) -> None:
        job.fim = self.tempo_atual
        self.fila_prontos.remove(job)
        self.jobs_terminados.append(job)
        if job.fim > job.deadline and not job.perdido:      # terminou atrasado
            job.perdido = True
            self.deadlines_perdidas.append((job.deadline, job.nome))

    def _marcar_perdas(self) -> None:
        for job in self.fila_prontos:
            if not job.perdido and job.tempo_restante > 0 and job.deadline <= self.tempo_atual:
                job.perdido = True
                self.deadlines_perdidas.append((job.deadline, job.nome))

    def pior_resposta(self, id_tarefa: int) -> Optional[int]:
        r = [j.fim - j.liberacao for j in self.jobs_terminados
             if j.id_tarefa == id_tarefa and j.fim is not None]
        return max(r) if r else None

    @property
    def viavel(self) -> bool:
        return not self.deadlines_perdidas


# =====================================================================
# 6. GANTT visual (matplotlib): claro, colorido e com deadlines marcados
# =====================================================================
CORES = ["#4E79A7", "#59A14F", "#F28E2B", "#B07AA1", "#76B7B2", "#EDC948"]
VERMELHO = "#D62728"


def plotar_gantt(sim: SimuladorEventosDiscretos, algoritmo: str,
                 salvar: Optional[str] = None, mostrar: bool = True) -> None:
    if plt is None:                              # sem matplotlib: cai no ASCII
        print(desenhar_gantt_ascii(sim))
        return

    tarefas = sim.tarefas
    H = sim.horizonte
    perdidos = {d for d, _ in sim.deadlines_perdidas}
    fig, ax = plt.subplots(figsize=(min(2 + H * 0.42, 18), 1.5 + len(tarefas) * 0.9))

    for i, t in enumerate(tarefas):
        y = len(tarefas) - 1 - i                 # T1 no topo
        cor = CORES[i % len(CORES)]
        # blocos de execução: azul/verde no prazo, vermelho o que vazou do deadline
        for inicio, fim, id_tarefa, deadline in sim.historico:
            if id_tarefa != t.id:
                continue
            if fim <= deadline:
                ax.broken_barh([(inicio, fim - inicio)], (y + 0.15, 0.7),
                               facecolors=cor, edgecolor="black", linewidth=0.5)
            else:                                # parte no prazo + parte atrasada
                if deadline > inicio:
                    ax.broken_barh([(inicio, deadline - inicio)], (y + 0.15, 0.7),
                                   facecolors=cor, edgecolor="black", linewidth=0.5)
                atraso_ini = max(inicio, deadline)
                ax.broken_barh([(atraso_ini, fim - atraso_ini)], (y + 0.15, 0.7),
                               facecolors=VERMELHO, edgecolor="black", linewidth=0.5)
        # marcadores: triângulo verde na liberação, linha tracejada no deadline
        k = 0
        while k * t.T <= H:
            r = k * t.T
            ax.plot(r, y + 0.1, marker="^", color="#2CA02C", markersize=8, clip_on=False)
            d = r + t.D
            if d <= H:
                perdido = d in perdidos
                ax.plot([d, d], [y + 0.1, y + 0.9], linestyle="--", linewidth=1.4,
                        color=VERMELHO if perdido else "#888888")
                if perdido:                      # X vermelho onde o deadline foi perdido
                    ax.plot(d, y + 0.9, marker="x", color=VERMELHO, markersize=10, mew=2.5)
            k += 1

    ax.set_yticks([len(tarefas) - 1 - i + 0.5 for i in range(len(tarefas))])
    ax.set_yticklabels([t.nome for t in tarefas])
    ax.set_xticks(range(0, H + 1))
    ax.set_xlim(0, H)
    ax.set_ylim(0, len(tarefas))
    ax.set_xlabel("Tempo (unidades)")
    ax.set_ylabel("Tarefas")
    ax.grid(axis="x", linestyle=":", alpha=0.4)

    status = "CUMPRE TODOS OS DEADLINES" if sim.viavel else f"PERDE {len(sim.deadlines_perdidas)} DEADLINE(S)"
    cor_status = "#2CA02C" if sim.viavel else VERMELHO
    ax.set_title(f"Escalonamento de Tempo Real - {algoritmo}",
                 fontweight="bold", fontsize=13, pad=30)
    ax.text(0.5, 1.06, status, transform=ax.transAxes, ha="center", va="bottom",
            color=cor_status, fontweight="bold", fontsize=11)
    fig.tight_layout()

    if salvar:
        fig.savefig(salvar, dpi=120, bbox_inches="tight")
        print(f"   (Gantt salvo em {salvar})")
    if mostrar:
        plt.show()
    plt.close(fig)


# =====================================================================
# 7. GANTT em ASCII: reserva para quando não houver matplotlib
# =====================================================================
def desenhar_gantt_ascii(sim: SimuladorEventosDiscretos) -> str:
    tarefas, H = sim.tarefas, sim.horizonte
    grade = {t.id: [" "] * H for t in tarefas}
    for inicio, fim, id_tarefa, deadline in sim.historico:
        for c in range(inicio, min(fim, H)):
            grade[id_tarefa][c] = "!" if c >= deadline else "#"
    larg = max(len(t.nome) for t in tarefas) + 1
    linhas = []
    for t in tarefas:
        linha = "".join("#" and ("█" if v == "#" else "▒" if v == "!" else "·") for v in grade[t.id])
        linhas.append(f"{t.nome.rjust(larg)} |{linha}|")
    linhas.append("legenda: █ no prazo   ▒ atrasado   · ocioso")
    return "\n".join(linhas)


# =====================================================================
# 8. DICIONÁRIO de termos de tempo real
# =====================================================================
DICIONARIO = {
    "Tarefa": "Trabalho periódico que libera um job a cada período T.",
    "Job": "Uma instância concreta de uma tarefa (T2.1 = 1º job de T2).",
    "C (WCET)": "Tempo de execução no pior caso: quanto de CPU o job pede.",
    "T (período)": "Intervalo entre duas liberações da mesma tarefa.",
    "D (deadline)": "Prazo relativo após a liberação (usamos D = T).",
    "Utilização U": "Soma de C/T. Fração da CPU exigida. U>1 é impossível de escalonar.",
    "Hiperperíodo": "MMC dos períodos: quanto basta simular para ver todo o padrão.",
    "Preempção": "Job de maior prioridade toma a CPU de quem estava rodando.",
    "RM": "Rate Monotonic: prioridade fixa, menor período = maior prioridade.",
    "DM": "Deadline Monotonic: prioridade fixa, menor deadline relativo vence.",
    "EDF": "Earliest Deadline First: prioridade dinâmica, menor deadline absoluto vence.",
    "Evento discreto": "O relógio salta para o próximo instante em que algo muda.",
    "Deadline miss": "Job não terminou até o deadline: falha de tempo real.",
    "Escalonável": "Existe ordem de execução que cumpre todos os deadlines.",
    "Limite Liu & Layland": "Se U <= n(2^(1/n)-1), o RM garante cumprir (suficiente).",
}


def imprimir_dicionario() -> None:
    print("\n=== Dicionário de termos ===")
    larg = max(len(k) for k in DICIONARIO)
    for termo, definicao in DICIONARIO.items():
        print(f"  {termo.ljust(larg)} : {definicao}")


# =====================================================================
# 9. INTERFACE DE TERMINAL (TUI) e execução
# =====================================================================
def imprimir_resumo(sim: SimuladorEventosDiscretos, algoritmo: str, tarefas: List[Tarefa]) -> None:
    U = utilizacao(tarefas)
    n = len(tarefas)
    print(f"\n>> {algoritmo}  |  U = {U:.3f}  |  hiperperíodo = {sim.horizonte}")
    print(f"   limite RM U_lub({n}) = {limite_liu_layland(n):.3f}   teste EDF: U<=1 -> "
          f"{'ok' if U <= 1 else 'sobrecarga'}")
    for t in tarefas:
        pr = sim.pior_resposta(t.id)
        estado = "n/d" if pr is None else ("OK" if pr <= t.D else f"PERDA (D={t.D})")
        print(f"   {t.nome}: pior tempo de resposta = {pr}   {estado}")
    if sim.viavel:
        print("   ✅ Sucesso: nenhuma deadline perdida no hiperperíodo.")
    else:
        nomes = ", ".join(sorted({n for _, n in sim.deadlines_perdidas}))
        print(f"   ❌ Falha: {len(sim.deadlines_perdidas)} deadline(s) perdida(s): {nomes}")


def rodar(cenario: str, algoritmo: str, mostrar: bool = True,
          salvar: Optional[str] = None) -> SimuladorEventosDiscretos:
    _, tarefas = CENARIOS[cenario]
    nome_alg, prioridade = POLITICAS[algoritmo]
    H = hiperperiodo(tarefas)
    sim = SimuladorEventosDiscretos(tarefas, prioridade, horizonte=H)
    sim.executar()
    imprimir_resumo(sim, nome_alg, tarefas)
    plotar_gantt(sim, nome_alg, salvar=salvar, mostrar=mostrar)
    return sim


def menu() -> None:
    while True:
        print("\n==============================================")
        print(" Simulador de Escalonamento de Tempo Real")
        print("==============================================")
        for chave, (descricao, tarefas) in CENARIOS.items():
            print(f"  {chave}) {descricao}  (U={utilizacao(tarefas):.2f})")
        print("  D) Dicionário de termos")
        print("  0) Sair")
        escolha = input("Cenário > ").strip().upper()

        if escolha == "0":
            return
        if escolha == "D":
            imprimir_dicionario()
            continue
        if escolha not in CENARIOS:
            print("Opção inválida.")
            continue

        alg = input("Algoritmo [RM/DM/EDF] > ").strip().upper() or "RM"
        if alg not in POLITICAS:
            print("Algoritmo inválido.")
            continue
        rodar(escolha, alg, mostrar=True)


def main() -> None:
    # Atalho: "main.py 2 RM" roda direto; sem argumentos, abre o menu.
    if len(sys.argv) >= 3:
        cenario, alg = sys.argv[1], sys.argv[2].upper()
        if cenario in CENARIOS and alg in POLITICAS:
            rodar(cenario, alg, mostrar=True)
            return
    menu()


if __name__ == "__main__":
    main()
