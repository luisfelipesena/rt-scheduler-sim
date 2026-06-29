"""Schedulability analysis: utilization and classic feasibility tests."""
from __future__ import annotations

from dataclasses import dataclass

from .model import TaskSet


def liu_layland_bound(n: int) -> float:
    """RM least-upper-bound utilization: U_lub = n (2^(1/n) - 1).

    Decreases from 1.0 (n=1) toward ln 2 ~= 0.693 as n grows. A taskset with
    U <= U_lub is guaranteed RM-schedulable (sufficient, not necessary).
    """
    if n <= 0:
        return 1.0
    return n * (2 ** (1 / n) - 1)


@dataclass
class Analysis:
    utilization: float
    n: int
    rm_bound: float
    rm_sufficient: bool      # U <= bound  => RM definitely schedulable
    edf_feasible: bool       # U <= 1      => EDF schedulable (exact for implicit D)


def analyze(ts: TaskSet) -> Analysis:
    u = ts.utilization
    n = len(ts.tasks)
    bound = liu_layland_bound(n)
    eps = 1e-9
    return Analysis(u, n, bound, u <= bound + eps, u <= 1 + eps)
