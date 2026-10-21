"""Behavioral tests, including an independent shortest-path oracle."""
from collections import deque
from dataclasses import dataclass
from pathlib import Path
import math
import random
import tracemalloc

import pytest

from core.block import Block, Orientation
from core.board import Board, Bridge, Switch
from core.game_state import GameState
from core.game_rules import initial_state, is_goal, is_valid, step, successors
from core.movement import Action
from levels.level_loader import load_level
from solvers.astar import astar_search, heuristic, solve


@dataclass
class Graph:
    edges: dict
    initial_state: str = "S"

    def is_goal(self, state):
        return state == "G"

    def successors(self, state):
        return self.edges.get(state, ())


def oracle_cost(board):
    """Independent Dijkstra with linear selection; handles free SWITCH edges."""
    start = initial_state(board)
    pending, settled = {start: 0}, set()
    while pending:
        state = min(pending, key=pending.get)
        cost = pending.pop(state)
        if is_goal(board, state):
            return cost
        settled.add(state)
        for _, neighbor, edge in successors(board, state):
            if neighbor not in settled:
                pending[neighbor] = min(pending.get(neighbor, math.inf), cost + edge)
    return None


def assert_replay(board, result):
    assert result.solved and result.states[0] == initial_state(board)
    assert len(result.states) == len(result.actions) + 1
    for state, action, expected in zip(result.states, result.actions, result.states[1:]):
        assert step(board, state, action) == expected
    assert is_goal(board, result.states[-1])
    assert result.cost == result.solution_length
    assert result.search_time_seconds >= 0
    assert result.peak_memory_bytes > 0


def test_repository_level_optimal_solution_and_replay():
    board = load_level(Path(__file__).resolve().parents[1] / "levels/level_01.json")
    result = solve(board)
    assert result.cost == oracle_cost(board) == 9
    assert_replay(board, result)


def test_forced_bridge_opening_solution():
    board = Board(7, 1, frozenset((x, 0) for x in (0, 1, 2, 4, 5, 6)),
                  Block(0, 0), (6, 0),
                  bridges=(Bridge("b", frozenset({(3, 0)})),),
                  switches=(Switch("s", "soft", (1, 0), ("b",)),))
    result = solve(board)
    assert result.cost == oracle_cost(board) == 4
    assert result.states[1].open_bridges == frozenset({"b"})
    assert_replay(board, result)


def test_forced_teleport_cube_selection_rejoin_and_goal():
    tiles = frozenset({(2, 0), (3, 0), (4, 0), (5, 0)} |
                      {(0, y) for y in range(1, 6)})
    board = Board(6, 6, tiles, Block(2, 0), (0, 1),
                  fragile_tiles=frozenset({(0, 3)}),
                  switches=(Switch("split", "split", (5, 0),
                                   destinations=((0, 2), (0, 5))),))
    result = solve(board)
    assert result.cost == oracle_cost(board) == 5
    assert Action.SWITCH in result.actions
    assert len(result.actions) == result.solution_length + 1
    assert any(state.block is None for state in result.states)
    assert all(heuristic(board, state) == 0 for state in result.states)
    assert_replay(board, result)


def test_search_can_start_from_current_game_state():
    board = Board(7, 1, frozenset((x, 0) for x in range(7)), Block(0, 0), (6, 0))
    current = step(board, initial_state(board), "right")
    result = solve(board, start=current)
    assert result.cost == 3 and result.states[0] == current
    with pytest.raises(ValueError):
        solve(board, start=GameState(Block(99, 99)))


def test_reopens_state_with_admissible_inconsistent_heuristic():
    # C is expanded with g=4, then B discovers a better g=3.
    graph = Graph({"S": [("sa", "A", 2), ("sb", "B", 2)],
                   "A": [("ac", "C", 2)], "B": [("bc", "C", 1)],
                   "C": [("cg", "G", 2)]})
    h = {"S": 0, "A": 0, "B": 3, "C": 0, "G": 0}
    result = astar_search(graph, h.__getitem__)
    assert result.cost == 5
    assert result.actions == ("sb", "bc", "cg")
    assert result.states == ("S", "B", "C", "G")
    assert result.expanded_nodes == 5  # S, A, C, B, C


