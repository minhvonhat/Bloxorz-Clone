# Day 1 Pre-Meeting Brief — M1: Core Mechanics & Level Contract

**Meeting objective:** Arrive ready to freeze the authoritative game-state model, level schema, and deterministic transition contract. Core mechanics must be reusable by manual play, every solver, and the GUI.

## Role & Core Focus

Own the rules engine and the canonical level/state boundary: block geometry and orientation, legal movement, fragile-tile failure, bridge passability, switch effects, split/rejoin behavior, goal testing, and level validation. Keep this layer deterministic, GUI-independent, and importable by all solvers.

**Boundary:** Do not own rendering, input handling, search strategy, or search metrics. Coordinate the movement cost boundary with M4/M5; game rules produce transitions, while each solver's configured cost policy assigns edge costs.

## Required Interface Proposals

Bring a concrete proposal (with types and examples) for the following. Proposed names are defaults; the team should freeze one consistent vocabulary and path.

### 1. Immutable, hashable search state

```python
from dataclasses import dataclass
from enum import Enum

class Orientation(Enum):
    STANDING = "standing"
    LYING_H = "lying_h"
    LYING_V = "lying_v"

@dataclass(frozen=True)
class RollingBlock:
    row: int
    col: int                 # standing cell, or top/left occupied cell
    orientation: Orientation

@dataclass(frozen=True)
class SplitBlock:
    cube_a: tuple[int, int]
    cube_b: tuple[int, int]
    active_cube: int         # 0 or 1

BlockState = RollingBlock | SplitBlock

@dataclass(frozen=True)
class GameState:
    block: BlockState
    bridge_mask: int         # bit i corresponds to canonical bridge index i
    activated_switch_mask: int  # records one-shot/locked switch activations

class Action(Enum):
    UP = "U"
    DOWN = "D"
    LEFT = "L"
    RIGHT = "R"
    SWITCH_CUBE = "SPACE"

@dataclass(frozen=True)
class GameEvent:
    kind: str                 # e.g. "switch_activated"
    source_id: str

@dataclass(frozen=True)
class Transition:
    action: Action
    state: GameState
    events: tuple[GameEvent, ...] = ()

class MoveStatus(Enum):
    MOVED = "moved"
    ILLEGAL = "illegal"
    LOST = "lost"

@dataclass(frozen=True)
class MoveResult:
    status: MoveStatus
    state: GameState | None
    reason: str | None

Cell = tuple[int, int]

class TileType(Enum):
    FLOOR = "floor"
    GOAL = "goal"
    FRAGILE = "fragile"
    BRIDGE = "bridge"

class SwitchKind(Enum):
    SOFT = "soft"
    HEAVY = "heavy"
    SPLIT = "split"

class SwitchTrigger(Enum):
    ENTER = "enter"

class BridgeMode(Enum):
    TOGGLE = "toggle"
    PERMANENT = "permanent"

@dataclass(frozen=True)
class Bridge:
    id: str
    tiles: tuple[Cell, ...]
    initially_open: bool

@dataclass(frozen=True)
class Switch:
    id: str
    kind: SwitchKind
    position: Cell
    trigger: SwitchTrigger
    bridge_ids: tuple[str, ...] = ()
    bridge_mode: BridgeMode | None = None
    target_open: bool | None = None
    lock_after_activation: bool = False
    split_destinations: tuple[Cell, Cell] | None = None

@dataclass(frozen=True)
class SplitRules:
    merge_when_adjacent: bool
    single_cube_can_win: bool

@dataclass(frozen=True)
class Level:
    id: str
    width: int
    height: int
    tiles: Mapping[Cell, TileType]
    goal: Cell
    initial_state: GameState
    bridges: tuple[Bridge, ...]
    switches: tuple[Switch, ...]
    split_rules: SplitRules
```

All fields participating in state identity must be immutable and hashable. Dynamic identity includes block mode/positions, active cube, bridge configuration, and any one-shot switch state. The loader must establish stable bridge and switch bit-index mappings for each `Level`.

