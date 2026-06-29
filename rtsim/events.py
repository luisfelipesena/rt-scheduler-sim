"""Events produced by the discrete-event simulation.

The two scheduling events required by the assignment are RELEASE (a task
releases a job) and COMPLETION (a job finishes). PREEMPTION and DEADLINE_MISS
are derived observations we also log to make the timeline easy to read.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EventKind(Enum):
    RELEASE = "RELEASE"          # a task releases a new job
    COMPLETION = "COMPLETION"    # a job finishes executing
    PREEMPTION = "PREEMPTION"    # running job yields the CPU to a higher-priority job
    DEADLINE_MISS = "MISS"       # a job's deadline passed while still unfinished


@dataclass
class Event:
    time: int
    kind: EventKind
    job: str                     # job name, e.g. "T1.2"
    detail: str = ""

    def __str__(self) -> str:
        tag = self.kind.value.ljust(11)
        line = f"t={self.time:>4}  {tag} {self.job}"
        return f"{line}  {self.detail}" if self.detail else line
