# file: maps.py
from typing import List, Tuple
from grid import (
    Grid,
    TERRAIN_GRASS, TERRAIN_HILL, TERRAIN_SWAMP, TERRAIN_MOUNTAIN,
    RES_STONE, RES_IRON, RES_CRYSTAL,
)

def build_map_A() -> Grid:
    """
    Mapa A — Básico:
      - Mayoría pradera, algunos pantanos/colinas.
      - Recursos inspirados en el ejemplo del enunciado.
    """
    terrain: List[List[str]] = [
        [TERRAIN_GRASS, TERRAIN_GRASS, TERRAIN_GRASS, TERRAIN_HILL,   TERRAIN_GRASS],
        [TERRAIN_GRASS, TERRAIN_SWAMP, TERRAIN_GRASS, TERRAIN_GRASS,  TERRAIN_GRASS],
        [TERRAIN_GRASS, TERRAIN_GRASS, TERRAIN_GRASS, TERRAIN_HILL,   TERRAIN_GRASS],
        [TERRAIN_GRASS, TERRAIN_SWAMP, TERRAIN_GRASS, TERRAIN_HILL,   TERRAIN_GRASS],
        [TERRAIN_GRASS, TERRAIN_GRASS, TERRAIN_GRASS, TERRAIN_GRASS,  TERRAIN_GRASS],
    ]
    # Al menos: 3×Stone, 2×Iron, 1×Crystal
    resources: List[Tuple[int,int,str]] = [
        (1, 3, RES_STONE), (3, 0, RES_STONE), (4, 2, RES_STONE),
        (2, 1, RES_IRON),  (4, 4, RES_IRON),
        (0, 4, RES_CRYSTAL),
    ]
    return Grid(terrain, resources)


def build_map_B() -> Grid:
    """
    Mapa B — Intermedio:
      - Más pantanos y colinas forzando rodeos.
      - Un Crystal algo apartado.
    """
    terrain: List[List[str]] = [
        [TERRAIN_GRASS,  TERRAIN_HILL,   TERRAIN_HILL,   TERRAIN_GRASS, TERRAIN_GRASS],
        [TERRAIN_SWAMP,  TERRAIN_SWAMP,  TERRAIN_HILL,   TERRAIN_GRASS, TERRAIN_GRASS],
        [TERRAIN_GRASS,  TERRAIN_GRASS,  TERRAIN_SWAMP,  TERRAIN_SWAMP, TERRAIN_GRASS],
        [TERRAIN_GRASS,  TERRAIN_HILL,   TERRAIN_GRASS,  TERRAIN_HILL,  TERRAIN_GRASS],
        [TERRAIN_GRASS,  TERRAIN_GRASS,  TERRAIN_GRASS,  TERRAIN_SWAMP, TERRAIN_GRASS],
    ]
    resources: List[Tuple[int,int,str]] = [
        (0, 3, RES_STONE), (3, 0, RES_STONE), (4, 2, RES_STONE),
        (2, 4, RES_IRON),  (4, 4, RES_IRON),
        (1, 4, RES_CRYSTAL),
    ]
    return Grid(terrain, resources)


def build_map_C() -> Grid:
    """
    Mapa C — Retador:
      - Montañas (coste 4, pero PASABLES) y pantanos dispersos.
      - Distancias más largas y rodeos más costosos.
    """
    terrain: List[List[str]] = [
        [TERRAIN_GRASS,    TERRAIN_MOUNTAIN, TERRAIN_HILL,     TERRAIN_MOUNTAIN, TERRAIN_GRASS],
        [TERRAIN_GRASS,    TERRAIN_MOUNTAIN, TERRAIN_SWAMP,    TERRAIN_HILL,     TERRAIN_GRASS],
        [TERRAIN_GRASS,    TERRAIN_GRASS,    TERRAIN_MOUNTAIN, TERRAIN_SWAMP,    TERRAIN_GRASS],
        [TERRAIN_MOUNTAIN, TERRAIN_HILL,     TERRAIN_GRASS,    TERRAIN_HILL,     TERRAIN_MOUNTAIN],
        [TERRAIN_GRASS,    TERRAIN_GRASS,    TERRAIN_GRASS,    TERRAIN_GRASS,    TERRAIN_GRASS],
    ]
    resources: List[Tuple[int,int,str]] = [
        (1, 3, RES_STONE), (3, 2, RES_STONE), (4, 0, RES_STONE),
        (2, 4, RES_IRON),  (4, 4, RES_IRON),
        (0, 4, RES_CRYSTAL),
    ]
    return Grid(terrain, resources)
