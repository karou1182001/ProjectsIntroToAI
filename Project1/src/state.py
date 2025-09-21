"""
State representation for the Grid Resource A* project.

What lives here:
- Helpers to normalize deliveries and freeze backpacks into hashable tuples.
- The immutable `State` explored by A* (agent pos, backpack, delivered, consumed_mask).
- Minimal utilities used by transitions and A* (deposit at base, start state).

Notes
-----
- We expose compatibility aliases so external modules can keep importing:
    clamp_delivered, delivered_tuple, backpack_tuple, apply_deposit, make_start_state
- Implementation details were tweaked (names, loops) to be less boilerplate-y,
  while preserving identical semantics.
"""

from dataclasses import dataclass
from typing import Tuple, Dict, List

from grid import (
    Coord,
    RES_STONE, RES_IRON, RES_CRYSTAL,
    REQ_COUNTS, CAPACITY,
)

# ---------------------------------------------------------
# Internal helpers (renamed) + public aliases
# ---------------------------------------------------------

def _limit_deliveries(raw: Dict[str, int]) -> Dict[str, int]:
    """
    Clamp delivered counts to mission maxima (3/2/1).
    Prevents over-counting in the state space (keeps state canonical).
    """
    # Using dict.get to be robust if keys are missing in 'raw'
    lim = {}
    for k, cap in ((RES_STONE, REQ_COUNTS[RES_STONE]),
                   (RES_IRON,  REQ_COUNTS[RES_IRON]),
                   (RES_CRYSTAL, REQ_COUNTS[RES_CRYSTAL])):
        lim[k] = min(raw.get(k, 0), cap)
    return lim


def _deliveries_triplet(d: Dict[str, int]) -> Tuple[int, int, int]:
    """
    Convert a (possibly messy) deliveries dict into a clean, clamped triplet:
        (stone, iron, crystal)
    """
    clamped = _limit_deliveries(d)
    return (clamped[RES_STONE], clamped[RES_IRON], clamped[RES_CRYSTAL])


def _sorted_pack(items: List[str]) -> Tuple[str, ...]:
    """
    Return the backpack as a SORTED TUPLE (hashable, order-insensitive).
    Sorting ensures ('IRON','STONE') and ('STONE','IRON') are the same key.
    """
    # tuple(sorted(...)) is stable, deterministic, and hashable
    return tuple(sorted(items))


# Public aliases for external modules (compatibility)
clamp_delivered = _limit_deliveries
delivered_tuple = _deliveries_triplet
backpack_tuple = _sorted_pack


# ---------------------------------------------------------
# Search state explored by A*
# ---------------------------------------------------------

@dataclass(frozen=True)
class State:
    """
    Immutable search node.

    Attributes
    ----------
    pos : Coord
        Agent location (row, col).
    backpack : Tuple[str, ...]
        Sorted tuple of carried resources; len(backpack) <= CAPACITY.
    delivered : Tuple[int, int, int]
        Totals already delivered at base: (stone, iron, crystal).
    consumed_mask : int
        Bitmask of resource tiles already picked (by their unique idx).
    """
    pos: Coord
    backpack: Tuple[str, ...]
    delivered: Tuple[int, int, int]
    consumed_mask: int

    # ---------- High-level queries ----------
    def is_goal(self) -> bool:
        """True when exactly 3/2/1 have been delivered."""
        return self.delivered == (
            REQ_COUNTS[RES_STONE],
            REQ_COUNTS[RES_IRON],
            REQ_COUNTS[RES_CRYSTAL],
        )

    def total_backpack(self) -> int:
        """How many items are currently carried (<= CAPACITY)."""
        return len(self.backpack)

    def count_in_backpack(self, kind: str) -> int:
        """Count how many items of a specific type are carried."""
        # Using tuple.count for clarity (no generator needed)
        return self.backpack.count(kind)

    def delivered_as_dict(self) -> Dict[str, int]:
        """Deliveries as a dictionary (handy for intermediate arithmetic)."""
        s, i, c = self.delivered
        return {RES_STONE: s, RES_IRON: i, RES_CRYSTAL: c}

    def remaining_needed(self) -> Dict[str, int]:
        """
        How many still need to be DELIVERED (ignores what’s in the backpack).
        Always clamped to >= 0.
        """
        cur = self.delivered_as_dict()
        need = {}
        for k in (RES_STONE, RES_IRON, RES_CRYSTAL):
            need[k] = max(0, REQ_COUNTS[k] - cur.get(k, 0))
        return need

    def need_to_collect_counts(self) -> Dict[str, int]:
        """
        How many still need to be COLLECTED (considering the backpack).
        This subtracts what's already carried and clamps to >= 0.
        """
        need = self.remaining_needed()
        out = {}
        # subtract carried amounts per kind
        for k in (RES_STONE, RES_IRON, RES_CRYSTAL):
            out[k] = max(0, need[k] - self.count_in_backpack(k))
        return out


# ---------------------------------------------------------
# Utilities used by transitions/A*
# ---------------------------------------------------------

def _settle_at_base(
    backpack: Tuple[str, ...],
    delivered: Tuple[int, int, int],
) -> Tuple[Tuple[str, ...], Tuple[int, int, int]]:
    """
    Simulate auto-deposit at the BASE:
      - move backpack contents into 'delivered'
      - clamp to mission maxima
      - return an EMPTY backpack and the updated deliveries triplet
    """
    current = {RES_STONE: delivered[0], RES_IRON: delivered[1], RES_CRYSTAL: delivered[2]}

    # Fold-in backpack contents
    if backpack:
        # Iterate explicitly (equivalent to a sum over kinds)
        for item in backpack:
            current[item] = current.get(item, 0) + 1

    clamped = _limit_deliveries(current)
    # Empty backpack is represented by empty tuple
    return (), (clamped[RES_STONE], clamped[RES_IRON], clamped[RES_CRYSTAL])


def _bootstrap_state() -> State:
    """
    Initial state:
      - position at base (0,0)
      - empty backpack
      - nothing delivered
      - no resources consumed (bitmask = 0)
    """
    return State(pos=(0, 0), backpack=(), delivered=(0, 0, 0), consumed_mask=0)


# Public aliases (compatibility with existing imports)
apply_deposit = _settle_at_base
make_start_state = _bootstrap_state
