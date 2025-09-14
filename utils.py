# file: utils.py
from typing import List, Tuple, Optional, Dict
from grid import Grid, RES_STONE, RES_IRON, RES_CRYSTAL

def ascii_render(grid: Grid, path: Optional[List[Tuple[int,int]]] = None) -> str:
    """
    Dibuja el grid 5x5 en ASCII.
    - Terrenos: . ^ ~ #
    - Base: B
    - Recursos sin ruta: S / I / C
    - Ruta: * (sobrescribe el símbolo de la celda excepto la base)
    """
    path_set = set(path or [])
    # Mapa (r,c) -> tipo de recurso, para sobreponer letras S/I/C
    res_map: Dict[Tuple[int,int], str] = {tile.pos: tile.kind for tile in grid.resources}

    lines = []
    for r in range(5):
        row = []
        for c in range(5):
            cell = (r, c)

            if cell == grid.base:
                ch = "B"
            else:
                # símbolo base del terreno
                t = grid.terrain[r][c]
                ch = grid.ascii_symbol_for_terrain(t)
                # si hay recurso, lo sobreponemos
                if cell in res_map:
                    kind = res_map[cell]
                    ch = "S" if kind == RES_STONE else ("I" if kind == RES_IRON else "C")

            # si la celda está en la ruta, marcamos con '*'
            if cell in path_set and cell != grid.base:
                ch = "*"

            row.append(ch)
        lines.append(" ".join(row))
    return "\n".join(lines)

def delivered_str(delivered_tuple) -> str:
    """
    Convierte la tupla (stone, iron, crystal) a texto legible.
    """
    s, i, c = delivered_tuple
    return f"{{Stone:{s}, Iron:{i}, Crystal:{c}}}"
