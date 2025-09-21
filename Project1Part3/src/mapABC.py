from typing import List, Tuple
from grid import (
    Grid,
    TERRAIN_GRASS, TERRAIN_HILL, TERRAIN_SWAMP, TERRAIN_MOUNTAIN,
    RES_STONE, RES_IRON, RES_CRYSTAL,
)

def map_A() -> Grid:
    """
     Map A 
    """
    terrain: List[List[str]] = [
        [TERRAIN_GRASS, TERRAIN_HILL,  TERRAIN_GRASS, TERRAIN_GRASS, TERRAIN_SWAMP],
        [TERRAIN_HILL,  TERRAIN_GRASS, TERRAIN_SWAMP, TERRAIN_GRASS, TERRAIN_GRASS],
        [TERRAIN_GRASS, TERRAIN_GRASS, TERRAIN_HILL,  TERRAIN_GRASS, TERRAIN_SWAMP],
        [TERRAIN_SWAMP, TERRAIN_GRASS, TERRAIN_GRASS, TERRAIN_HILL,  TERRAIN_GRASS],
        [TERRAIN_GRASS, TERRAIN_SWAMP, TERRAIN_GRASS, TERRAIN_GRASS, TERRAIN_GRASS],
    ]
    # At least: 3×Stone, 2×Iron, 1×Crystal
    resources: List[Tuple[int,int,str]] = [
        (0, 2, RES_STONE), (2, 3, RES_STONE), (4, 1, RES_STONE),
        (3, 4, RES_IRON),  (1, 4, RES_IRON),
        (2, 0, RES_CRYSTAL),
    ]
    return Grid(terrain, resources)


def map_B() -> Grid:
    """
    Map B 
    """
    terrain: List[List[str]] = [
        [TERRAIN_HILL,  TERRAIN_GRASS, TERRAIN_SWAMP, TERRAIN_GRASS,  TERRAIN_HILL],
        [TERRAIN_SWAMP, TERRAIN_SWAMP, TERRAIN_HILL,  TERRAIN_GRASS,  TERRAIN_GRASS],
        [TERRAIN_GRASS, TERRAIN_HILL,  TERRAIN_SWAMP, TERRAIN_SWAMP,  TERRAIN_GRASS],
        [TERRAIN_GRASS, TERRAIN_GRASS, TERRAIN_HILL,  TERRAIN_GRASS,  TERRAIN_SWAMP],
        [TERRAIN_GRASS, TERRAIN_SWAMP, TERRAIN_GRASS, TERRAIN_HILL,   TERRAIN_GRASS],
    ]
    resources: List[Tuple[int,int,str]] = [
        (0, 4, RES_STONE), (3, 2, RES_STONE), (4, 0, RES_STONE),
        (2, 4, RES_IRON),  (4, 3, RES_IRON),
        (1, 3, RES_CRYSTAL),
    ]
    return Grid(terrain, resources)


def map_C() -> Grid:
    """
    New Map C
    """
    terrain: List[List[str]] = [
        [TERRAIN_GRASS,    TERRAIN_MOUNTAIN, TERRAIN_GRASS,   TERRAIN_MOUNTAIN, TERRAIN_HILL],
        [TERRAIN_GRASS,    TERRAIN_SWAMP,    TERRAIN_HILL,    TERRAIN_MOUNTAIN, TERRAIN_GRASS],
        [TERRAIN_MOUNTAIN, TERRAIN_GRASS,    TERRAIN_MOUNTAIN,TERRAIN_SWAMP,    TERRAIN_GRASS],
        [TERRAIN_GRASS,    TERRAIN_HILL,     TERRAIN_GRASS,   TERRAIN_HILL,     TERRAIN_MOUNTAIN],
        [TERRAIN_GRASS,    TERRAIN_GRASS,    TERRAIN_SWAMP,   TERRAIN_GRASS,    TERRAIN_GRASS],
    ]
    resources: List[Tuple[int,int,str]] = [
        (0, 3, RES_STONE), (3, 0, RES_STONE), (4, 3, RES_STONE),
        (1, 2, RES_IRON),  (4, 1, RES_IRON),
        (0, 4, RES_CRYSTAL),
    ]
    return Grid(terrain, resources)
