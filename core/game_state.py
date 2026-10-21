"""All dynamic data affecting successors belongs in the hashable state."""
from dataclasses import dataclass
from core.block import Block, Cell


@dataclass(frozen=True)
class GameState:
    block: Block | None
    open_bridges: frozenset[str] = frozenset()
    locked_bridges: frozenset[str] = frozenset()
    cubes: tuple[Cell, ...] = ()
    active_cube: int = 0

    def __post_init__(self):
        if self.block is None:
            if len(self.cubes) != 2 or len(set(self.cubes)) != 2:
                raise ValueError("A split state needs two distinct cubes")
            if self.active_cube not in (0, 1):
                raise ValueError("active_cube must be 0 or 1")
        elif self.cubes or self.active_cube != 0:
            raise ValueError("A whole block cannot also contain split cubes")

    @property
    def cells(self) -> tuple[Cell, ...]:
        return self.block.cells if self.block is not None else self.cubes
