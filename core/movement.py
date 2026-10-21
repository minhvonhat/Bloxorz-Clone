"""Geometry only: board validity is checked separately by game_rules."""
from enum import Enum
from core.block import Block, Orientation


class Action(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    SWITCH = "switch"


ROLLS = (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT)
DELTAS = {
    Action.UP: (0, -1), Action.DOWN: (0, 1),
    Action.LEFT: (-1, 0), Action.RIGHT: (1, 0),
}


def roll(block: Block, action: Action | str) -> Block:
    action = Action(action)
    if action == Action.SWITCH:
        raise ValueError("switch changes the active cube, not block geometry")
    x, y, orientation = block.x, block.y, block.orientation
    S, H, V = Orientation.STANDING, Orientation.HORIZONTAL, Orientation.VERTICAL
    transitions = {
        S: {Action.UP: (0, -2, V), Action.DOWN: (0, 1, V),
            Action.LEFT: (-2, 0, H), Action.RIGHT: (1, 0, H)},
        H: {Action.UP: (0, -1, H), Action.DOWN: (0, 1, H),
            Action.LEFT: (-1, 0, S), Action.RIGHT: (2, 0, S)},
        V: {Action.UP: (0, -1, S), Action.DOWN: (0, 2, S),
            Action.LEFT: (-1, 0, V), Action.RIGHT: (1, 0, V)},
    }
    dx, dy, next_orientation = transitions[orientation][action]
    return Block(x + dx, y + dy, next_orientation)
