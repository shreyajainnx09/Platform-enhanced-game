<div align="center">

# 🍄 Python Platformer
### A 2D side-scrolling platformer built with Python & Pygame

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
[![Pygame](https://img.shields.io/badge/Pygame-000000?style=for-the-badge&logo=python&logoColor=white)](https://img.shields.io/badge/Pygame-000000?style=for-the-badge&logo=python&logoColor=white)

</div>

---

## 📌 Description

A 2D platformer built with **Pygame**, based on Tech With Tim's `Python-Platformer` tutorial and sprite pack — extended here with additional levels and improvements.

- **Pixel-perfect collision** using `pygame.mask` instead of plain rectangle collision
- **Double jump** support with dedicated animation states
- Animated **hazards** (fire, and more available in the asset pack) that damage the player on contact
- A **scrolling camera** that follows the player once they near the edge of the screen
- Sprite-sheet–based animation system with automatic left/right mirroring

## 🎮 Controls

| Action | Key |
|---|---|
| Move Left | `←` (Left Arrow) |
| Move Right | `→` (Right Arrow) |
| Jump (double jump supported) | `Space` |
| Quit | Close the window |

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| 🐍 Python | Game logic |
| 🎮 Pygame | Rendering, input, collision, and the game loop |

## ⚙️ Setup

**Requirements**
- Python 3.8+
- Pygame (see `requirements.txt`)

```bash
git clone https://github.com/shreyajainnx09/Platform-enhanced-game.git
cd Platform-enhanced-game
python3 -m venv .venv
source .venv/bin/activate      # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> Keep `main.py` and the `assets/` folder in the same directory — the game loads sprites via relative paths like `assets/MainCharacters/MaskDude`.

## ▶️ Run

```bash
python3 main.py
```

## 🧠 How It Works

- `load_sprite_sheets()` slices each sprite-sheet PNG into individual frames based on a fixed tile size, scales them up with `pygame.transform.scale2x`, and auto-generates mirrored left-facing frames from the right-facing ones
- `Player` loads the MaskDude sprite set, tracks velocity and gravity, supports a double jump, and switches between `idle`, `run`, `jump`, `double_jump`, `fall`, and `hit` animations based on state
- `Block` is a static terrain tile cut from the terrain tileset
- `Fire` is an animated hazard that can be toggled `on()` / `off()`; touching it triggers `player.make_hit()`
- Collision detection uses `pygame.mask` for pixel-perfect accuracy via `pygame.sprite.collide_mask`, rather than simple rect overlap
- The camera doesn't move the world — instead, `offset_x` scrolls what's drawn once the player nears the edge of the visible scroll zone

## 📁 Project Structure

```
Platform-enhanced-game/
│
├── main.py             → Game entry point and core logic
├── requirements.txt    → Python dependencies
├── assets/
│   ├── MainCharacters/  → MaskDude, NinjaFrog, PinkMan, VirtualGuy sprite sheets
│   ├── Terrain/         → Tileset used for platform blocks
│   ├── Traps/           → Fire, Saw, Spikes, Fan, Arrow, Trampoline, Rock Head, etc.
│   ├── Items/            → Fruits, Boxes, Checkpoints
│   ├── Background/      → Tileable background colors
│   └── Menu/             → Menu/UI sprites
└── README.md
```

## 🌟 Ideas for Extending

- Wire in more hazards from `assets/Traps/` (Saw, Spikes, Trampoline, Rock Head, Fan, Arrow) using the same pattern as the `Fire` class
- Add collectible fruit from `assets/Items/Fruits` and a score counter
- Add checkpoints and respawn points using `assets/Items/Checkpoints`
- Extend the scrolling camera to also move vertically
- Add a level file format for easier level design
- Add sound effects and background music

## 👩🏻‍💻 Author

**Shreya Jain**
BCA | Data Analytics | Python | SQL | Tableau

### Credits

Built on top of the sprite assets and base tutorial from [Tech With Tim's Python-Platformer](https://github.com/techwithtim/Python-Platformer).
