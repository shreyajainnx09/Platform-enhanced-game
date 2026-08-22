# Python Platformer

A 2D platformer built with Pygame, using sprite sheets from Tech With Tim's
`Python-Platformer` asset pack. This package contains the working game code
(`tutorial.py`) plus every asset it needs, cloned directly from:
https://github.com/techwithtim/Python-Platformer

## Setup

```bash
pip install -r requirements.txt
python tutorial.py
```

Requires Python 3.8+ and Pygame. Keep `tutorial.py` and the `assets/` folder
in the same directory — the game loads sprites with relative paths like
`assets/MainCharacters/MaskDude`.

## Controls

| Action | Key |
|---|---|
| Move left / right | `Left Arrow` / `Right Arrow` |
| Jump (double jump supported) | `Space` |
| Quit | close the window |

## What's in the box

```
Python-Platformer/
├── tutorial.py          # the game
├── requirements.txt
├── README.md            # this file
├── README_original.md   # the repo's own README
└── assets/
    ├── MainCharacters/   # MaskDude, NinjaFrog, PinkMan, VirtualGuy sprite sheets
    ├── Terrain/          # tileset used for platform blocks
    ├── Traps/            # Fire, Saw, Spikes, Fan, Arrow, Trampoline, Rock Head, etc.
    ├── Items/             # Fruits, Boxes, Checkpoints
    ├── Background/       # tileable background colors
    ├── Menu/             # menu/UI sprites (not wired up in tutorial.py yet)
    └── Other/
```

## How it works

- **`load_sprite_sheets()`** slices a sprite-sheet PNG into individual frames
  based on a fixed tile width/height, and doubles their size with
  `pygame.transform.scale2x`. When `direction=True`, it also auto-generates
  mirrored left-facing frames from the right-facing ones.
- **`Player`** — loads the `MaskDude` sprite set, tracks velocity/gravity,
  supports a double jump, and picks the right animation (`idle`, `run`,
  `jump`, `double_jump`, `fall`, `hit`) based on current state.
- **`Block`** — a static terrain tile, cut from `Terrain/Terrain.png`.
- **`Fire`** — an animated hazard sprite (`Traps/Fire`) that can be turned
  `on()`/`off()`; touching it calls `player.make_hit()`.
- **Collision** uses `pygame.mask` (pixel-perfect) rather than plain rect
  collision, via `pygame.sprite.collide_mask`.
- **Camera** — the world doesn't move; instead `offset_x` scrolls what's
  drawn once the player nears the left/right edge of the scroll zone.

## Extending it

The `assets/Traps/` folder has a lot more hazards than the base tutorial
uses — Saw, Spikes, Spiked Ball, Rock Head, Fan, Arrow, Trampoline, Falling
Platforms — all already sliced-and-ready sprite sheets in the same format as
`Fire`. You can drop in a new hazard by copying the `Fire` class pattern:

```python
saw = Object(x, y, 32, 32, "saw")  # or subclass like Fire does
saw.animation = load_sprite_sheets("Traps", "Saw", 38, 38)
```

`assets/Items/Fruits` and `assets/Items/Checkpoints` are similarly unused in
the base tutorial and are ready to wire in for collectibles/respawn points.

Want me to build any of these out (more traps, a scrolling camera that also
moves vertically, a level file format, collectible fruit, checkpoints)? Just
ask and I'll add it directly to this code.
