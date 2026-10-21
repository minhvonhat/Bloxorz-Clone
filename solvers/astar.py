"""A* graph search with reopening, path reconstruction and measured statistics."""
from __future__ import annotations

import heapq
import itertools
import math
import time
import tracemalloc
from typing import Callable

from core.board import Board
from core.game_state import GameState
from solvers.common import BloxorzProblem, SearchProblem, SearchResult, StateT, ActionT


def heuristic(board: Board, state: GameState) -> int:
    """Admissible/consistent for unit rolls and free cube selection.

    Without teleports, nearest-occupied-cell Manhattan distance can decrease
    by at most two per roll. ceil(distance / 2) is therefore a lower bound.
    Lying states need at least one roll; max (not sum) preserves the bound.
    Teleports can defeat geometric bounds, so such levels use zero globally.
    """
    if board.has_teleports or state.block is None:
        return 0
    gx, gy = board.goal
    distance = min(abs(x - gx) + abs(y - gy) for x, y in state.cells)
    return max((distance + 1) // 2, int(len(state.cells) == 2))


def astar_search(
    problem: SearchProblem[StateT, ActionT],
    estimate: Callable[[StateT], float] | None = None,
    *,
    max_expanded: int | None = None,
    timeout_seconds: float | None = None,
    measure_memory: bool = True,
) -> SearchResult[StateT, ActionT]:
    """Find a minimum-cost path with an admissible heuristic (default h=0).

    Successors yield (action, state, nonnegative_cost). State keys must be
    immutable/hashable. Reopening supports admissible inconsistent heuristics.
    Node counts: expanded = non-goal nodes whose successors were enumerated;
    generated = start + successful strict g improvements, including reopens.
    Limits return a distinct status, never an 'unsolvable' claim.

    tracemalloc measures Python allocations, not process RSS. A pre-existing
    trace is rejected rather than reset or silently contaminate the metric;
    pass measure_memory=False to leave external profiling untouched.
    """
    if max_expanded is not None and (type(max_expanded) is not int or max_expanded < 0):
        raise ValueError("max_expanded must be a nonnegative integer")
    if timeout_seconds is not None and (
            not math.isfinite(timeout_seconds) or timeout_seconds < 0):
        raise ValueError("timeout_seconds must be finite and nonnegative")
    if measure_memory and tracemalloc.is_tracing():
        raise RuntimeError("Memory tracing is already active; use measure_memory=False")
    estimate = estimate if estimate is not None else lambda state: 0
    started = time.perf_counter()
    if measure_memory:
        tracemalloc.start()
    try:
        def checked_h(state):
            value = float(estimate(state))
            if not math.isfinite(value) or value < 0:
                raise ValueError("Heuristic must be finite and nonnegative")
            return value

        start = problem.initial_state
        sequence = itertools.count()
        frontier = [(checked_h(start), next(sequence), 0.0, start)]
        best_g = {start: 0.0}
        parents: dict[StateT, tuple[StateT, ActionT]] = {}
        expanded, generated = 0, 1
        final = None
        status = "unsolvable"
        while frontier:
            if timeout_seconds is not None and time.perf_counter() - started >= timeout_seconds:
                status = "timeout"
                break
            _, _, g, state = heapq.heappop(frontier)
            if g != best_g[state]:
                continue  # An improved entry superseded this heap item.
            if problem.is_goal(state):
                final, status = state, "solved"
                break
            if max_expanded is not None and expanded >= max_expanded:
                status = "limit_reached"
                break
            expanded += 1
            for action, neighbor, cost in problem.successors(state):
                cost = float(cost)
                if not math.isfinite(cost) or cost < 0:
                    raise ValueError("Edge costs must be finite and nonnegative")
                candidate_g = g + cost
                if not math.isfinite(candidate_g):
                    raise ValueError("Accumulated path cost overflowed")
                if candidate_g >= best_g.get(neighbor, math.inf):
                    continue
                h = checked_h(neighbor)
                best_g[neighbor] = candidate_g
                parents[neighbor] = (state, action)
                heapq.heappush(frontier, (candidate_g + h, next(sequence),
                                         candidate_g, neighbor))
                generated += 1
        actions, states = [], []
        if status == "solved":
            cursor = final
            states.append(cursor)
            while cursor != start:
                cursor, action = parents[cursor]
                actions.append(action)
                states.append(cursor)
            actions.reverse()
            states.reverse()
        peak = tracemalloc.get_traced_memory()[1] if measure_memory else None
        return SearchResult(status, tuple(actions), tuple(states),
                            best_g[final] if status == "solved" else None,
                            expanded, generated, time.perf_counter() - started, peak)
    finally:
        if measure_memory:
            tracemalloc.stop()


def solve(board: Board, start: GameState | None = None, **options) -> SearchResult:
    """GUI/API entry point. Pass current GameState to solve from mid-game."""
    return astar_search(BloxorzProblem(board, start),
                        lambda state: heuristic(board, state), **options)


def main() -> int:
    import argparse
    import json
    from levels.level_loader import load_level

    parser = argparse.ArgumentParser(description="Solve Bloxorz using A*")
    parser.add_argument("level", help="Path to a level JSON file")
    parser.add_argument("--max-expanded", type=int, default=None)
    parser.add_argument("--timeout", type=float, default=None, help="Search seconds")
    args = parser.parse_args()
    try:
        result = solve(load_level(args.level), max_expanded=args.max_expanded,
                       timeout_seconds=args.timeout)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "status": result.status,
        "actions": [action.value for action in result.actions],
        "cost": result.cost,
        "solution_length": result.solution_length,
        "expanded_nodes": result.expanded_nodes,
        "generated_nodes": result.generated_nodes,
        "search_time_seconds": result.search_time_seconds,
        "peak_memory_bytes": result.peak_memory_bytes,
    }, indent=2))
    return 0 if result.solved else 1


if __name__ == "__main__":
    raise SystemExit(main())
