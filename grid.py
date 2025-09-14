# file: grid.py
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

# -----------------------------
# Tipos básicos
# -----------------------------
Coord = Tuple[int, int]  # (fila, columna) en la grilla 5x5

# -----------------------------
# Terrenos (constantes string)
# -----------------------------
TERRAIN_GRASS = "GRASS"       # pradera
TERRAIN_HILL = "HILL"         # colina
TERRAIN_SWAMP = "SWAMP"       # pantano
TERRAIN_MOUNTAIN = "MOUNTAIN" # montaña

# Costo de ENTRAR a la celda de ese terreno (convención fija)
TERRAIN_COSTS: Dict[str, int] = {
    TERRAIN_GRASS: 1,
    TERRAIN_HILL: 2,
    TERRAIN_SWAMP: 3,
    TERRAIN_MOUNTAIN: 4,  # si luego quieres, se puede tratar como impasable
}

# Símbolos ASCII para visualizar el terreno (opcional)
TERRAIN_SYMBOL: Dict[str, str] = {
    TERRAIN_GRASS: ".",
    TERRAIN_HILL:  "^",
    TERRAIN_SWAMP: "~",
    TERRAIN_MOUNTAIN: "#",
}

# -----------------------------
# Recursos (constantes string)
# -----------------------------
RES_STONE = "STONE"
RES_IRON = "IRON"
RES_CRYSTAL = "CRYSTAL"

# Requeridos de la misión (3 piedra, 2 hierro, 1 cristal)
REQ_COUNTS: Dict[str, int] = {
    RES_STONE: 3,
    RES_IRON: 2,
    RES_CRYSTAL: 1,
}

# Capacidad de la mochila
CAPACITY = 2

# -----------------------------
# Recurso físico en el mapa
# -----------------------------
@dataclass(frozen=True)
class ResourceTile:
    pos: Coord     # (r, c)
    kind: str      # RES_STONE / RES_IRON / RES_CRYSTAL
    idx: int       # índice único (0..N-1) para bitmask

# -----------------------------
# Clase Grid (5x5)
# -----------------------------
class Grid:
    """
    Representa un mundo 5x5.
    - Base fija en (0,0)
    - terrain[r][c] -> str (uno de TERRAIN_*)
    - resources: lista de ResourceTile
    - resource_index_by_pos: lookup rápido pos -> índice
    """
    def __init__(self, terrain: List[List[str]], resources: List[Tuple[int, int, str]]):
        # Validación 5x5
        assert len(terrain) == 5 and all(len(row) == 5 for row in terrain), "Grid must be 5x5"

        valid_terrains = {TERRAIN_GRASS, TERRAIN_HILL, TERRAIN_SWAMP, TERRAIN_MOUNTAIN}
        for r in range(5):
            for c in range(5):
                if terrain[r][c] not in valid_terrains:
                    raise ValueError(f"Terreno inválido en {(r, c)}: {terrain[r][c]}")

        self.terrain: List[List[str]] = terrain
        self.base: Coord = (0, 0)

        # Cargar recursos y construir índice por posición
        valid_resources = {RES_STONE, RES_IRON, RES_CRYSTAL}
        self.resources: List[ResourceTile] = []
        self.resource_index_by_pos: Dict[Coord, int] = {}

        for i, (rr, cc, kind) in enumerate(resources):
            if kind not in valid_resources:
                raise ValueError(f"Recurso inválido en {(rr, cc)}: {kind}")
            tile = ResourceTile(pos=(rr, cc), kind=kind, idx=i)
            self.resources.append(tile)
            self.resource_index_by_pos[(rr, cc)] = i

    # -----------------------------
    # Utilidades del grid
    # -----------------------------
    def in_bounds(self, rc: Coord) -> bool:
        r, c = rc
        return 0 <= r < 5 and 0 <= c < 5

    def neighbors(self, rc: Coord) -> List[Coord]:
        """Retorna los 4 vecinos (N/S/O/E) dentro de la grilla."""
        r, c = rc
        cand = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
        return [p for p in cand if self.in_bounds(p)]

    def terrain_cost(self, rc: Coord) -> int:
        """Costo de ENTRAR a la celda rc (depende del terreno de rc)."""
        r, c = rc
        return TERRAIN_COSTS[self.terrain[r][c]]

    def resource_at(self, rc: Coord) -> Optional[ResourceTile]:
        """Devuelve el recurso colocado en rc (si existe), o None si no hay."""
        idx = self.resource_index_by_pos.get(rc)
        if idx is None:
            return None
        return self.resources[idx]

    def min_terrain_cost(self) -> int:
        """Costo mínimo de cualquier terreno (útil para heurísticas admisibles)."""
        return min(TERRAIN_COSTS.values())

    def ascii_symbol_for_terrain(self, t: str) -> str:
        """Símbolo ASCII (solo para render simple opcional)."""
        return TERRAIN_SYMBOL[t]
