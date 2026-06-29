"""Render a simulation as a Gantt chart: ASCII (terminal) or SVG (browser)."""
from __future__ import annotations

from typing import Dict, List, Tuple

from .model import Task
from .simulator import SimulationResult

# Distinct, color-blind friendly palette for the SVG lanes.
_COLORS = ["#4e79a7", "#f28e2b", "#59a14f", "#e15759",
           "#b07aa1", "#76b7b2", "#edc948", "#9c755f"]


def _occupancy(result: SimulationResult) -> Dict[int, List[str]]:
    """Per-task, per-unit cell: ' ' idle, '#' on-time run, '!' late run."""
    H = result.horizon
    grid = {t.id: [" "] * H for t in result.tasks}
    for seg in result.segments:
        for c in range(seg.start, min(seg.end, H)):
            grid[seg.task_id][c] = "!" if c >= seg.deadline else "#"
    return grid


def _markers(task: Task, horizon: int) -> Tuple[List[int], List[int]]:
    """Release and deadline instants of a task inside [0, horizon]."""
    releases, deadlines = [], []
    k = 0
    while True:
        r = task.phase + k * task.period
        if r > horizon:
            break
        releases.append(r)
        if r + task.deadline <= horizon:
            deadlines.append(r + task.deadline)
        k += 1
    return releases, deadlines


def ascii_gantt(result: SimulationResult) -> str:
    H = result.horizon
    if H > 200:
        return f"(horizon={H} too wide for ASCII; use --svg for a scaled chart)"

    grid = _occupancy(result)
    missed_at = {m.abs_deadline for m in result.misses}
    label_w = max(len(t.name) for t in result.tasks) + 1
    prefix = label_w + 2                          # name + space + left border "|"

    lines: List[str] = []
    ruler = " " * prefix + "".join(
        "|" if c % 5 == 0 else str(c % 10) for c in range(H + 1))
    tens = (" " * prefix + "".join(
        str(c // 10) if (c % 10 == 0 and c >= 10) else " " for c in range(H + 1)))
    lines.append(ruler.rstrip())
    lines.append(tens.rstrip())

    for task in result.tasks:
        cells = grid[task.id]
        exec_row = "".join("█" if v == "#" else "▒" if v == "!" else "·"
                           for v in cells)
        lines.append(f"{task.name.rjust(label_w)} |{exec_row}|")

        releases, deadlines = _markers(task, H)
        mark = [" "] * (H + 1)
        for d in deadlines:
            mark[d] = "v"                       # deadline
        for r in releases:
            mark[r] = "^"                       # release (drawn on top)
        for d in deadlines:
            if d in missed_at:
                mark[d] = "X"                   # missed deadline
        lines.append(" " * prefix + "".join(mark).rstrip())
    legend = ("legend: █ running   ▒ running late   · idle   "
              "^ release   v deadline   X miss")
    lines.append(legend)
    return "\n".join(lines)


def svg_gantt(result: SimulationResult, unit: int = 26, lane: int = 46) -> str:
    H = result.horizon
    tasks = result.tasks
    left = 70
    top = 40
    width = left + H * unit + 40
    height = top + len(tasks) * lane + 60
    color = {t.id: _COLORS[i % len(_COLORS)] for i, t in enumerate(tasks)}

    parts: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'font-family="Helvetica,Arial,sans-serif" font-size="13">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{left}" y="24" font-size="16" font-weight="bold">'
        f'{result.taskset_name} &#183; {result.policy.short}: '
        f'{"FEASIBLE" if result.feasible else "MISSES DEADLINES"}</text>',
    ]

    # Time grid and ruler.
    for c in range(H + 1):
        x = left + c * unit
        stroke = "#cccccc" if c % 5 else "#888888"
        parts.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{top + len(tasks) * lane}" '
                     f'stroke="{stroke}" stroke-width="1"/>')
        if c % 5 == 0:
            parts.append(f'<text x="{x}" y="{top - 6}" text-anchor="middle" '
                         f'fill="#555">{c}</text>')

    for i, task in enumerate(tasks):
        y = top + i * lane
        parts.append(f'<text x="{left - 10}" y="{y + lane / 2 + 4}" '
                     f'text-anchor="end" font-weight="bold">{task.name}</text>')
        parts.append(f'<rect x="{left}" y="{y + 6}" width="{H * unit}" '
                     f'height="{lane - 12}" fill="#f6f6f6" stroke="#eeeeee"/>')

        # Execution segments.
        for seg in result.segments:
            if seg.task_id != task.id:
                continue
            x = left + seg.start * unit
            w = (seg.end - seg.start) * unit
            late = seg.end > seg.deadline
            fill = "#d62728" if late else color[task.id]
            parts.append(f'<rect x="{x}" y="{y + 6}" width="{w}" height="{lane - 12}" '
                         f'rx="3" fill="{fill}" stroke="#333" stroke-width="0.6"/>')

        # Release (up arrow) and deadline (down arrow) markers.
        releases, deadlines = _markers(task, H)
        missed_at = {m.abs_deadline for m in result.misses if m.task.id == task.id}
        for r in releases:
            x = left + r * unit
            parts.append(f'<path d="M{x},{y + lane - 4} l-4,9 l8,0 z" fill="#2ca02c"/>')
        for d in deadlines:
            x = left + d * unit
            col = "#d62728" if d in missed_at else "#666666"
            parts.append(f'<path d="M{x},{y + 13} l-4,-9 l8,0 z" fill="{col}"/>')
            if d in missed_at:
                parts.append(f'<text x="{x + 6}" y="{y + 10}" fill="#d62728" '
                             f'font-weight="bold">miss</text>')

    parts.append('</svg>')
    return "\n".join(parts)
