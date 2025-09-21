from typing import List, Tuple, Optional
from dataclasses import replace
from grid import Grid, LootTile, CAPACITY
from status import GameState, Player, A_BASE, B_BASE

Coord = Tuple[int, int]

def manDist(a: Coord, b: Coord) -> int:
    (ar, ac), (br, bc) = a, b
    return abs(ar - br) + abs(ac - bc)


def close_neigh(grid: Grid, pos: Coord) -> List[Coord]:
    r, c = pos
    deltas = ((-1, 0), (1, 0), (0, -1), (0, 1))
    nbrs = [(r + dr, c + dc) for dr, dc in deltas]
    return [p for p in nbrs if grid.in_bounds(p)]


def valid_mov(state: GameState) -> List[Coord]:
    active: Player = state.B if state.turn == "B" else state.A
    return close_neigh(state.grid, active.pos)


def full_moveto_base(state: GameState) -> List[Coord]:
    who = state.turn
    me: Player = state.B if who == "B" else state.A
    home = (B_BASE if who == "B" else A_BASE)

    if me.bag.count() < CAPACITY:
        return valid_mov(state)

    options = valid_mov(state)
    here_d = manDist(me.pos, home)
    closer = [m for m in options if manDist(m, home) < here_d]

    if home in closer:        
        return [home]

    return closer or options


# ============  state transition ============
def exec_move(state: GameState, dest: Coord) -> GameState:
    """
    Execute one action for the current player:
       step to dest
       pick up if resource present and capacity left
       deliver all if standing on own base
      flip the turn
    Returns a NEW GameState
    """
    who = state.turn
    me: Player = state.B if who == "B" else state.A

    # --- Internal helpers --------------------------------------------
    def __hop(p: Player, where: Coord) -> Player:
        return replace(p, pos=where)

    def __spot_loot(s: GameState, where: Coord) -> Optional[LootTile]:
        t = s.grid.resource_on(where)
        return None if (t is None or t.idx in s.collected_mask) else t

    def __stash_if_room(p: Player, mask_set: set, tile: Optional[LootTile]) -> Player:
        if tile is None or p.bag.is_full():
            return p
        mask_set.add(tile.idx)
        return replace(p, bag=p.bag.add(tile.kind))

    def __drop_if_home(p: Player, side: str) -> Tuple[Player, int]:
        home = (B_BASE if side == "B" else A_BASE)
        if p.pos != home or p.bag.count() == 0:
            return p, 0
        delivered = p.bag.count()
        return p.deliver(), delivered

    # --- move ---------------------------------------------------------------
    moved = __hop(me, dest)

    # --- collect ------------------------------------------------------------
    new_mask = set(state.collected_mask)
    loot = __spot_loot(state, dest)
    moved = __stash_if_room(moved, new_mask, loot)

    # --- deliver ------------------------------------------------------------
    moved, delivered_now = __drop_if_home(moved, who)

    # ---  write back ---------------------------------------------------------
    if who == "A":
        A_new, B_new = moved, state.B
    else:
        A_new, B_new = state.A, moved

    updated = replace(
        state,
        A=A_new,
        B=B_new,
        collected_mask=frozenset(new_mask),
        delivered_total_global=state.delivered_total_global + delivered_now,
    )

    # --- toggle turn ---------------------------------------------------------
    return updated.switch_turn()
