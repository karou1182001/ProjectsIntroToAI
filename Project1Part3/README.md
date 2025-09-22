# Agent A vs Agent B grid

A two player grid world where agents collect resources and race back to base. Our main agent uses Minimax with Alpha Beta pruning plus a backpack aware heuristic. 
Our game includes a Ui made with pygame.

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
cd src
python game.py
```
## Controls

- M – Switch map
- 1 / 0 – Toggle B’s agent: Random / Minimax
- P – Play / Pause auto-play
- N – Advance one turn (step mode)
- C – Reset current map
- ESC – Quit

## What you’ll see

- Colored terrain; bases at (0,0) for A and (4,4) for B
- S/I/C letters for Stone/Iron/Crystal
- Pink circles = players
- Metrics: delivered counts, backpack sizes, remaining resources, and Last Agent decide

