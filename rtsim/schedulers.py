"""Scheduling policies.

A policy is defined entirely by a priority key: given a job and the current
time it returns a sortable tuple where *smaller means higher priority*. The
simulator always runs the ready job with the smallest key, so preemption and
the difference between fixed and dynamic priority both fall out of the key.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Tuple

from .model import Job


@dataclass(frozen=True)
class Policy:
    name: str
    short: str
    key: Callable[[Job, int], Tuple]
    description: str


def _rm_key(job: Job, now: int) -> Tuple:
    # Rate Monotonic: shorter period => higher priority (static). Tie-break by id.
    return (job.task.period, job.task.id)


def _dm_key(job: Job, now: int) -> Tuple:
    # Deadline Monotonic: shorter relative deadline => higher priority (static).
    return (job.task.deadline, job.task.id)


def _edf_key(job: Job, now: int) -> Tuple:
    # Earliest Deadline First: nearest absolute deadline => higher priority (dynamic).
    return (job.abs_deadline, job.task.id)


RM = Policy(
    "Rate Monotonic", "RM", _rm_key,
    "Static priority by period (shorter period wins). Liu & Layland, 1973.",
)
DM = Policy(
    "Deadline Monotonic", "DM", _dm_key,
    "Static priority by relative deadline (shorter deadline wins).",
)
EDF = Policy(
    "Earliest Deadline First", "EDF", _edf_key,
    "Dynamic priority by absolute deadline. Optimal for U <= 1.",
)

POLICIES = {p.short: p for p in (RM, DM, EDF)}
