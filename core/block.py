"""Immutable block placement. Coordinates use (x, y), matching level JSON."""
from dataclasses import dataclass
from enum import Enum

Cell = tuple[int, int]


class Orientation(str, Enum):
    STANDING = "standing"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


@dataclass(frozen=True)
class Block:
    """Anchor is the left/top occupied cell for a lying block."""

    x: int
    y: int
    orientation: Orientation = Orientation.STANDING

    def __post_init__(self):
        object.__setattr__(self, "orientation", Orientation(self.orientation))

    @property
    def cells(self) -> tuple[Cell, ...]:
        if self.orientation == Orientation.HORIZONTAL:
            return ((self.x, self.y), (self.x + 1, self.y))
        if self.orientation == Orientation.VERTICAL:
            return ((self.x, self.y), (self.x, self.y + 1))
        return ((self.x, self.y),)
