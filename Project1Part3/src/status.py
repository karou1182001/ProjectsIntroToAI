from dataclasses import dataclass, replace
from typing import Tuple, FrozenSet
from grid import Grid, CAPACITY

# =========================
# Coordinates & bases
# =========================
Coord = Tuple[int, int]
A_BASE: Coord = (0, 0)
B_BASE: Coord = (4, 4)


# =========================
# Player inventory 
# =========================
@dataclass(frozen=True)
class PlayerBag:
    items: Tuple[str, ...] 

    def is_full(self) -> bool:
        """True if no more items can be added."""
        return len(self.items) >= CAPACITY

    def add(self, kind: str) -> "PlayerBag":
        """
        Add one item if there is room; otherwise return self unchanged.
        """
        if self.is_full():
            return self
        # Build a new tuple without mutating the original
        return PlayerBag(self.items + (kind,))

    def empty(self) -> "PlayerBag":
        """Return an empty version of this bag."""
        return PlayerBag(tuple())

    def count(self) -> int:
        """Number of items currently in the bag."""
        return len(self.items)


# =========================
#  Player snapshot
# =========================
@dataclass(frozen=True)
class Player:
    """Position, inventory and delivered cont."""
    pos: Coord
    bag: PlayerBag
    delivered_total: int  # total items delivered at own base

    def at_base(self, who: str) -> bool:
        """Whether this player stands on their base"""
        home = A_BASE if who == "A" else B_BASE
        return self.pos == home

    def deliver(self) -> "Player":
        cnt = self.bag.count()
        if cnt == 0:
            return self
        # Keep position, reset bag, bump delivered_total
        return replace(self, bag=self.bag.empty(), delivered_total=self.delivered_total + cnt)


# =========================
#  Whole game state node
# =========================
@dataclass(frozen=True)
class GameState:
    grid: Grid
    A: Player
    B: Player
    collected_mask: FrozenSet[int]   
    delivered_total_global: int      # A+B delivered 
    turn: str                        

    # ----- queries -----
    def is_terminal(self) -> bool:
        return self.delivered_total_global >= len(self.grid.resources)

    def utility(self) -> int:
        """
        Zero-sum payoff from A  perspective 
        positive if A delivered more than B, negative if less
        """
        return self.A.delivered_total - self.B.delivered_total


    def switch_turn(self) -> "GameState":
        nxt = "B" if self.turn == "A" else "A"
        return replace(self, turn=nxt)


# =========================
#  Factory
# =========================
def initial_state(grid: Grid) -> GameState:
    a0 = Player(pos=A_BASE, bag=PlayerBag(tuple()), delivered_total=0)
    b0 = Player(pos=B_BASE, bag=PlayerBag(tuple()), delivered_total=0)
    return GameState(
        grid=grid,
        A=a0,
        B=b0,
        collected_mask=frozenset(),
        delivered_total_global=0,
        turn="A",
    )
