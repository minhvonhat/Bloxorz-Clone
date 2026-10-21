"""Static level data, independent from the renderer and search algorithm."""
from dataclasses import dataclass
from core.block import Block, Cell


@dataclass(frozen=True)
class Bridge:
    id: str
    tiles: frozenset[Cell]
    initially_open: bool = False


@dataclass(frozen=True)
class Switch:
    id: str
    kind: str
    position: Cell
    bridge_ids: tuple[str, ...] = ()
    mode: str = "toggle"
    open_state: bool = True
    lock_after_activation: bool = False
    destinations: tuple[Cell, ...] = ()


@dataclass(frozen=True)
class Board:
    width: int
    height: int
    tiles: frozenset[Cell]
    start: Block
    goal: Cell
    fragile_tiles: frozenset[Cell] = frozenset()
    bridges: tuple[Bridge, ...] = ()
    switches: tuple[Switch, ...] = ()
    merge_when_adjacent: bool = True

    def supported(self, cell: Cell, open_bridges: frozenset[str]) -> bool:
        x, y = cell
        return (0 <= x < self.width and 0 <= y < self.height and
                (cell in self.tiles or any(
                    bridge.id in open_bridges and cell in bridge.tiles
                    for bridge in self.bridges)))

    @property
    def has_teleports(self) -> bool:
        return any(switch.kind == "split" for switch in self.switches)
