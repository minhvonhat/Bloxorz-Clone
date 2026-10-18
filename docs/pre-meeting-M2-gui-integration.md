# Day 1 Pre-Meeting Brief — M2: GUI, Input & Solver Integration

**Meeting objective:** Freeze how users play, launch solvers, observe metrics, and replay solutions without tying the GUI to solver internals or blocking its event loop.

## Role & Core Focus

Own the user-facing application: board and block rendering, keyboard/button input, level/restart controls, solver selection, result/error presentation, and solution playback. The GUI consumes immutable `GameState` values and the shared level/solver contracts; it does not implement game rules or search.

**Boundary:** Do not import search implementation details or mutate core state. Route user actions through M1's transition API. Keep UI toolkit decisions explicit: the plan says Pygame-CE, while the current scaffold includes `ui/tk_app.py` and describes Pygame in its README. Resolve and record the toolkit before implementation is split.

## Required Interface Proposals

Bring a UI-to-application contract with typed requests and results. Suggested boundary:

```python
class SolverName(Enum):
    BFS = "bfs"
    DFS = "dfs"       # or IDS, but name the selected implementation
    UCS = "ucs"
    ASTAR = "astar"

@dataclass(frozen=True)
class SolveRequest:
    request_id: str
    solver: SolverName
    level_id: str
    start_state: GameState

@dataclass(frozen=True)
class SolveFinished:
    request_id: str
    result: SolverResult

def request_solve(request: SolveRequest) -> str: ...
def cancel_solve(request_id: str) -> None: ...
def poll_solver_events() -> list[SolveStarted | SolveProgress | SolveFinished]: ...
def replay_action(state: GameState, action: Action) -> GameState: ...
```

The GUI must not call a long-running search synchronously from its event callback. Propose a worker boundary (thread/process) and a main-loop-safe event/queue contract. Only the UI thread updates widgets or draws frames. Request IDs must prevent stale results from replacing the current level/session; define how cancellation/window-close avoids leaving a worker behind.

Bring a playback contract that maps a returned action sequence to states by replaying actions through the core transition function—never by reimplementing movement. Freeze:

- Controls: New Game/level selection, Restart, four directional moves, solver buttons, and (when split) `SPACE`/cube switch.
- `SolverResult` presentation: found/unsolvable/limit/cancelled/error status, path, solution length, cost, expanded nodes, elapsed time, peak memory, and clear failure text.
- Playback policy: step duration, pause/stop/restart behavior, and what happens if a user input arrives mid-playback.
- Visual legend for floor, void, goal, fragile, bridge open/closed, switch type, block orientation, split cubes, win, and loss.

Propose a minimal view model so rendering does not depend on solver classes:

```python
@dataclass(frozen=True)
class GameView:
    level: Level
    state: GameState
    status_message: str
    solver_result: SolverResult | None
    playback_index: int | None
```

## Critical Thinking Questions

1. Which toolkit is the team freezing—Pygame-CE or Tkinter—and what exact existing scaffold/dependency will be retained or retired?
2. How will the GUI remain responsive while Python search runs? What is the worker-to-UI result channel, and how will cancellation/window-close avoid leaving a worker or stale result behind?
3. How will playback reconstruct states for `SPACE`, split teleport, switch-triggered bridge changes, and other actions? What prevents the displayed replay from diverging from core rules?
4. What is the defined behavior when solver output is unsolvable, hits a resource limit, errors, or is cancelled? Which metrics are shown and which must remain available for the experiment export?

## Day 1 Commitments

- Present a toolkit recommendation grounded in the current scaffold and confirm the choice with the team.
- Bring the typed solve-request/event and playback proposals, including the main-thread boundary.
- Agree on action/key names, solver IDs (including DFS versus IDS), UI-visible result states, and the metrics labels/units.
- Leave the meeting with a frozen UI adapter contract, an interaction/control checklist, and a mock-screen or smoke-test plan that covers normal, solver-running, solved, unsolvable, and split-block states.