def test_stale_entries_zero_cost_cycle_and_unorderable_ties():
    graph = Graph({"S": [("expensive", "A", 10), ("cheap", "B", 1)],
                   "B": [("back", "S", 0), ("improve", "A", 1)],
                   "A": [("stay", "A", 0)]})
    result = astar_search(graph)
    assert result.status == "unsolvable" and result.expanded_nodes == 3
    assert result.cost is None and not result.actions and not result.states

    @dataclass(frozen=True)
    class Key:
        n: int

    class Tied:
        initial_state = Key(0)

        def is_goal(self, state):
            return state.n == 2

        def successors(self, state):
            return [("one", Key(1), 1), ("two", Key(2), 1)] if state.n == 0 else []

    assert astar_search(Tied()).cost == 1  # heap never compares state objects


def test_limits_start_goal_and_memory_mode():
    graph = Graph({"S": [("finish", "G", 1)]})
    result = astar_search(graph, max_expanded=0)
    assert result.status == "limit_reached" and not result.solved
    assert result.expanded_nodes == 0
    assert astar_search(graph, timeout_seconds=0).status == "timeout"
    result = astar_search(Graph({}, initial_state="G"), max_expanded=0)
    assert result.solved and result.cost == 0 and result.states == ("G",)
    assert result.actions == () and result.expanded_nodes == 0
    assert astar_search(graph, measure_memory=False).peak_memory_bytes is None


@pytest.mark.parametrize("bad", [-1, math.nan, math.inf])
def test_rejects_invalid_edge_costs_and_cleans_up_tracing(bad):
    with pytest.raises(ValueError):
        astar_search(Graph({"S": [("bad", "G", bad)]}))
    assert not tracemalloc.is_tracing()


@pytest.mark.parametrize("bad", [-1, math.nan, math.inf])
def test_rejects_invalid_heuristics(bad):
    with pytest.raises(ValueError):
        astar_search(Graph({}), lambda _: bad)
    assert not tracemalloc.is_tracing()


@pytest.mark.parametrize("options", [
    {"max_expanded": -1}, {"max_expanded": 1.5},
    {"timeout_seconds": -1}, {"timeout_seconds": math.inf},
])
def test_invalid_limits(options):
    with pytest.raises(ValueError):
        astar_search(Graph({}), **options)


def test_external_memory_tracing_is_preserved():
    tracemalloc.start()
    try:
        with pytest.raises(RuntimeError, match="already active"):
            astar_search(Graph({}))
        assert tracemalloc.is_tracing()
        astar_search(Graph({}), measure_memory=False)
        assert tracemalloc.is_tracing()
    finally:
        tracemalloc.stop()


def test_random_small_boards_match_independent_shortest_path():
    randomizer = random.Random(2026)
    solved = unsolvable = 0
    for _ in range(30):
        tiles = {(x, y) for x in range(6) for y in range(5)
                 if randomizer.random() > 0.22}
        start, goal = (0, 0), (5, 4)
        tiles.update((start, goal))
        fragile = frozenset(p for p in sorted(tiles - {start, goal})
                            if randomizer.random() < 0.1)
        board = Board(6, 5, frozenset(tiles), Block(*start), goal, fragile)
        result, expected = solve(board), oracle_cost(board)
        assert result.cost == expected
        if expected is None:
            unsolvable += 1
            assert result.status == "unsolvable"
        else:
            solved += 1
            assert_replay(board, result)
    assert solved > 0 and unsolvable > 0


def test_heuristic_admissibility_and_consistency_on_entire_small_state_space():
    board = Board(6, 5, frozenset((x, y) for x in range(6) for y in range(5)),
                  Block(0, 0), (5, 4), fragile_tiles=frozenset({(2, 2)}))
    states = [GameState(Block(x, y, orientation)) for x in range(6)
              for y in range(5) for orientation in Orientation]
    states = [state for state in states if is_valid(board, state)]
    reverse = {state: [] for state in states}
    for state in states:
        for _, neighbor, cost in successors(board, state):
            assert heuristic(board, state) <= cost + heuristic(board, neighbor)
            reverse[neighbor].append(state)
    goal = GameState(Block(*board.goal))
    distances, pending = {goal: 0}, deque([goal])
    while pending:
        state = pending.popleft()
        for previous in reverse[state]:
            if previous not in distances:
                distances[previous] = distances[state] + 1
                pending.append(previous)
    assert len(distances) > 20
    for state, exact_cost in distances.items():
        assert heuristic(board, state) <= exact_cost
    assert heuristic(board, goal) == 0
    assert heuristic(board, GameState(Block(4, 4, "horizontal"))) == 1
