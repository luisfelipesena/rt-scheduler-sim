"""rtsim: a discrete-event simulator for real-time task scheduling.

Public API:
    TaskSet, Task, Job          -- data models (model.py)
    RM, DM, EDF, POLICIES       -- scheduling policies (schedulers.py)
    simulate, hyperperiod       -- the event-driven engine (simulator.py)
    analyze, liu_layland_bound  -- schedulability tests (metrics.py)
    ascii_gantt, svg_gantt      -- charts (gantt.py)
"""
from .gantt import ascii_gantt, svg_gantt
from .metrics import analyze, liu_layland_bound
from .model import Job, Task, TaskSet
from .schedulers import DM, EDF, POLICIES, RM, Policy
from .simulator import SimulationResult, Segment, hyperperiod, simulate

__all__ = [
    "Task", "Job", "TaskSet",
    "Policy", "RM", "DM", "EDF", "POLICIES",
    "simulate", "hyperperiod", "SimulationResult", "Segment",
    "analyze", "liu_layland_bound",
    "ascii_gantt", "svg_gantt",
]

__version__ = "1.0.0"
