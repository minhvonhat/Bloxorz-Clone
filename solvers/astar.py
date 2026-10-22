"""Standalone A* solver (Python 3.10+, standard library only).

The game supplies hashable states and callbacks for legal successors and goals.
No imports from core, GUI, level loaders or other solver modules are required.
Run this file directly for a small, predefined Bloxorz corridor demonstration.
"""
from __future__ import annotations

from dataclasses import dataclass
import heapq
import itertools
import math
import time
import tracemalloc
from typing import Callable, Generic, Hashable, Iterable, Literal, TypeVar

StateT = TypeVar("StateT", bound=Hashable)
ActionT = TypeVar("ActionT")
Status = Literal["solved", "unsolvable", "limit_reached", "timeout"]


@dataclass(frozen=True)
class SearchResult(Generic[StateT, ActionT]):
    status: Status
    actions: tuple[ActionT, ...]
    states: tuple[StateT, ...]
    cost: float | None
    expanded_nodes: int
    generated_nodes: int
    search_time_seconds: float
    peak_memory_bytes: int | None

    @property
    def solved(self) -> bool:
        return self.status == "solved"

    @property
    def solution_length(self) -> int:
        """Number of returned actions, including any zero-cost actions."""
        return len(self.actions)


def bloxorz_heuristic(
    occupied_cells: Iterable[tuple[int, int]],
    goal: tuple[int, int],
    *,
    standing: bool,
    has_teleports: bool = False,
    split: bool = False,
    min_move_cost: float = 1.0,
) -> float:
    """Model-independent lower bound; coordinates are integer (x, y) pairs.

    Each geometric move must cost at least min_move_cost. Free control changes
    may cost zero because they do not change occupied cells. For whole blocks
    without teleports: h = max(ceil(nearest Manhattan / 2), lying penalty).
    Use max, not addition, to avoid counting the same move twice.

    If ANY split/teleport is possible on the level, set has_teleports=True for
    every state, including states before splitting. Geometry alone is unsafe
    with teleports, so that case (and split states) conservatively returns zero.
    """
    if not math.isfinite(min_move_cost) or min_move_cost < 0:
        raise ValueError("min_move_cost must be finite and nonnegative")
    if has_teleports or split:
        return 0.0
    gx, gy = goal
    distance = min((abs(x - gx) + abs(y - gy) for x, y in occupied_cells),
                   default=None)
    if distance is None:
        raise ValueError("occupied_cells must contain at least one cell")
    return max(math.ceil(distance / 2), int(not standing)) * min_move_cost


