"""Load the repository's (x, y) JSON format with actionable validation errors."""
import json
from pathlib import Path
from core.block import Block, Orientation
from core.board import Board, Bridge, Switch
from core.game_rules import initial_state


def board_from_dict(data: dict) -> Board:
    if not isinstance(data, dict):
        raise ValueError("Level must be a JSON object")

    def integer(value, name):
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        return value

    def boolean(value, name):
        if type(value) is not bool:
            raise ValueError(f"{name} must be a boolean")
        return value

    def required(obj, key):
        if not isinstance(obj, dict) or key not in obj:
            raise ValueError(f"Missing required field: {key}")
        return obj[key]

    width = integer(required(data, "width"), "width")
    height = integer(required(data, "height"), "height")
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")

    def cell(value):
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise ValueError("Each coordinate must be [x, y]")
        x, y = (integer(v, "coordinate") for v in value)
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError(f"Coordinate {(x, y)} lies outside the board")
        return x, y

    def cells(values):
        if not isinstance(values, list):
            raise ValueError("A tile collection must be a list")
        parsed = [cell(value) for value in values]
        if len(set(parsed)) != len(parsed):
            raise ValueError("Duplicate tile coordinates")
        return frozenset(parsed)

    def identifier(obj):
        value = required(obj, "id")
        if not isinstance(value, str) or not value:
            raise ValueError("IDs must be nonempty strings")
        return value

    tiles = cells(required(data, "tiles"))
    fragile = cells(data.get("fragile_tiles", []))
    if not fragile <= tiles:
        raise ValueError("fragile_tiles must belong to floor tiles")
    goal = cell(required(data, "goal"))
    if goal not in tiles or goal in fragile:
        raise ValueError("Goal must be a non-fragile floor tile")
    start_data = required(data, "start")
    start_cell = cell(required(start_data, "position"))
    try:
        orientation = Orientation(start_data.get("orientation", "standing"))
    except ValueError as exc:
        raise ValueError("Unknown starting orientation") from exc
    start = Block(*start_cell, orientation)

    bridges, bridge_ids, bridge_tiles = [], set(), set()
    bridge_data = data.get("bridges", [])
    if not isinstance(bridge_data, list):
        raise ValueError("bridges must be a list")
    for item in bridge_data:
        name = identifier(item)
        occupied = cells(required(item, "tiles"))
        status = item.get("initial_state", "closed")
        if status not in ("open", "closed"):
            raise ValueError("Bridge initial_state must be open or closed")
        if name in bridge_ids or not occupied or occupied & (tiles | bridge_tiles):
            raise ValueError("Duplicate bridge ID, empty bridge, or overlapping tiles")
        bridges.append(Bridge(name, occupied, status == "open"))
        bridge_ids.add(name)
        bridge_tiles.update(occupied)

    switches, switch_ids, positions = [], set(), set()
    switch_data = data.get("switches", [])
    if not isinstance(switch_data, list):
        raise ValueError("switches must be a list")
    for item in switch_data:
        name = identifier(item)
        kind = required(item, "type")
        position = cell(required(item, "position"))
        if kind not in ("soft", "heavy", "split"):
            raise ValueError("Unsupported switch type")
        if name in switch_ids or position in positions or position not in tiles:
            raise ValueError("Switch IDs/positions must be unique and on floor")
        effect = required(item, "effect")
        effect_type = required(effect, "type")
        if effect.get("trigger", "enter") != "enter":
            raise ValueError("Only enter-triggered switches are supported")
        if kind == "split":
            if effect_type != "split":
                raise ValueError("Split switch requires a split effect")
            raw_destinations = required(effect, "destinations")
            if not isinstance(raw_destinations, list):
                raise ValueError("Split destinations must be a list")
            destinations = tuple(cell(v) for v in raw_destinations)
            if len(destinations) != 2 or len(set(destinations)) != 2:
                raise ValueError("Split requires two distinct destinations")
            if any(p not in tiles | bridge_tiles for p in destinations):
                raise ValueError("Split destinations must belong to the board")
            switch = Switch(name, kind, position, destinations=destinations)
        else:
            if effect_type != "bridge":
                raise ValueError("Soft/heavy switches require a bridge effect")
            ids = required(effect, "bridge_ids")
            if (not isinstance(ids, list) or not ids or
                    any(not isinstance(v, str) for v in ids) or
                    len(ids) != len(set(ids)) or not set(ids) <= bridge_ids):
                raise ValueError("Switch references missing or duplicate bridges")
            mode = effect.get("mode", "toggle")
            if mode not in ("toggle", "permanent"):
                raise ValueError("Unsupported bridge effect mode")
            status = effect.get("state", "open")
            if status not in ("open", "closed"):
                raise ValueError("Bridge effect state must be open or closed")
            lock = boolean(effect.get("lock_after_activation", False),
                           "lock_after_activation")
            if lock and mode != "permanent":
                raise ValueError("Only permanent effects can lock bridges")
            switch = Switch(name, kind, position, tuple(ids), mode,
                            status == "open", lock)
        switches.append(switch)
        switch_ids.add(name)
        positions.add(position)

    rules = data.get("split_rules", {})
    if not isinstance(rules, dict):
        raise ValueError("split_rules must be an object")
    # Reject rule variants rather than silently solve a different game.
    expected = {"single_cube_can_win": False,
                "single_cube_activates": ["soft"],
                "single_cube_cannot_activate": ["heavy", "split"]}
    for key, value in expected.items():
        if key in rules and (rules[key] != value or type(rules[key]) is not type(value)):
            raise ValueError(f"Unsupported split rule: {key}")
    merge = boolean(rules.get("merge_when_adjacent", True), "merge_when_adjacent")
    board = Board(width, height, tiles, start, goal, fragile,
                  tuple(bridges), tuple(switches), merge)
    initial_state(board)
    return board


def load_level(path: str | Path) -> Board:
    with Path(path).open(encoding="utf-8") as source:
        return board_from_dict(json.load(source))
