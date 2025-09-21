# state.py
from dataclasses import dataclass, replace
from typing import Tuple, FrozenSet
from grid import Grid, CAPACITY

Coord = Tuple[int, int]
A_BASE: Coord = (0, 0)
B_BASE: Coord = (4, 4)

@dataclass(frozen=True)
class PlayerBag:
    items: Tuple[str, ...]  # p.ej. ("STONE","IRON")

    def is_full(self) -> bool:
        return len(self.items) >= CAPACITY

    def add(self, kind: str) -> "PlayerBag":
        if self.is_full():
            return self
        return PlayerBag(self.items + (kind,))

    def empty(self) -> "PlayerBag":
        return PlayerBag(tuple())

    def count(self) -> int:
        return len(self.items)

@dataclass(frozen=True)
class Player:
    pos: Coord
    bag: PlayerBag
    delivered_total: int  # cuántos items entregados en la base

    def at_base(self, who: str) -> bool:
        return self.pos == (A_BASE if who == "A" else B_BASE)

    def deliver(self) -> "Player":
        if self.bag.count() == 0:
            return self
        return Player(pos=self.pos, bag=self.bag.empty(),
                      delivered_total=self.delivered_total + self.bag.count())

@dataclass(frozen=True)
class GameState:
    grid: Grid
    A: Player
    B: Player
    collected_mask: FrozenSet[int]  # índices de recursos ya recogidos del mapa
    delivered_total_global: int     # entregados A+B (para detener el juego)
    turn: str                       # "A" o "B"

    def is_terminal(self) -> bool:
        return self.delivered_total_global >= len(self.grid.resources)

    def utility(self) -> int:
        # Zero-sum: A - B
        return self.A.delivered_total - self.B.delivered_total

    def switch_turn(self) -> "GameState":
        return replace(self, turn=("B" if self.turn == "A" else "A"))

def initial_state(grid: Grid) -> GameState:
    return GameState(
        grid=grid,
        A=Player(pos=A_BASE, bag=PlayerBag(tuple()), delivered_total=0),
        B=Player(pos=B_BASE, bag=PlayerBag(tuple()), delivered_total=0),
        collected_mask=frozenset(),
        delivered_total_global=0,
        turn="A",
    )
