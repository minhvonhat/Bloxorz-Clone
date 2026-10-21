"""Pure transitions shared by A* and future manual play/other solvers.

Switches fire on entering their activation condition. Destinations must be
supported before and after effects; split teleports do not chain-trigger other
switches in the same turn. A permanent lock applies to its linked bridges.
"""
from dataclasses import replace
from core.block import Block, Orientation
from core.board import Board, Switch
from core.game_state import GameState
from core.movement import Action, DELTAS, ROLLS, roll


def initial_state(board: Board) -> GameState:
    state = GameState(board.start, frozenset(
        bridge.id for bridge in board.bridges if bridge.initially_open))
    if not is_valid(board, state):
        raise ValueError("Starting block is not supported")
    return state


def is_valid(board: Board, state: GameState) -> bool:
    if not all(board.supported(cell, state.open_bridges) for cell in state.cells):
        return False
    # A single cube is allowed on fragile tiles: it weighs half the full block.
    return not (state.block is not None
                and state.block.orientation == Orientation.STANDING
                and state.cells[0] in board.fragile_tiles)


def is_goal(board: Board, state: GameState) -> bool:
    return (state.block is not None
            and state.block.orientation == Orientation.STANDING
            and state.cells[0] == board.goal)


def _pressed(switch: Switch, state: GameState) -> bool:
    if switch.kind == "soft":
        return switch.position in state.cells
    return (state.block is not None
            and state.block.orientation == Orientation.STANDING
            and switch.position == state.cells[0])


def _merge(board: Board, state: GameState) -> GameState:
    if state.block is not None or not board.merge_when_adjacent:
        return state
    (x1, y1), (x2, y2) = state.cubes
    if abs(x1 - x2) + abs(y1 - y2) != 1:
        return state
    orientation = Orientation.HORIZONTAL if y1 == y2 else Orientation.VERTICAL
    return GameState(Block(min(x1, x2), min(y1, y2), orientation),
                     state.open_bridges, state.locked_bridges)


def step(board: Board, state: GameState, action: Action | str) -> GameState | None:
    """Return the successor, or None for an illegal action/fall.

    SWITCH selects the other cube without moving it. It costs zero in search;
    each actual roll/cube translation costs one.
    """
    action = Action(action)
    if is_goal(board, state):
        return None
    if action == Action.SWITCH:
        return (replace(state, active_cube=1 - state.active_cube)
                if state.block is None else None)
    if state.block is not None:
        candidate = replace(state, block=roll(state.block, action))
    else:
        dx, dy = DELTAS[action]
        cubes = list(state.cubes)
        x, y = cubes[state.active_cube]
        destination = (x + dx, y + dy)
        if destination == cubes[1 - state.active_cube]:
            return None
        cubes[state.active_cube] = destination
        candidate = replace(state, cubes=tuple(cubes))
    if not is_valid(board, candidate):
        return None
    candidate = _merge(board, candidate)
    triggered = [switch for switch in board.switches
                 if _pressed(switch, candidate) and not _pressed(switch, state)]
    opened, locked = set(candidate.open_bridges), set(candidate.locked_bridges)
    for switch in triggered:
        if switch.kind == "split":
            continue
        for bridge_id in switch.bridge_ids:
            if bridge_id in locked:
                continue
            should_open = (bridge_id not in opened if switch.mode == "toggle"
                           else switch.open_state)
            if should_open:
                opened.add(bridge_id)
            else:
                opened.discard(bridge_id)
            if switch.lock_after_activation:
                locked.add(bridge_id)
    candidate = replace(candidate, open_bridges=frozenset(opened),
                        locked_bridges=frozenset(locked))
    for switch in triggered:
        if switch.kind == "split":
            candidate = GameState(None, candidate.open_bridges,
                                  candidate.locked_bridges, switch.destinations)
            candidate = _merge(board, candidate)
    return candidate if is_valid(board, candidate) else None


def successors(board: Board, state: GameState):
    for action in (*ROLLS, Action.SWITCH):
        next_state = step(board, state, action)
        if next_state is not None:
            yield action, next_state, 0 if action == Action.SWITCH else 1
