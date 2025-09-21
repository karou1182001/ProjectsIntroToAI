# state.py
from dataclasses import dataclass, replace
from typing import Tuple, List, Dict, FrozenSet, Optional
from grid import Grid, CAPACITY, LootTile

Coord = Tuple[int, int]

A_BASE: Coord = (0, 0)
B_BASE: Coord = (4, 4)

@dataclass(frozen=True)
class PlayerBag:
    items: Tuple[str, ...]  # tipos de recursos en mochila ("STONE", "IRON", "CRYSTAL")

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
    delivered_total: int
    delivered_by_kind: Tuple[int, int, int]  # (stone, iron, crystal) – opcional/para métricas

    def at_base(self, who: str) -> bool:
        return self.pos == (A_BASE if who == "A" else B_BASE)

    def deliver(self) -> "Player":
        # vacía mochila y suma al entregado_total
        if self.bag.count() == 0:
            return self
        stone = self.delivered_by_kind[0]
        iron = self.delivered_by_kind[1]
        cryst = self.delivered_by_kind[2]
        # Cuenta lo que trae
        add_stone = sum(1 for k in self.bag.items if k == "STONE")
        add_iron  = sum(1 for k in self.bag.items if k == "IRON")
        add_cry   = sum(1 for k in self.bag.items if k == "CRYSTAL")
        return Player(
            pos=self.pos,
            bag=self.bag.empty(),
            delivered_total=self.delivered_total + self.bag.count(),
            delivered_by_kind=(stone + add_stone, iron + add_iron, cryst + add_cry),
        )

@dataclass(frozen=True)
class GameState:
    grid: Grid
    A: Player
    B: Player
    # índices de recursos que ya NO están en el mapa (porque alguien los recogió)
    collected_mask: FrozenSet[int]
    # cuántos recursos han sido entregados (A + B)
    delivered_total_global: int
    turn: str  # "A" o "B"

    def is_terminal(self) -> bool:
        # Terminal cuando TODOS los recursos fueron ENTREGADOS (no solo recogidos)
        return self.delivered_total_global >= len(self.grid.resources)

    def utility(self) -> int:
        # Zero-sum: deliveredA - deliveredB
        return self.A.delivered_total - self.B.delivered_total

    def whose(self):
        return self.A if self.turn == "A" else self.B

    def other(self):
        return self.B if self.turn == "A" else self.A

    def switch_turn(self) -> "GameState":
        return replace(self, turn=("B" if self.turn == "A" else "A"))

def initial_state(grid: Grid) -> GameState:
    return GameState(
        grid=grid,
        A=Player(pos=(0, 0), bag=PlayerBag(tuple()), delivered_total=0, delivered_by_kind=(0,0,0)),
        B=Player(pos=(4, 4), bag=PlayerBag(tuple()), delivered_total=0, delivered_by_kind=(0,0,0)),
        collected_mask=frozenset(),
        delivered_total_global=0,
        turn="A",
    )
