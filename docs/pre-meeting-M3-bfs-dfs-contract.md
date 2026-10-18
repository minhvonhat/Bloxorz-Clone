# Day 1 Pre-Meeting Brief — M3: BFS, DFS/IDS & Shared Solver Contract

**Meeting objective:** Freeze the solver-facing API and deliver a well-tested baseline for unweighted and depth-first search that every algorithm can use consistently.

## Role & Core Focus

Own BFS and DFS (or IDS, with the choice explicitly recorded), common solver result/status types, and shared metric definitions/harness in coordination with M4 and M5. Validate search behavior against small, deterministic graph fixtures first, then against real level transitions after M1 integrates the core.

**Boundary:** Solvers consume only the public core API and level/state values. No Pygame/Tkinter, rendering, direct board mutation, or algorithm-specific assumptions in the game engine.

## Required Interface Proposals

Bring a common protocol and stable result shape:

```python
class SearchStatus(Enum):
    FOUND = "found"
    UNSOLVABLE = "unsolvable"
    LIMIT_REACHED = "limit_reached"
    CANCELLED = "cancelled"

@dataclass(frozen=True)
class SolverResult:
    status: SearchStatus
    path: tuple[Action, ...] | None
    solution_length: int | None     # number of actions in path; specify SPACE policy
    total_cost: float | None
    expanded_nodes: int
    generated_nodes: int
    peak_frontier_size: int
    search_time_ms: float
    peak_memory_kb: int

class Solver(Protocol):
    def solve(
        self,
        level: Level,
        start: GameState,
        *,
        limits: SearchLimits | None = None,
        cancel: CancelToken | None = None,
    ) -> SolverResult: ...
```

Bring concrete limit/cancellation types:

```python
@dataclass(frozen=True)
class SearchLimits:
    max_expanded_nodes: int | None = None
    timeout_ms: float | None = None

class CancelToken(Protocol):
    @property
    def cancelled(self) -> bool: ...
```

Use a shared successor contract from M1 (`Transition(action, state, events)`); cost is supplied by a solver policy, not hidden in a mock-only graph.

Metric rules to propose:

- `expanded_nodes`: states removed from the frontier and actually examined, excluding a goal returned before expansion (or state the alternative).
- `generated_nodes`: legal successor transitions considered; specify treatment of duplicates.
- `solution_length`: count of returned actions, including `SPACE` if it is in the path; optionally report roll count separately.
- `search_time_ms`: monotonic wall-clock around search only; exclude UI rendering, level loading, and experiment serialization.
- `peak_memory_kb`: define whether this is Python-traced allocations (`tracemalloc`) or process peak RSS. Do not label one as the other.
- Run each measurement in an isolated, repeatable run; report the aggregation method (e.g., median across repeated runs) and preserve raw results.

Bring a mock operations seam so search can run against a deterministic graph before the real movement engine is ready. The solver keeps the planned `solve(level, start)` shape; its successor/goal operations should be injectable for tests, defaulting to M1's production functions. Give each fixture explicit immutable states, adjacency, and goal states:

```python
@dataclass(frozen=True)
class MockSearchGraph:
    adjacency: Mapping[GameState, tuple[Transition, ...]]
    goals: frozenset[GameState]

    def successors(self, state: GameState, level: Level) -> tuple[Transition, ...]: ...
    def is_goal(self, state: GameState, level: Level) -> bool: ...

def make_mock_graph(edges, start, goals) -> MockSearchGraph: ...
def mock_level_with_bridge_mask_pair() -> tuple[GameState, GameState]: ...
```

The two bridge fixture states must have identical block placement but distinct `bridge_mask` values, proving that state identity does not collapse them. The graph fixture validates generic search mechanics; separate integration fixtures using M1's real `get_successors` must validate fragile, bridge, switch, and split semantics. Freeze how the solver receives the mock operations (constructor injection or a small `SearchOperations` protocol) rather than importing a test stub into production code.

## Critical Thinking Questions

1. What is DFS/IDS's finite-search policy? How does it avoid cycles while preserving completeness (and what solution-quality guarantee does the selected variant provide)?
2. When `GameState` objects differ only by `bridge_mask`, activated-switch state, or active cube, will they remain distinct in `visited` and predecessor maps?
3. How will a search distinguish truly unsolvable from cancelled/resource-limited, and what result fields are meaningful when no path is returned?
4. What precisely do the four required measurements include/exclude, and can the team reproduce them on a clean run without GUI timing or stale `tracemalloc` state?

## Day 1 Commitments

- Propose and obtain agreement on `Solver`, `SolverResult`, action/path, status, metric, and limit semantics.
- Bring BFS and DFS/IDS pseudocode plus a test matrix for shortest path, cycles, unreachable goal, duplicate successors, and bridge-distinct states.
- Agree with M4/M5 on whether the shared metric harness is a wrapper or solver-owned instrumentation; avoid mutating a frozen result object after solve.
- Sign off on the interface and commit to a mock test module with fixed graph fixtures and a real-core integration gate before final experiments.
