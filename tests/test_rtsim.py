"""End-to-end and unit tests for the rtsim simulator. Run: python -m unittest -v"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rtsim import (EDF, RM, DM, TaskSet, analyze, hyperperiod,
                   liu_layland_bound, simulate)
from rtsim.events import EventKind
from rtsim.model import Task


def ts(*triples, name="t"):
    """Build a TaskSet from (wcet, period[, deadline]) triples."""
    tasks = []
    for i, tr in enumerate(triples, start=1):
        c, p = tr[0], tr[1]
        d = tr[2] if len(tr) > 2 else p
        tasks.append(Task(id=i, name=f"T{i}", wcet=c, period=p, deadline=d))
    return TaskSet(name, tasks)


class TestMetrics(unittest.TestCase):
    def test_utilization(self):
        self.assertAlmostEqual(ts((2, 5), (4, 7)).utilization, 2 / 5 + 4 / 7)

    def test_liu_layland_bound(self):
        self.assertAlmostEqual(liu_layland_bound(1), 1.0)
        self.assertAlmostEqual(liu_layland_bound(2), 2 * (2 ** 0.5 - 1))
        self.assertGreater(liu_layland_bound(1000), math.log(2))
        self.assertLess(liu_layland_bound(1000), 0.70)

    def test_hyperperiod(self):
        self.assertEqual(hyperperiod(ts((1, 4), (1, 6), (1, 8)).tasks), 24)
        self.assertEqual(hyperperiod(ts((2, 5), (4, 7)).tasks), 35)

    def test_analyze_flags(self):
        a = analyze(ts((1, 4), (2, 6), (1, 8)))   # U = 0.708
        self.assertTrue(a.rm_sufficient)
        self.assertTrue(a.edf_feasible)
        over = analyze(ts((2, 4), (3, 5)))         # U = 1.10
        self.assertFalse(over.edf_feasible)


class TestPolicyKeys(unittest.TestCase):
    def test_rm_prefers_shorter_period(self):
        t = ts((1, 4), (1, 9)).tasks
        from rtsim.model import Job
        j_short = Job(t[0], 1, 0, 1, 4)
        j_long = Job(t[1], 1, 0, 1, 9)
        self.assertLess(RM.key(j_short, 0), RM.key(j_long, 0))

    def test_edf_prefers_earlier_deadline(self):
        t = ts((1, 4), (1, 9)).tasks
        from rtsim.model import Job
        j_far = Job(t[0], 1, 0, 1, 100)
        j_near = Job(t[1], 1, 0, 1, 5)
        self.assertLess(EDF.key(j_near, 0), EDF.key(j_far, 0))


class TestSimulator(unittest.TestCase):
    def test_single_task_response_equals_wcet(self):
        r = simulate(ts((2, 5)), RM)
        self.assertTrue(r.feasible)
        self.assertEqual(r.worst_response(r.tasks[0]), 2)
        # one job released per period over the hyperperiod
        self.assertEqual(len(r.jobs), r.horizon // 5)

    def test_conservation_of_execution_time(self):
        # Total CPU busy time equals sum of executed job costs.
        r = simulate(ts((1, 4), (2, 6), (1, 8)), EDF)
        busy = sum(s.end - s.start for s in r.segments)
        owed = sum(j.task.wcet for j in r.jobs)
        self.assertEqual(busy, owed)

    def test_segments_never_overlap(self):
        r = simulate(ts((2, 5), (4, 7)), EDF)
        segs = sorted(r.segments, key=lambda s: s.start)
        for a, b in zip(segs, segs[1:]):
            self.assertLessEqual(a.end, b.start)

    def test_idle_when_underutilized(self):
        r = simulate(ts((1, 10)), RM, horizon=10)
        busy = sum(s.end - s.start for s in r.segments)
        self.assertEqual(busy, 1)                  # 9 idle units

    def test_headline_rm_misses_edf_meets(self):
        taskset = ts((2, 5), (4, 7), name="headline")
        rm = simulate(taskset, RM)
        edf = simulate(taskset, EDF)
        self.assertFalse(rm.feasible)
        self.assertTrue(edf.feasible)
        # RM misses T2's first deadline exactly at t=7.
        miss_names = {m.name for m in rm.misses}
        self.assertIn("T2.1", miss_names)

    def test_first_miss_time_is_seven(self):
        rm = simulate(ts((2, 5), (4, 7)), RM)
        miss_events = [e for e in rm.events if e.kind == EventKind.DEADLINE_MISS]
        self.assertTrue(miss_events)
        self.assertEqual(miss_events[0].time, 7)

    def test_overload_misses_under_both(self):
        taskset = ts((2, 4), (3, 5), name="overload")
        self.assertFalse(simulate(taskset, RM).feasible)
        self.assertFalse(simulate(taskset, EDF).feasible)

    def test_dm_schedules_low_utilization(self):
        self.assertTrue(simulate(ts((1, 4), (1, 5), (2, 10)), DM).feasible)

    def test_event_trace_is_chronological(self):
        r = simulate(ts((2, 5), (4, 7)), RM)
        times = [e.time for e in r.events]
        self.assertEqual(times, sorted(times))

    def test_release_count_matches_periods(self):
        r = simulate(ts((1, 4), (1, 5), (2, 10)), EDF)
        releases = [e for e in r.events if e.kind == EventKind.RELEASE]
        # hyperperiod 20: T1 -> 5, T2 -> 4, T3 -> 2 releases.
        self.assertEqual(len(releases), 5 + 4 + 2)


class TestTaskSetIO(unittest.TestCase):
    def test_load_examples(self):
        base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples")
        for fname in ("feasible.json", "rm_fails_edf_ok.json",
                      "three_tasks.json", "overload.json"):
            taskset = TaskSet.load(os.path.join(base, fname))
            self.assertGreater(len(taskset.tasks), 0)
            simulate(taskset, EDF)                 # must not raise


if __name__ == "__main__":
    unittest.main(verbosity=2)
