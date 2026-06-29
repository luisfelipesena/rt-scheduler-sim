"""Core data models: periodic real-time tasks and the jobs they release."""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class Task:
    """A periodic real-time task.

    A task releases an infinite stream of jobs, one every ``period`` time units
    starting at ``phase``. Each job needs up to ``wcet`` units of CPU and must
    finish within ``deadline`` units of its release (relative deadline). When
    ``deadline == period`` the task has an implicit deadline.
    """

    id: int
    name: str
    wcet: int           # worst-case execution time (C)
    period: int         # inter-release time (T)
    deadline: int       # relative deadline (D); implicit deadline => D == T
    phase: int = 0      # release offset of the first job (O)

    @property
    def utilization(self) -> float:
        return self.wcet / self.period


@dataclass
class Job:
    """One concrete invocation (job) of a task."""

    task: Task
    index: int               # 1-based job number within the task
    release: int             # absolute release time
    remaining: int           # CPU time still owed
    abs_deadline: int        # absolute deadline = release + task.deadline
    finish: Optional[int] = None
    missed: bool = False

    @property
    def name(self) -> str:
        return f"{self.task.name}.{self.index}"

    @property
    def response_time(self) -> Optional[int]:
        return None if self.finish is None else self.finish - self.release


@dataclass
class TaskSet:
    """A set of periodic tasks to be scheduled together."""

    name: str
    tasks: List[Task]

    @property
    def utilization(self) -> float:
        return sum(t.utilization for t in self.tasks)

    @classmethod
    def from_dict(cls, data: dict) -> "TaskSet":
        tasks: List[Task] = []
        for i, td in enumerate(data["tasks"], start=1):
            tid = td.get("id", i)
            period = td["period"]
            tasks.append(
                Task(
                    id=tid,
                    name=td.get("name", f"T{tid}"),
                    wcet=td["wcet"],
                    period=period,
                    deadline=td.get("deadline", period),
                    phase=td.get("phase", 0),
                )
            )
        return cls(name=data.get("name", "taskset"), tasks=tasks)

    @classmethod
    def load(cls, path: str) -> "TaskSet":
        return cls.from_dict(json.loads(pathlib.Path(path).read_text(encoding="utf-8")))