```python
def occupied_cells(block: BlockState) -> tuple[tuple[int, int], ...]: ...
def is_goal(state: GameState, level: Level) -> bool: ...
def get_successors(
    state: GameState, level: Level
) -> tuple[Transition, ...]: ...
def apply_action(
    state: GameState, action: Action, level: Level
) -> MoveResult: ...
```

Keep cost out of the core transition result so BFS, UCS, and A* can apply the same game rules with their own documented cost policy. Include transition events so M4 can score switch activation without re-implementing switch-entry rules. `get_successors` returns searchable moves; manual play uses `apply_action` to distinguish a blocked move from a fragile-tile loss.

### 2. Level schema and validation

Use the existing [`levels/level_01.json`](../levels/level_01.json) as the compatibility fixture; do not replace it with the shorter example in the plan. Bring a schema proposal covering:

- `id`, dimensions, start, goal, and all supported tile coordinates.
- Bridge IDs, bridge tiles, initial open/closed state, and stable index order.
- Switch ID, type, position, trigger rule, effect type, linked bridge IDs, toggle/permanent mode, target state, and any lock-after-activation behavior.
- Split-switch destinations and `split_rules` (`SPACE`, adjacency/merge, and cube switch capabilities).
- Coordinate convention (`[row, col]`) and whether missing cells are void.

Propose `load_level(path: Path) -> Level`, with explicit validation errors for unknown IDs/types, out-of-bounds or overlapping coordinates, invalid bridge references, malformed destinations, and unsupported values. Normalize JSON `[row, col]` pairs to `Cell`, and normalize the JSON start plus bridge initial states to `Level.initial_state: GameState`; this keeps the loader and solver's start-state type consistent.

### 3. Rule semantics to freeze

Bring a short, ordered transition pipeline and unit-test cases for:

1. The 12 orientation/direction outcomes in the plan's movement table.
2. Bounds, void, and closed-bridge checks for every occupied cell.
3. Fragile behavior: lying is supported; standing on fragile causes a loss/failure, not a silently omitted successor. Confirm how the GUI presents this terminal outcome.
4. Soft switch: any occupied cell; heavy and split switches: only a standing block.
5. Switch activation on `enter`: occupying a switch continuously must not toggle on every action; leaving and re-entering can trigger again unless locked.
6. Whether a switch occupied in the initial state activates at level start, and how that is represented.
7. Toggle versus permanent bridge effects and the ordering when a switch changes a bridge under the block.
8. Split teleport destinations, cube movement, `SPACE` control, merge-on-adjacency, unsupported switch types for cubes, fragile-tile behavior for a single cube, and the rule that a split block cannot win.
9. Goal success only when the unsplit block is standing on the goal.

## Critical Thinking Questions

1. Which parts of `GameState` can change during play, and are all of them represented in equality/hash identity? In particular, how are a one-shot switch and the active split cube represented?
2. What exact result represents a fragile-tile loss versus an ordinary illegal move? How will this distinction reach manual play and search without making a losing state look like “no successor” or “unsolvable”?
3. When a switch opens/closes a bridge, what happens if the block occupies a tile that becomes closed? Specify validation and update order.
4. Does the schema in the existing sample validate without migration? What exact loader errors will callers receive for invalid references or coordinates?

## Day 1 Commitments

- Bring a typed state/action/transition proposal and a transition-order diagram.
- Walk through one example each for a fragile loss, a soft-toggle bridge, a heavy permanent switch, and split/SPACE/rejoin.
- Agree with M3/M4/M5 on stable state hashing, action names, goal and terminal semantics, and deterministic successor order.
- By meeting close, sign off on the frozen state/transition API, level schema plus sample compatibility, error policy, and tests that gate changes to these contracts. Record any unresolved rule as an owner and due time; do not leave it implicit in a `dict` or comment.
