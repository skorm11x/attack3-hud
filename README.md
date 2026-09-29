# attack3-hud

Cross platform HID controller diagnostics HUD for the Logitech Attack 3 joystick.

## Installation

```bash
pip install attack3-hud
```

Or install from source with `uv`:

```bash
git clone https://github.com/skorm11x/attack3-hud
cd attack3-hud
uv sync
```

## Running with uv

This project uses [uv](https://docs.astral.sh/uv/). The main commands are:

```bash
# Run the GUI from the installed package entry point
uv run attack3-hud

# Or run the source file directly
uv run python src/attack3_hud/main.py
```

`uv run` will sync the lockfile and create/use the project virtual environment automatically.

Make sure the Logitech Attack 3 joystick is plugged in before launching; the program exits immediately if no joystick is detected.

## Other useful commands

```bash
uv sync                # install dependencies and the package
uv build               # build distributable wheels/sdists
uv pip install -e .    # editable install (if you prefer)
```

The `attack3-hud` command is defined by the `[project.gui-scripts]` entry point in `pyproject.toml`.

## Library usage

You can also import the package as a library:

```python
from attack3_hud import Attack3Controller, Attack3HUD, Calibration

# Poll controller state in your own loop
controller = Attack3Controller()
while True:
    state = controller.read()
    print(state.x, state.y, state.throttle, state.buttons)

# Or open the diagnostics window
hud = Attack3HUD(controller=controller)
hud.run()
```

Calibration and button-name remapping live in the `Calibration` object:

```python
cal = Calibration()
cal.axes[0].invert = True
cal.axes[1].deadzone = 0.1
controller = Attack3Controller(calibration=cal)
```

`Attack3HUD.run()` takes over the Pygame event loop. If your own app already owns the
window and loop, embed the HUD instead:

```python
hud = Attack3HUD(controller=controller)  # pass your own controller to avoid stealing it

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        else:
            hud.handle_event(event)  # returns True if the HUD consumed it

    state = controller.read()
    hud.draw(screen.subsurface(pygame.Rect(400, 0, 800, 500)), state)
    pygame.display.flip()
```

- `draw(surface, state)` renders into any `pygame.Surface` — useful for a side panel or
  a subsurface of your own window.
- `handle_event(event)` forwards mouse/keyboard input (button renaming still works).
- `controller.read()` polls raw + calibrated state and reconnects if the device
  re-appears; `controller.close()` / `hud.close()` release the device cleanly.
- `Attack3HUD.run()` is standalone-only: it owns the loop and calls `pygame.quit()`.
