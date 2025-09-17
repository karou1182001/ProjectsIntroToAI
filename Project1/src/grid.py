"""
This  defines:
- Terrain and resource constants (strings)
- Global mission requirements and agent capacity
- ResourceTile: immutable placement of a single resource on the grid
- Grid: a 5x5 board with terrain, a fixed base at (0,0), and resource lookups

The GUI uses:
- Grid.terrain to color each cell
- Grid.base to draw the base border
- Grid.resource_at() to overlay S/I/C letters

The solver uses:
- Grid.terrain_cost() to price steps
- Grid.resource_at() to auto-pick resources
- Grid.in_bounds() for move validity
- Grid.min_terrain_cost() for admissible heuristics
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

# -----------------------------
# Basic types
# -----------------------------
Coord = Tuple[int, int]  # (row, col) in a 5x5 grid

# -----------------------------
# Terrain (string constants)
# -----------------------------
TERRAIN_GRASS = "GRASS"
TERRAIN_HILL = "HILL"
TERRAIN_SWAMP = "SWAMP"
TERRAIN_MOUNTAIN = "MOUNTAIN"

# Cost to ENTER a cell of a given terrain (fixed convention throughout the project)
TERRAIN_COSTS: Dict[str, int] = {
    TERRAIN_GRASS: 1,
    TERRAIN_HILL: 2,
    TERRAIN_SWAMP: 3,
    TERRAIN_MOUNTAIN: 4, 
}

# -----------------------------
# Resources (string constants)
# -----------------------------
RES_STONE = "STONE"
RES_IRON = "IRON"
RES_CRYSTAL = "CRYSTAL"

# Mission requirements: deliver exactly 3 Stone, 2 Iron, 1 Crystal
REQ_COUNTS: Dict[str, int] = {
    RES_STONE: 3,
    RES_IRON: 2,
    RES_CRYSTAL: 1,
}

# Backpack capacity (max items the agent can carry at once)
CAPACITY = 2

# -----------------------------
# Resource placement on the map
# -----------------------------
@dataclass(frozen=True)
class ResourceTile:
    """
    Immutable description of one resource placed on the grid.

    Attributes
    ----------
    pos : (row, col)
        Cell where the resource lives.
    kind : str
        One of RES_STONE / RES_IRON / RES_CRYSTAL.
    idx : int
        Unique index (0..N-1). Used as a bit position in the search state's bitmask
        so we can't pick the same physical resource twice along a path.
    """
    pos: Coord
    kind: str
    idx: int

# -----------------------------
# Grid (5x5 world)
# -----------------------------
class Grid:
    """
    5x5 world model.

    Attributes
    ----------
    terrain : List[List[str]]
        5x5 matrix of terrain constants (TERRAIN_*).
    base : Coord
        Fixed base location at (0,0).
    resources : List[ResourceTile]
        All resource placements.
    resource_index_by_pos : Dict[Coord, int]
        Fast lookup from cell -> resource index in `resources`.
    """

    def __init__(self, terrain: List[List[str]], resources: List[Tuple[int, int, str]]):
        # Validate shape 5x5
        assert len(terrain) == 5 and all(len(row) == 5 for row in terrain), "Grid must be 5x5"

        # Validate terrain values
        valid_terrains = {TERRAIN_GRASS, TERRAIN_HILL, TERRAIN_SWAMP, TERRAIN_MOUNTAIN}
        for r in range(5):
            for c in range(5):
                if terrain[r][c] not in valid_terrains:
                    raise ValueError(f"Invalid terrain at {(r, c)}: {terrain[r][c]}")

        self.terrain: List[List[str]] = terrain
        self.base: Coord = (0, 0)

        # Load resources and build position index
        valid_resources = {RES_STONE, RES_IRON, RES_CRYSTAL}
        self.resources: List[ResourceTile] = []
        self.resource_index_by_pos: Dict[Coord, int] = {}

        for i, (rr, cc, kind) in enumerate(resources):
            if kind not in valid_resources:
                raise ValueError(f"Invalid resource at {(rr, cc)}: {kind}")
            tile = ResourceTile(pos=(rr, cc), kind=kind, idx=i)
            self.resources.append(tile)
            self.resource_index_by_pos[(rr, cc)] = i

    # -----------------------------
    # Grid utilities used by GUI & solver
    # -----------------------------
    def in_bounds(self, rc: Coord) -> bool:
        """Return True if (row, col) is inside the 5x5 board."""
        r, c = rc
        return 0 <= r < 5 and 0 <= c < 5

    def terrain_cost(self, rc: Coord) -> int:
        """Cost to ENTER cell `rc` based on its terrain type."""
        r, c = rc
        return TERRAIN_COSTS[self.terrain[r][c]]

    def resource_at(self, rc: Coord) -> Optional[ResourceTile]:
        """Return the ResourceTile at `rc` if any, else None."""
        idx = self.resource_index_by_pos.get(rc)
        if idx is None:
            return None
        return self.resources[idx]

    def min_terrain_cost(self) -> int:
        """
        Minimum terrain-enter cost on the board.
        Used by admissible heuristics as a safe (optimistic) per-step cost.
        """
        return min(TERRAIN_COSTS.values())
