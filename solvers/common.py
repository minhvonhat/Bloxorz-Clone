"""Shared contracts for solvers; importing this module does not import Pygame."""
from dataclasses import dataclass
from typing import Generic, Hashable, Iterable, Protocol, TypeVar
from core.board import Board
from core.game_rules import initial_state, is_goal, successors
from core.game_state import GameState
from core.movement import Action

StateT = TypeVar("StateT", bound=Hashable)
ActionT = TypeVar("ActionT")


class SearchProblem(Protocol[StateT, ActionT]):
    initial_state: StateT

    def is_goal(self, state: StateT) -> bool: ...

    def successors(self, state: StateT) -> Iterable[tuple[ActionT, StateT, float]]: ...


@dataclass(frozen=True)
class SearchResult(Generic[StateT, ActionT]):
    status: str  # solved | unsolvable | limit_reached | timeout
    actions: tuple[ActionT, ...]
    states: tuple[StateT, ...]
    cost: float | None
    expanded_nodes: int
    generated_nodes: int
    search_time_seconds: float
    peak_memory_bytes: int | None

    @property
    def solved(self) -> bool:
        return self.status == "solved"

    @property
    def solution_length(self) -> int:
        """Number of rolls/cube moves; free control selection is excluded."""
        return sum(action != Action.SWITCH for action in self.actions)


class BloxorzProblem:
    def __init__(self, board: Board, start: GameState | None = None):
        from core.game_rules import is_valid
        self.board = board
        self.initial_state = start if start is not None else initial_state(board)
        if not is_valid(board, self.initial_state):
            raise ValueError("Search start must be a valid supported state")

    def is_goal(self, state: GameState) -> bool:
        return is_goal(self.board, state)

    def successors(self, state: GameState):
        return successors(self.board, state)
