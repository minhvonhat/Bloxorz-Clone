from copy import deepcopy
from pathlib import Path
import json
import pytest
from levels.level_loader import board_from_dict, load_level

LEVEL = Path(__file__).resolve().parents[1] / "levels/level_01.json"


def test_load_repository_level():
    board = load_level(LEVEL)
    assert board.goal == (6, 3) and board.start.cells == ((1, 3),)
    assert len(board.bridges) == 1 and len(board.switches) == 3
    assert board.has_teleports


@pytest.mark.parametrize("mutate", [
    lambda d: d.pop("goal"),
    lambda d: d.update(width=True),
    lambda d: d.update(width=0),
    lambda d: d.update(goal=[8, 3]),
    lambda d: d.update(goal=[3, 2]),
    lambda d: d["tiles"].append([1, 3]),
    lambda d: d["fragile_tiles"].append([0, 0]),
    lambda d: d["start"].update(orientation="diagonal"),
    lambda d: d["start"].update(position=[0, 0]),
    lambda d: d["bridges"][0].update(initial_state="maybe"),
    lambda d: d["bridges"][0].update(tiles=[[1, 3]]),
    lambda d: d["bridges"].append(deepcopy(d["bridges"][0])),
    lambda d: d["switches"][0]["effect"].update(bridge_ids=["missing"]),
    lambda d: d["switches"][0]["effect"].update(trigger="every_frame"),
    lambda d: d["switches"][0]["effect"].update(lock_after_activation="false"),
    lambda d: d["switches"][2]["effect"].update(destinations=[[1, 5], [1, 5]]),
    lambda d: d["switches"][2]["effect"].update(destinations=None),
    lambda d: d["split_rules"].update(single_cube_can_win=True),
    lambda d: d["split_rules"].update(single_cube_can_win=0),
])
def test_invalid_level_is_rejected(mutate):
    data = json.loads(LEVEL.read_text())
    mutate(data)
    with pytest.raises(ValueError):
        board_from_dict(data)
