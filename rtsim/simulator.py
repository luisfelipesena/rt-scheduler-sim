"""Event-driven simulator for preemptive real-time scheduling.

The simulation advances from event to event, never tick by tick. The only
scheduling events are job *releases* and job *completions*; between two
consecutive events the highest-priority ready job runs uninterrupted. Deadline
misses are derived observations (we detect and log them), not events that drive
the scheduler.

Main loop (at the current time ``t``):
  1. release every job whose release time equals ``t``;
  2. flag any ready job whose deadline has already passed;
  3. pick the ready job with the highest priority (smallest policy key);
  4. the next event is min(its completion time, the next release time);
  5. run the picked job up to that event and jump ``t`` there.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import gcd
from typing import List, Optional

from .events import Event, EventKind
from .model import Job, Task, TaskSet
from .schedulers import Policy


@dataclass
class Segment:
    """A maximal interval [start, end) during which one job held the CPU."""

    start: int
    end: int
    job: str
    task_id: int
    deadline: int            # absolute deadline of the job (to render late runs)


@dataclass
class SimulationResult:
    taskset_name: str
    policy: Policy
    horizon: int
    tasks: List[Task]
    events: List[Event]
    segments: List[Segment]
    jobs: List[Job]          # completed jobs
    misses: List[Job]

    @property
    def feasible(self) -> bool:
        return not self.misses

    def worst_response(self, task: Task) -> Optional[int]:
        rts = [j.response_time for j in self.jobs
               if j.task.id == task.id and j.response_time is not None]
        return max(rts) if rts else None


def _lcm(a: int, b: int) -> int:
    return a // gcd(a, b) * b


def hyperperiod(tasks: List[Task]) -> int:
    h = 1
    for t in tasks:
        h = _lcm(h, t.period)
    return h


def simulate(taskset: TaskSet, policy: Policy, horizon: Optional[int] = None,
             stop_on_miss: bool = False) -> SimulationResult:
    tasks = taskset.tasks
    if horizon is None:
        # For synchronous periodic tasks one hyperperiod (after the last phase)
        # is enough to expose any deadline miss.
        horizon = max(t.phase for t in tasks) + hyperperiod(tasks)

    next_release = {t.id: t.phase for t in tasks}
    counters = {t.id: 0 for t in tasks}
    ready: List[Job] = []
    events: List[Event] = []
    segments: List[Segment] = []
    finished: List[Job] = []
    misses: List[Job] = []
    prev_running: Optional[Job] = None

    def release_due(now: int) -> None:
        for task in sorted(tasks, key=lambda x: x.id):
            if next_release[task.id] == now:
                counters[task.id] += 1
                job = Job(task=task, index=counters[task.id], release=now,
                          remaining=task.wcet, abs_deadline=now + task.deadline)
                ready.append(job)
                next_release[task.id] += task.period
                events.append(Event(now, EventKind.RELEASE, job.name,
                                    f"deadline={job.abs_deadline}"))

    def flag_misses(now: int) -> None:
        for job in ready:
            if not job.missed and job.remaining > 0 and job.abs_deadline <= now:
                job.missed = True
                misses.append(job)
                events.append(Event(job.abs_deadline, EventKind.DEADLINE_MISS,
                                    job.name, "deadline passed, unfinished"))

    t = 0
    while t < horizon:
        release_due(t)
        flag_misses(t)

        running = min(ready, key=lambda j: policy.key(j, t)) if ready else None

        if (running is not None and prev_running is not None
                and running is not prev_running
                and prev_running.finish is None and prev_running.remaining > 0):
            events.append(Event(t, EventKind.PREEMPTION, prev_running.name,
                                f"preempted by {running.name}"))

        next_rel = min(next_release.values())   # always strictly greater than t here

        if running is None:
            prev_running = None
            if next_rel >= horizon:
                break
            t = next_rel                         # CPU idle until the next release
            continue

        completion = t + running.remaining
        t_next = min(completion, next_rel, horizon)

        if t_next > t:
            segments.append(Segment(t, t_next, running.name, running.task.id,
                                    running.abs_deadline))
            running.remaining -= (t_next - t)
        prev_running = running

        if t_next == completion and running.remaining == 0:
            running.finish = t_next
            ready.remove(running)
            finished.append(running)
            late = t_next > running.abs_deadline
            events.append(Event(t_next, EventKind.COMPLETION, running.name,
                                f"response={running.finish - running.release}"
                                + (" (LATE)" if late else "")))
            if late and not running.missed:
                running.missed = True
                misses.append(running)
            prev_running = None
            if stop_on_miss and misses:
                t = t_next
                break

        t = t_next

    flag_misses(horizon)
    # Stable chronological order; releases before other events at the same instant.
    order = {EventKind.RELEASE: 0, EventKind.PREEMPTION: 1,
             EventKind.COMPLETION: 2, EventKind.DEADLINE_MISS: 3}
    events.sort(key=lambda e: (e.time, order[e.kind]))
    return SimulationResult(taskset.name, policy, horizon, list(tasks),
                            events, segments, finished, misses)
