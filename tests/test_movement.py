import pytest
from core.block import Block, Orientation as O
from core.movement import Action, roll


@pytest.mark.parametrize("orientation,action,expected", [
    (O.STANDING, "up", (5, 3, O.VERTICAL)),
    (O.STANDING, "down", (5, 6, O.VERTICAL)),
    (O.STANDING, "left", (3, 5, O.HORIZONTAL)),
    (O.STANDING, "right", (6, 5, O.HORIZONTAL)),
    (O.HORIZONTAL, "up", (5, 4, O.HORIZONTAL)),
    (O.HORIZONTAL, "down", (5, 6, O.HORIZONTAL)),
    (O.HORIZONTAL, "left", (4, 5, O.STANDING)),
    (O.HORIZONTAL, "right", (7, 5, O.STANDING)),
    (O.VERTICAL, "up", (5, 4, O.STANDING)),
    (O.VERTICAL, "down", (5, 7, O.STANDING)),
    (O.VERTICAL, "left", (4, 5, O.VERTICAL)),
    (O.VERTICAL, "right", (6, 5, O.VERTICAL)),
])
def test_all_orientation_transitions(orientation, action, expected):
    block = Block(5, 5, orientation)
    assert roll(block, action) == Block(*expected)
    inverse = {"up": "down", "down": "up", "left": "right", "right": "left"}
    assert roll(roll(block, action), inverse[action]) == block


def test_occupied_cells_and_invalid_direction():
    assert Block(2, 3).cells == ((2, 3),)
    assert Block(2, 3, "horizontal").cells == ((2, 3), (3, 3))
    assert Block(2, 3, "vertical").cells == ((2, 3), (2, 4))
    with pytest.raises(ValueError):
        roll(Block(2, 3), Action.SWITCH)
