"""Standard-library tests: python3 -m unittest tests.test_astar -v."""
from dataclasses import dataclass
import json
import math
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import tracemalloc
import unittest
from unittest.mock import patch

from solvers.astar import astar, bloxorz_heuristic


class AStarTests(unittest.TestCase):
    def search(self, graph, start="S", goal="G", heuristic=None, **options):
        return astar(start, lambda state: state == goal,
                     lambda state: graph.get(state, ()), heuristic, **options)

    def test_weighted_shortest_path_and_replay(self):
        graph = {"S": [("sa", "A", 1), ("sb", "B", 4)],
                 "A": [("ab", "B", 1), ("ag", "G", 5)],
                 "B": [("bg", "G", 1)]}
        h = {"S": 3, "A": 2, "B": 1, "G": 0}
        result = self.search(graph, heuristic=h.__getitem__)
        self.assertTrue(result.solved)
        self.assertEqual(result.cost, 3)
        self.assertEqual(result.actions, ("sa", "ab", "bg"))
        self.assertEqual(result.states, ("S", "A", "B", "G"))
        self.assertEqual(result.solution_length, 3)
        replay_cost = 0
        for state, action, following in zip(result.states, result.actions, result.states[1:]):
            matches = [cost for act, target, cost in graph[state]
                       if act == action and target == following]
            self.assertEqual(len(matches), 1)
            replay_cost += matches[0]
        self.assertEqual(replay_cost, result.cost)
        self.assertGreaterEqual(result.search_time_seconds, 0)
        self.assertGreater(result.peak_memory_bytes, 0)
        self.assertEqual(result.expanded_nodes, 3)
        self.assertEqual(result.generated_nodes, 6)

    def test_reopens_with_admissible_inconsistent_heuristic(self):
        graph = {"S": [("sa", "A", 2), ("sb", "B", 2)],
                 "A": [("ac", "C", 2)], "B": [("bc", "C", 1)],
                 "C": [("cg", "G", 2)]}
        h = {"S": 0, "A": 0, "B": 3, "C": 0, "G": 0}
        result = self.search(graph, heuristic=h.__getitem__)
        self.assertEqual(result.cost, 5)
        self.assertEqual(result.actions, ("sb", "bc", "cg"))
        self.assertEqual(result.expanded_nodes, 5)  # S,A,C,B,C (C is reopened)

    def test_stale_heap_entry_is_not_expanded_twice(self):
        graph = {"S": [("sa", "A", 10), ("sb", "B", 1)],
                 "B": [("ba", "A", 1)], "A": [("stay", "A", 0)]}
        result = self.search(graph)
        self.assertEqual(result.status, "unsolvable")
        self.assertEqual(result.expanded_nodes, 3)
        self.assertEqual(result.generated_nodes, 4)
        self.assertIsNone(result.cost)
        self.assertEqual(result.states, ())
        self.assertEqual(result.actions, ())

    def test_zero_cost_control_actions_and_cycles(self):
        graph = {"S": [("switch", "B", 0)],
                 "B": [("switch", "S", 0), ("right", "G", 1)]}
        result = self.search(graph)
        self.assertEqual(result.cost, 1)
        self.assertEqual(result.actions, ("switch", "right"))
        self.assertEqual(result.solution_length, 2)  # all actions, not total cost

    def test_goal_start_even_with_zero_expansion_limit(self):
        result = self.search({}, start="G", max_expanded=0)
        self.assertTrue(result.solved)
        self.assertEqual(result.cost, 0)
        self.assertEqual(result.states, ("G",))
        self.assertEqual(result.solution_length, 0)
        self.assertEqual(result.expanded_nodes, 0)

    def test_none_is_a_valid_state(self):
        result = self.search({None: [("go", "G", 1)]}, start=None)
        self.assertEqual(result.states, (None, "G"))
        self.assertEqual(result.cost, 1)
        self.assertTrue(self.search({}, start=None, goal=None).solved)

    def test_heap_ties_do_not_compare_states(self):
        @dataclass(frozen=True)
        class State:
            n: int
        start, a, goal = State(0), State(1), State(2)
        graph = {start: [("a", a, 1), ("g", goal, 1)]}
        self.assertEqual(self.search(graph, start, goal).cost, 1)

    def test_game_state_is_opaque_and_keeps_bridge_configuration(self):
        # The solver makes no assumptions about the team's eventual state class.
        @dataclass(frozen=True)
        class State:
            placement: tuple
            open_bridges: frozenset
            active_cube: int = 0
        closed = State((2, 3, "standing"), frozenset())
        opened = State((2, 3, "standing"), frozenset({"b"}))
        goal = State((6, 3, "standing"), frozenset({"b"}))
        graph = {closed: [("press", opened, 1)], opened: [("cross", goal, 1)]}
        result = self.search(graph, closed, goal)
        self.assertEqual(result.states, (closed, opened, goal))
        self.assertEqual(result.cost, 2)

    def test_limits_are_distinct_from_unsolvable(self):
        graph = {"S": [("finish", "G", 1)]}
        result = self.search(graph, max_expanded=0)
        self.assertEqual(result.status, "limit_reached")
        self.assertEqual(result.expanded_nodes, 0)
        self.assertIsNone(result.cost)
        self.assertEqual(self.search(graph, timeout_seconds=0).status, "timeout")
        self.assertTrue(self.search(graph, max_expanded=1).solved)

    def test_timeout_between_successor_yields(self):
        with patch("solvers.astar.time.perf_counter", side_effect=[0, 0, 2, 2]):
            result = self.search({"S": [("go", "G", 1)]}, timeout_seconds=1,
                                 measure_memory=False)
        self.assertEqual(result.status, "timeout")
        self.assertEqual(result.generated_nodes, 1)

    def test_invalid_parameters(self):
        for options in ({"max_expanded": -1}, {"max_expanded": True},
                        {"max_expanded": 1.5}, {"timeout_seconds": -1},
                        {"timeout_seconds": math.inf}, {"timeout_seconds": math.nan}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.search({}, **options)

    def test_invalid_costs_and_heuristics_cleanup_memory_tracing(self):
        for value in (-1, math.inf, math.nan):
            with self.subTest(edge=value), self.assertRaises(ValueError):
                self.search({"S": [("bad", "G", value)]})
            self.assertFalse(tracemalloc.is_tracing())
            with self.subTest(heuristic=value), self.assertRaises(ValueError):
                self.search({}, heuristic=lambda _: value)
            self.assertFalse(tracemalloc.is_tracing())
        with self.assertRaisesRegex(ValueError, "cost overflowed"):
            self.search({"S": [("a", "A", 1e308)], "A": [("b", "G", 1e308)]})
        with self.assertRaisesRegex(ValueError, "priority overflowed"):
            self.search({"S": [("g", "G", 1e308)]},
                        heuristic=lambda state: 0 if state == "S" else 1e308)
        self.assertFalse(tracemalloc.is_tracing())

    def test_callback_exception_cleans_up_tracing(self):
        def broken(_):
            raise LookupError("core callback failed")
        with self.assertRaisesRegex(LookupError, "core callback failed"):
            astar("S", lambda _: False, broken)
        self.assertFalse(tracemalloc.is_tracing())

    def test_external_memory_trace_is_not_reset(self):
        self.assertIsNone(self.search({}, measure_memory=False).peak_memory_bytes)
        tracemalloc.start()
        try:
            with self.assertRaisesRegex(RuntimeError, "already active"):
                self.search({})
            self.assertIsNone(self.search({}, measure_memory=False).peak_memory_bytes)
            self.assertTrue(tracemalloc.is_tracing())
        finally:
            tracemalloc.stop()

    def test_heuristic_geometry_orientation_and_cost_scaling(self):
        self.assertEqual(bloxorz_heuristic([(0, 0)], (6, 0), standing=True), 3)
        self.assertEqual(bloxorz_heuristic([(4, 0), (5, 0)], (6, 0), standing=False), 1)
        self.assertEqual(bloxorz_heuristic([(5, 0), (6, 0)], (6, 0), standing=False), 1)
        self.assertEqual(bloxorz_heuristic([(6, 0)], (6, 0), standing=True), 0)
        self.assertEqual(bloxorz_heuristic([(0, 0)], (6, 0), standing=True,
                                          min_move_cost=0.5), 1.5)
        for flag in ({"has_teleports": True}, {"split": True}):
            self.assertEqual(bloxorz_heuristic([(0, 0)], (100, 100),
                                              standing=True, **flag), 0)
        with self.assertRaises(ValueError):
            bloxorz_heuristic([], (0, 0), standing=True)
        for cost in (-1, math.inf, math.nan):
            with self.subTest(cost=cost), self.assertRaises(ValueError):
                bloxorz_heuristic([(0, 0)], (1, 1), standing=True, min_move_cost=cost)

    def test_predefined_bloxorz_corridor_is_optimal_and_consistent(self):
        route = ((0, "standing"), (1, "horizontal"), (3, "standing"),
                 (4, "horizontal"), (6, "standing"))
        graph = {state: [] for state in route}
        for left, right in zip(route, route[1:]):
            graph[left].append(("right", right, 1))
            graph[right].append(("left", left, 1))
        def h(state):
            x, orientation = state
            cells = [(x, 0)] if orientation == "standing" else [(x, 0), (x + 1, 0)]
            return bloxorz_heuristic(cells, (6, 0), standing=orientation == "standing")
        for i, state in enumerate(route):
            self.assertLessEqual(h(state), len(route) - 1 - i)
            for _, following, cost in graph[state]:
                self.assertLessEqual(h(state), cost + h(following))
        result = self.search(graph, route[0], route[-1], h)
        self.assertEqual(result.cost, 4)
        self.assertEqual(result.actions, ("right",) * 4)
        self.assertEqual(result.states, route)

    def test_random_weighted_graphs_match_independent_dijkstra(self):
        def distances(graph, start):
            pending, settled = {start: 0}, {}
            while pending:
                state = min(pending, key=pending.get)
                cost = pending.pop(state)
                settled[state] = cost
                for _, neighbor, edge in graph.get(state, ()):
                    if neighbor not in settled:
                        pending[neighbor] = min(pending.get(neighbor, math.inf), cost + edge)
            return settled

        rng = random.Random(2026)
        solved = unsolvable = 0
        for case in range(40):
            graph = {n: [] for n in range(12)}
            reverse = {n: [] for n in range(12)}
            for source in graph:
                for target in graph:
                    if rng.random() < 0.12:
                        cost = rng.choice((0, 0.5, 1, 2, 4))
                        graph[source].append((f"{source}->{target}", target, cost))
                        reverse[target].append((None, source, cost))
            actual = distances(graph, 0).get(11)
            remaining = distances(reverse, 11)
            # Always admissible, potentially inconsistent: exercises reopening.
            h = {n: remaining.get(n, 0) * rng.choice((0, 0.25, 0.75, 1)) for n in graph}
            result = self.search(graph, 0, 11, h.__getitem__)
            with self.subTest(case=case):
                self.assertEqual(result.cost, actual)
                if actual is None:
                    unsolvable += 1
                    self.assertEqual(result.status, "unsolvable")
                else:
                    solved += 1
                    self.assertEqual(result.states[0], 0)
                    self.assertEqual(result.states[-1], 11)
                    replay_cost = 0
                    for state, action, following in zip(result.states, result.actions,
                                                         result.states[1:]):
                        replay_cost += next(c for a, n, c in graph[state]
                                            if a == action and n == following)
                    self.assertEqual(replay_cost, actual)
        self.assertGreater(solved, 0)
        self.assertGreater(unsolvable, 0)

    def test_single_file_runs_without_repo_or_installed_packages(self):
        source = Path(__file__).resolve().parents[1] / "solvers/astar.py"
        with tempfile.TemporaryDirectory() as directory:
            copied = shutil.copyfile(source, Path(directory) / "astar.py")
            process = subprocess.run([sys.executable, "-I", "-S", str(copied)],
                                     cwd=directory, text=True, capture_output=True,
                                     timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(result["status"], "solved")
        self.assertEqual(result["actions"], ["right"] * 4)
        self.assertEqual(result["solution_length"], 4)


if __name__ == "__main__":
    unittest.main()
