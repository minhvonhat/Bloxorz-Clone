from dataclasses import replace
from core.block import Block, Orientation as O
from core.board import Board, Bridge, Switch
from core.game_state import GameState
from core.game_rules import initial_state, is_goal, is_valid, step, successors


def rectangle(**options):
    values = dict(width=8, height=7,
                  tiles=frozenset((x, y) for x in range(8) for y in range(7)),
                  start=Block(1, 3), goal=(7, 6))
    values.update(options)
    return Board(**values)


def test_void_boundary_and_fragile():
    board = rectangle(fragile_tiles=frozenset({(4, 3)}))
    state = initial_state(board)
    assert step(board, state, "left") is None
    lying = step(board, state, "right")
    assert lying.block == Block(2, 3, O.HORIZONTAL)
    assert step(board, lying, "right") is None  # stands on fragile (4, 3)
    assert is_valid(board, GameState(Block(3, 3, O.HORIZONTAL)))
    board = rectangle(tiles=rectangle().tiles - {(3, 3)})
    assert step(board, initial_state(board), "right") is None


def test_goal_requires_full_standing_block():
    board = rectangle(goal=(4, 3))
    lying = GameState(Block(3, 3, O.HORIZONTAL))
    assert not is_goal(board, lying)
    won = step(board, GameState(Block(2, 3, O.HORIZONTAL)), "right")
    assert is_goal(board, won)
    assert list(successors(board, won)) == []
    assert not is_goal(board, GameState(None, cubes=((4, 3), (0, 0))))


def test_soft_switch_enter_only_and_toggle_on_return():
    bridge = Bridge("b", frozenset({(7, 0)}))
    board = rectangle(tiles=rectangle().tiles - bridge.tiles, bridges=(bridge,),
                      switches=(Switch("soft", "soft", (2, 3), ("b",)),))
    start = initial_state(board)
    first = step(board, start, "right")
    assert first.open_bridges == frozenset({"b"})
    left = step(board, first, "left")
    assert left.open_bridges == frozenset({"b"})
    returned = step(board, left, "right")
    assert not returned.open_bridges


def test_split_cube_staying_on_soft_switch_does_not_retrigger():
    bridge = Bridge("b", frozenset({(7, 0)}))
    board = rectangle(tiles=rectangle().tiles - bridge.tiles, bridges=(bridge,),
                      switches=(Switch("s", "soft", (2, 3), ("b",)),))
    state = GameState(None, frozenset({"b"}), cubes=((2, 3), (5, 5)), active_cube=1)
    assert step(board, state, "right").open_bridges == frozenset({"b"})


def test_heavy_requires_standing_and_permanent_lock_is_in_state():
    bridge = Bridge("b", frozenset({(7, 0)}))
    board = rectangle(tiles=rectangle().tiles - bridge.tiles, bridges=(bridge,),
                      switches=(Switch("h", "heavy", (4, 3), ("b",),
                                       "permanent", True, True),
                                Switch("s", "soft", (2, 3), ("b",))))
    lying_over = step(board, GameState(Block(3, 3, O.VERTICAL)), "right")
    assert not lying_over.open_bridges
    locked = step(board, GameState(Block(2, 3, O.HORIZONTAL)), "right")
    assert locked.open_bridges == locked.locked_bridges == frozenset({"b"})
    returned = step(board, locked, "left")  # soft switch cannot close locked b
    assert returned.open_bridges == returned.locked_bridges == frozenset({"b"})
    assert len({locked, replace(locked, locked_bridges=frozenset()),
                replace(locked, open_bridges=frozenset())}) == 3
    cube = GameState(None, cubes=((3, 3), (0, 0)))
    assert not step(board, cube, "right").open_bridges


def test_bridge_support_and_closing_under_cube_falls():
    bridge = Bridge("b", frozenset({(3, 3)}))
    board = rectangle(tiles=rectangle().tiles - bridge.tiles, bridges=(bridge,),
                      switches=(Switch("s", "soft", (2, 3), ("b",)),))
    start = initial_state(board)
    assert step(board, start, "right") is None  # closed destination before effects
    assert step(board, replace(start, open_bridges=frozenset({"b"})), "right") is None
    cube = GameState(None, frozenset({"b"}), cubes=((3, 3), (2, 4)), active_cube=1)
    assert step(board, cube, "up") is None  # toggles support out from other cube
    assert step(replace(board, switches=()),
                replace(start, open_bridges=frozenset({"b"})), "right") is not None


def test_split_control_merge_and_single_cube_restrictions():
    board = rectangle(switches=(Switch("split", "split", (4, 3),
                                        destinations=((1, 5), (3, 5))),))
    split = step(board, GameState(Block(2, 3, O.HORIZONTAL)), "right")
    assert split.cubes == ((1, 5), (3, 5)) and split.block is None
    assert not is_goal(board, split)
    other = step(board, split, "switch")
    assert other.active_cube == 1 and other.cubes == split.cubes
    assert step(board, other, "switch") == split
    merged = step(board, split, "right")
    assert merged.block == Block(2, 5, O.HORIZONTAL)
    assert not merged.cubes and merged.active_cube == 0
    assert step(board, merged, "switch") is None
    # A cube touching a heavy or split switch cannot trigger either.
    cube = GameState(None, cubes=((3, 3), (0, 0)))
    assert step(board, cube, "right").block is None
    assert step(board, GameState(Block(3, 3, O.VERTICAL)), "right").block is not None


def test_adjacent_teleports_merge_and_unsupported_teleport_fails():
    board = rectangle(switches=(Switch("split", "split", (4, 3),
                                        destinations=((1, 5), (2, 5))),))
    before = GameState(Block(2, 3, O.HORIZONTAL))
    assert step(board, before, "right").block == Block(1, 5, O.HORIZONTAL)
    missing = replace(board, tiles=board.tiles - {(1, 5)})
    assert step(missing, before, "right") is None
    no_merge = replace(board, merge_when_adjacent=False)
    assert step(no_merge, before, "right").block is None


def test_single_cube_can_press_soft_and_walk_on_fragile():
    bridge = Bridge("b", frozenset({(7, 0)}))
    board = rectangle(tiles=rectangle().tiles - bridge.tiles, bridges=(bridge,),
                      fragile_tiles=frozenset({(2, 3)}),
                      switches=(Switch("s", "soft", (2, 3), ("b",)),))
    cube = GameState(None, cubes=((1, 3), (5, 5)))
    assert step(board, cube, "right").open_bridges == frozenset({"b"})
