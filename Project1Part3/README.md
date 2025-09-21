# A* Collector 

<img width="336" height="301" alt="image" src="https://github.com/user-attachments/assets/7a18ea95-a895-469a-bb45-326201b81eb2" />


Small A* search project with a 5×5 grid, resource pickups, terrain costs, and a Pygame UI.
Goal: deliver Stone ×3, Iron ×2, Crystal ×1 while minimizing total cost (sum of terrain entry costs).

Features

A* with pluggable heuristics:

- Main heuristic (admissible, guided)

- Zero / Dijkstra baseline (for validation)

Clean GUI: terrain colors, S/I/C resource labels, optimal path, metrics.

Prints the exact optimal path (cell coordinates) to the terminal when you solve.

## Requirements

- Python 3.10+

- Pygame (installed via pip)

## Installation

```python
# 1) Create & activate venv
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2) Install deps
pip install -r requirements.txt   
# or:
pip install pygame
```

## Usage

```python
python pygame_ui.py
```
The window shows the grid on the left and a panel on the right with status, controls, legend, and metrics.

## Controls
- M — Switch map 
- 1 — Use Main heuristic
- 0 — Use Zero (Dijkstra) heuristic
- R — Solve (run A* with the currently selected heuristic)
-  C — Clear result (hide path/metrics)
- ESC — Quit

### What you’ll see

Pink path over the grid (the optimal route).

### Metrics in the right panel:
- Total cost (sum of terrain entry costs: Grass=1, Hill=2, Swamp=3, Mountain=4)
- Path length (number of moves len(path) - 1)
- Expanded nodes
- Runtime 
- Delivered: S / I / C

### Path printed to terminal
When you press R and a solution is found, the program also prints to your terminal:
the ordered list of coordinates of the optimal path

**AI assistance:** We used ChatGPT to speed up coding:  all design/algorithms are our own.


