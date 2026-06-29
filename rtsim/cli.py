"""Command-line interface for the real-time scheduling simulator."""
from __future__ import annotations

import argparse
import pathlib
import sys
from typing import List

from .gantt import ascii_gantt, svg_gantt
from .metrics import analyze
from .model import TaskSet
from .schedulers import POLICIES, RM, EDF
from .simulator import SimulationResult, hyperperiod, simulate


def _print_taskset(ts: TaskSet) -> None:
    a = analyze(ts)
    print(f"Taskset: {ts.name}   (n={a.n}, hyperperiod={hyperperiod(ts.tasks)})")
    print(f"  {'task':<6}{'C':>4}{'T':>5}{'D':>5}{'phase':>7}{'U':>8}")
    for t in ts.tasks:
        print(f"  {t.name:<6}{t.wcet:>4}{t.period:>5}{t.deadline:>5}"
              f"{t.phase:>7}{t.utilization:>8.3f}")
    print(f"  total utilization U = {a.utilization:.3f}")
    print(f"  RM bound  U_lub({a.n}) = {a.rm_bound:.3f}  -> "
          f"{'PASS (RM guaranteed)' if a.rm_sufficient else 'inconclusive (simulate)'}")
    print(f"  EDF test  U <= 1       -> "
          f"{'FEASIBLE' if a.edf_feasible else 'INFEASIBLE (overload)'}")


def _print_result(result: SimulationResult, verbose: bool, gantt: str) -> None:
    print(f"\n=== {result.policy.name} ({result.policy.short}) ===")
    print(f"  {result.policy.description}")
    if verbose:
        print("  -- event trace --")
        for ev in result.events:
            print(f"    {ev}")
    print("  -- response times --")
    for task in result.tasks:
        wr = result.worst_response(task)
        status = "n/a" if wr is None else (
            "OK" if wr <= task.deadline else f"MISS (D={task.deadline})")
        print(f"    {task.name:<6} worst response = "
              f"{'-' if wr is None else wr:<4} {status}")
    verdict = "FEASIBLE (no deadline miss)" if result.feasible else (
        f"INFEASIBLE: {len(result.misses)} deadline miss(es): "
        + ", ".join(sorted({m.name for m in result.misses})))
    print(f"  verdict: {verdict}")
    if gantt == "ascii":
        print("  -- Gantt --")
        print(ascii_gantt(result))


def _load(path: str) -> TaskSet:
    return TaskSet.load(path)


def _resolve_policies(names: List[str]):
    out = []
    for n in names:
        key = n.upper()
        if key not in POLICIES:
            sys.exit(f"unknown algorithm '{n}'. choose from: {', '.join(POLICIES)}")
        out.append(POLICIES[key])
    return out


def cmd_run(args) -> None:
    ts = _load(args.taskset)
    _print_taskset(ts)
    policy = _resolve_policies([args.algo])[0]
    result = simulate(ts, policy, horizon=args.horizon, stop_on_miss=args.stop_on_miss)
    _print_result(result, args.verbose, args.gantt)
    if args.svg:
        pathlib.Path(args.svg).write_text(svg_gantt(result), encoding="utf-8")
        print(f"\n  SVG written to {args.svg}")


def cmd_compare(args) -> None:
    ts = _load(args.taskset)
    _print_taskset(ts)
    policies = _resolve_policies(args.algos)
    results = []
    for policy in policies:
        result = simulate(ts, policy, horizon=args.horizon)
        _print_result(result, args.verbose, args.gantt)
        results.append(result)

    print("\n=== summary ===")
    print(f"  {'algorithm':<26}{'feasible':<10}{'misses'}")
    for r in results:
        print(f"  {r.policy.name:<26}"
              f"{'yes' if r.feasible else 'NO':<10}{len(r.misses)}")
    if args.svg_dir:
        d = pathlib.Path(args.svg_dir)
        d.mkdir(parents=True, exist_ok=True)
        for r in results:
            p = d / f"{ts.name}_{r.policy.short}.svg"
            p.write_text(svg_gantt(r), encoding="utf-8")
            print(f"  SVG: {p}")


def cmd_analyze(args) -> None:
    _print_taskset(_load(args.taskset))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="rtsim",
        description="Discrete-event simulator for real-time task scheduling "
                    "(RM, DM, EDF). Steps event to event: job releases and "
                    "job completions.")
    sub = p.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("taskset", help="path to a taskset JSON file")
    common.add_argument("--horizon", type=int, default=None,
                        help="simulation length (default: max phase + hyperperiod)")
    common.add_argument("--verbose", "-v", action="store_true",
                        help="print the full event trace")
    common.add_argument("--gantt", choices=["ascii", "none"], default="ascii",
                        help="terminal Gantt chart (default: ascii)")

    r = sub.add_parser("run", parents=[common], help="simulate one algorithm")
    r.add_argument("--algo", default="EDF", help="RM, DM or EDF (default: EDF)")
    r.add_argument("--svg", help="write an SVG Gantt chart to this path")
    r.add_argument("--stop-on-miss", action="store_true",
                   help="halt at the first deadline miss")
    r.set_defaults(func=cmd_run)

    c = sub.add_parser("compare", parents=[common], help="simulate several algorithms")
    c.add_argument("--algos", nargs="+", default=["RM", "EDF"],
                   help="algorithms to compare (default: RM EDF)")
    c.add_argument("--svg-dir", help="write one SVG per algorithm into this folder")
    c.set_defaults(func=cmd_compare)

    a = sub.add_parser("analyze", parents=[common],
                       help="utilization and feasibility tests only")
    a.set_defaults(func=cmd_analyze)
    return p


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
