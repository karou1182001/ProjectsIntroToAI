# file: transitions.py
from typing import List, Tuple, Optional
from grid import Grid, CAPACITY, RES_STONE, RES_IRON, RES_CRYSTAL
from state import State, backpack_tuple, apply_deposit

# Movement deltas: (row_offset, col_offset)
_STEP_DELTAS: Tuple[Tuple[int, int], ...] = (
    (-1, 0),  # up
    ( 1, 0),  # down
    ( 0,-1),  # left
    ( 0, 1),  # right
)

def _adjacent4(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
    """True iff b is a 4-neighbor of a (Manhattan distance == 1)."""
    (ar, ac), (br, bc) = a, b
    return (abs(ar - br) + abs(ac - bc)) == 1

def _lookup_resource(world: Grid, cell: Tuple[int, int]):
    """
    Get the resource tile at `cell`, if any.
    Supports either Grid.resource_at(pos) or Grid.resource_on(pos).
    """
    # Prefer the canonical method name
    if hasattr(world, "resource_at"):
        return world.resource_at(cell)  # type: ignore[attr-defined]
    # Fallback if your Grid happens to use 'resource_on'
    if hasattr(world, "resource_on"):
        return world.resource_on(cell)  # type: ignore[attr-defined]
    return None

def _pack_delivered_tuple(delivered_dict_like) -> Tuple[int, int, int]:
    """Return delivered as a stable (stone, iron, crystal) tuple."""
    return (
        delivered_dict_like[RES_STONE],
        delivered_dict_like[RES_IRON],
        delivered_dict_like[RES_CRYSTAL],
    )

def apply_move(world: Grid, cur: State, nxt: Tuple[int, int]) -> Optional[Tuple[State, int]]:
    """
    Try to move from state `cur` into cell `nxt` (one step).
    Rules:
      - Step must be in-bounds and 4-adjacent.
      - Step cost = terrain cost of the DESTINATION cell.
      - If stepping on BASE with items -> auto-deposit.
      - If stepping on an available resource and backpack has room -> auto-pick.
    Returns (new_state, step_cost) or None if invalid move.
    """
    # quick validity
    if not world.in_bounds(nxt) or not _adjacent4(cur.pos, nxt):
        return None

    cost = world.terrain_cost(nxt)

    # mutable copies to assemble the next state
    bag = list(cur.backpack)
    # keep delivered as a dict-like via indices (avoid dict construction)
    d_stone, d_iron, d_crystal = cur.delivered
    mask = cur.consumed_mask

    # deposit first if we land on base and carry items
    if nxt == world.base and bag:
        bag_after, delivered_after = apply_deposit(tuple(bag), cur.delivered)
        bag = list(bag_after)
        d_stone, d_iron, d_crystal = delivered_after  # tuple already ordered

    # then try to pick if there's a resource, it's not taken, and we have room
    tile = _lookup_resource(world, nxt)
    if tile is not None:
        taken = (mask >> tile.idx) & 1
        if not taken and len(bag) < CAPACITY:
            bag.append(tile.kind)
            mask |= (1 << tile.idx)
        # if full, we simply can't pick it now; it remains available in other branches

    # build the next immutable state (sort bag so state keys are stable)
    next_state = State(
        pos=nxt,
        backpack=backpack_tuple(bag),
        delivered=(d_stone, d_iron, d_crystal),
        consumed_mask=mask,
    )
    return next_state, cost

def expand(world: Grid, cur: State) -> List[Tuple[State, int]]:
    """
    Generate all valid successors from `cur` (up to four).
    Uses a comprehension with in-line calls to vary the loop style.
    """
    r, c = cur.pos
    # Try all 4 candidate cells, apply the move, and keep only successful transitions
    candidates = ((r + dr, c + dc) for dr, dc in _STEP_DELTAS)
    results = [res for res in (apply_move(world, cur, cell) for cell in candidates) if res]
    return results