def astar(
    initial_state: StateT,
    is_goal: Callable[[StateT], bool],
    get_successors: Callable[[StateT], Iterable[tuple[ActionT, StateT, float]]],
    heuristic: Callable[[StateT], float] | None = None,
    *,
    max_expanded: int | None = None,
    timeout_seconds: float | None = None,
    measure_memory: bool = True,
) -> SearchResult[StateT, ActionT]:
    """Find a minimum-cost path with an admissible heuristic (default h=0).

    get_successors(state) yields (action, next_state, nonnegative_cost).
    States must be immutable/hashable and include ALL data affecting future
    moves: orientation, bridge/lock states, split positions, active cube, etc.
    Callbacks must describe a fixed, deterministic graph during the search.

    A state is reopened on a strictly better g, supporting admissible but
    inconsistent heuristics. Stale heap entries and zero-cost cycles are safe.
    expanded_nodes counts successor enumerations, including reopens, excluding
    the goal. generated_nodes counts the start plus strict g improvements.

    Memory is peak traced Python allocations during search, not process RSS.
    Existing tracemalloc sessions are left alone: disable measure_memory when
    profiling externally. Timeouts are cooperative between callback yields;
    this function cannot interrupt a callback that blocks indefinitely.
    """
    if max_expanded is not None and (
            type(max_expanded) is not int or max_expanded < 0):
        raise ValueError("max_expanded must be a nonnegative integer")
    if timeout_seconds is not None and (
            not math.isfinite(timeout_seconds) or timeout_seconds < 0):
        raise ValueError("timeout_seconds must be finite and nonnegative")
    if measure_memory and tracemalloc.is_tracing():
        raise RuntimeError("Memory tracing is already active; use measure_memory=False")
    estimate = heuristic if heuristic is not None else lambda _: 0.0
    started = time.perf_counter()
    if measure_memory:
        tracemalloc.start()
    try:
        def checked_h(state):
            value = float(estimate(state))
            if not math.isfinite(value) or value < 0:
                raise ValueError("Heuristic must be finite and nonnegative")
            return value

        def expired():
            return (timeout_seconds is not None
                    and time.perf_counter() - started >= timeout_seconds)

        sequence = itertools.count()
        # The sequence number prevents comparing arbitrary state objects on ties.
        frontier = [(checked_h(initial_state), next(sequence), 0.0, initial_state)]
        best_g = {initial_state: 0.0}
        parents: dict[StateT, tuple[StateT, ActionT]] = {}
        expanded, generated = 0, 1
        final_state = None
        status: Status = "unsolvable"

        while frontier:
            if expired():
                status = "timeout"
                break
            _, _, g, state = heapq.heappop(frontier)
            if g != best_g[state]:
                continue
            if is_goal(state):
                final_state, status = state, "solved"
                break
            if max_expanded is not None and expanded >= max_expanded:
                status = "limit_reached"
                break
            expanded += 1
            for action, neighbor, edge_cost in get_successors(state):
                if expired():
                    status = "timeout"
                    break
                edge_cost = float(edge_cost)
                if not math.isfinite(edge_cost) or edge_cost < 0:
                    raise ValueError("Edge costs must be finite and nonnegative")
                candidate_g = g + edge_cost
                if not math.isfinite(candidate_g):
                    raise ValueError("Accumulated path cost overflowed")
                if candidate_g >= best_g.get(neighbor, math.inf):
                    continue
                priority = candidate_g + checked_h(neighbor)
                if not math.isfinite(priority):
                    raise ValueError("A* priority overflowed")
                best_g[neighbor] = candidate_g
                parents[neighbor] = (state, action)
                heapq.heappush(frontier, (priority, next(sequence), candidate_g, neighbor))
                generated += 1
            if status == "timeout":
                break

        actions, states = [], []
        if status == "solved":
            cursor = final_state
            states.append(cursor)
            while cursor != initial_state:
                cursor, action = parents[cursor]
                actions.append(action)
                states.append(cursor)
            actions.reverse()
            states.reverse()
        peak = tracemalloc.get_traced_memory()[1] if measure_memory else None
        return SearchResult(
            status=status, actions=tuple(actions), states=tuple(states),
            cost=best_g[final_state] if status == "solved" else None,
            expanded_nodes=expanded, generated_nodes=generated,
            search_time_seconds=time.perf_counter() - started,
            peak_memory_bytes=peak,
        )
    finally:
        if measure_memory:
            tracemalloc.stop()


def _demo() -> None:
    """A fixed transition table, not an implementation of the game's core."""
    import json

    # A seven-cell corridor: stand(0), lie(1,2), stand(3), lie(4,5), stand(6).
    route = ((0, "standing"), (1, "horizontal"), (3, "standing"),
             (4, "horizontal"), (6, "standing"))
    graph = {state: [] for state in route}
    for left, right in zip(route, route[1:]):
        graph[left].append(("right", right, 1))
        graph[right].append(("left", left, 1))

    def estimate(state):
        x, orientation = state
        cells = [(x, 0)] if orientation == "standing" else [(x, 0), (x + 1, 0)]
        return bloxorz_heuristic(cells, (6, 0), standing=orientation == "standing")

    result = astar(route[0], lambda state: state == route[-1], graph.__getitem__, estimate)
    print(json.dumps({
        "demo": "predefined Bloxorz corridor transitions; no level loader required",
        "status": result.status, "actions": result.actions, "cost": result.cost,
        "solution_length": result.solution_length,
        "expanded_nodes": result.expanded_nodes,
        "generated_nodes": result.generated_nodes,
        "search_time_seconds": result.search_time_seconds,
        "peak_memory_bytes": result.peak_memory_bytes,
    }, indent=2))


if __name__ == "__main__":
    _demo()
