from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

# -----------------------------
# Basic types
# -----------------------------
Coord = Tuple[int, int]  # (row, col)

# -----------------------------
# Terrain constants (strings)
# -----------------------------
TERRAIN_GRASS = "GRASS"
TERRAIN_HILL = "HILL"
TERRAIN_SWAMP = "SWAMP"
TERRAIN_MOUNTAIN = "MOUNTAIN"

# Cost to ENTER a cell of that terrain
TERRAIN_COSTS: Dict[str, int] = {
    TERRAIN_GRASS: 1,
    TERRAIN_HILL: 2,
    TERRAIN_SWAMP: 3,
    TERRAIN_MOUNTAIN: 4,  
}

# -----------------------------
# Resource constants (strings)
# -----------------------------
RES_STONE = "STONE"
RES_IRON = "IRON"
RES_CRYSTAL = "CRYSTAL"

# Mission requirements (exact delivery counts)
REQ_COUNTS: Dict[str, int] = {
    RES_STONE: 3,
    RES_IRON: 2,
    RES_CRYSTAL: 1,
}

# Agent backpack capacity
CAPACITY = 2

# -----------------------------
# Resource placement record
# -----------------------------
@dataclass(frozen=True)
class LootTile:
    pos: Coord
    kind: str
    idx: int


# -----------------------------
# Grid (5x5 world)
# -----------------------------
class Grid:
    """
    Holds a 5x5 terrain matrix, the base at (0,0),
    and a list of resource placements with fast lookup.
    """

    # class level sets to validate inputs
    _VALID_TERRAINS = {TERRAIN_GRASS, TERRAIN_HILL, TERRAIN_SWAMP, TERRAIN_MOUNTAIN}
    _VALID_RESOURCES = {RES_STONE, RES_IRON, RES_CRYSTAL}

    def __init__(self, terrain: List[List[str]], resources: List[Tuple[int, int, str]]):
        # --- shape check (5x5) ---------------------------------------------------
        if len(terrain) != 5 or any(len(row) != 5 for row in terrain):
            raise AssertionError("Grid must be 5x5")

        # --- terrain validation  -------------------------------------
        if any(cell not in self._VALID_TERRAINS for row in terrain for cell in row):
            # find the first offending cell to report a helpful error
            for r in range(5):
                for c in range(5):
                    t = terrain[r][c]
                    if t not in self._VALID_TERRAINS:
                        raise ValueError(f"Invalid terrain at {(r, c)}: {t}")

        self.terrain: List[List[str]] = terrain
        self.base: Coord = (0, 0)

        # --- resource loading ----------------------------------------------------
        self.resources: List[LootTile] = []
        self._pos_to_idx: Dict[Coord, int] = {}

        # validate and build placements 
        for i, (rr, cc, kind) in enumerate(resources):
            if kind not in self._VALID_RESOURCES:
                raise ValueError(f"Invalid resource at {(rr, cc)}: {kind}")
            tile = LootTile(pos=(rr, cc), kind=kind, idx=i)
            self.resources.append(tile)
            self._pos_to_idx[(rr, cc)] = i

        
        self.resource_index_by_pos: Dict[Coord, int] = self._pos_to_idx

        self._min_cost = min(TERRAIN_COSTS.values())

    # -----------------------------
    # Methods for solver
    # -----------------------------
    def in_bounds(self, rc: Coord) -> bool:
        """
        True if (row, col) is inside the 5x5 board.
        Implemented with simple range checks for clarity and speed.
        """
        r, c = rc
        return 0 <= r < 5 and 0 <= c < 5

    def terrain_cost(self, rc: Coord) -> int:
        """
        Cost to ENTER cell , derived from the target cell's terrain.
        This is the convention used throughout the project.
        """
        r, c = rc
        return TERRAIN_COSTS[self.terrain[r][c]]

    def resource_on(self, rc: Coord) -> Optional[LootTile]:
        idx = self._pos_to_idx.get(rc)
        return self.resources[idx] if idx is not None else None

    def cheapest_step(self) -> int:
        return self._min_cost
