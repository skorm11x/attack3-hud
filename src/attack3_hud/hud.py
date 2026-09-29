import os
from typing import Optional

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")

import pygame

from .calibration import Calibration
from .state import Attack3Controller, ControllerState


class Attack3HUD:
    """Reusable Pygame HUD window for the Logitech Attack 3 controller."""

    def __init__(
        self,
        controller: Optional[Attack3Controller] = None,
        width: int = 800,
        height: int = 500,
        title: str = "Logitech Attack 3 — HID Driver HUD",
        config_path: Optional[str] = None,
        resizable: bool = True,
    ):
        self.config_path = config_path
        self.resizable = resizable
        self._editing_slot: Optional[int] = None
        self._edit_buffer = ""
        self._owns_controller = controller is None
        if controller is None:
            calibration = None
            if self.config_path is not None and os.path.exists(self.config_path):
                calibration = Calibration.from_file(self.config_path)
            controller = Attack3Controller(calibration=calibration, require_device=True)
        self.controller = controller
        self.width = width
        self.height = height
        self.title = title

        self._screen = None
        self._clock = None
        self._font_title = None
        self._font_label = None
        self._font_btn = None
        self._s = 0.0
        self._ox = 0
        self._oy = 0
        self._mode = "landscape"
        self._layout = {}

        self._color_bg = (22, 27, 34)
        self._color_panel = (33, 38, 45)
        self._color_text = (201, 209, 217)
        self._color_accent = (88, 166, 255)
        self._color_active = (46, 160, 67)
        self._color_inactive = (48, 54, 61)
        self._color_grid = (56, 139, 253)

    def _font_size(self, size: int) -> int:
        return max(8, int(size * self._s))

    def _load_font(self, size: int, bold: bool = False) -> pygame.font.Font:
        font = pygame.font.Font(None, self._font_size(size))
        font.set_bold(bold)
        return font

    @staticmethod
    def _create_icon() -> pygame.Surface:
        surf = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.circle(surf, (56, 139, 253), (32, 42), 20)
        pygame.draw.line(surf, (88, 166, 255), (32, 42), (32, 12), 4)
        pygame.draw.circle(surf, (201, 209, 217), (32, 12), 9)
        return surf

    def _update_scale(self) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        sw, sh = self._screen.get_size()
        if sh / sw > 1.2:
            mode = "portrait"
            design_w, design_h = 500, 800
        else:
            mode = "landscape"
            design_w, design_h = 800, 500
        s = min(sw / design_w, sh / design_h)
        self._ox = int((sw - design_w * s) // 2)
        self._oy = int((sh - design_h * s) // 2)
        if abs(s - self._s) > 0.01 or mode != self._mode:
            self._s = s
            self._mode = mode
            self._layout = self._compute_layout()
            self._font_title = self._load_font(22, bold=True)
            self._font_label = self._load_font(14)
            self._font_btn = self._load_font(12, bold=True)
        else:
            self._s = s

    def _compute_layout(self) -> dict:
        if self._mode == "portrait":
            return {
                "header": (30, 30),
                "stick_center": (190, 185),
                "stick_radius": 110,
                "axis_label": (140, 310),
                "throttle": (370, 130, 40, 220),
                "button_title": (140, 470),
                "button_start": (110, 500),
                "hint": (30, 770),
            }
        return {
            "header": (30, 20),
            "stick_center": (180, 230),
            "stick_radius": 110,
            "axis_label": (110, 360),
            "throttle": (360, 120, 40, 220),
            "button_title": (460, 95),
            "button_start": (460, 125),
            "hint": (460, 350),
        }

    def _init_display(self) -> None:
        if self._screen is not None:
            return
        pygame.display.set_icon(self._create_icon())
        flags = pygame.RESIZABLE if self.resizable else 0
        self._screen = pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption(self.title)
        self._clock = pygame.time.Clock()
        self._update_scale()

    def _x(self, v: float) -> int:
        return int(self._ox + v * self._s)

    def _y(self, v: float) -> int:
        return int(self._oy + v * self._s)

    def _r(self, v: float) -> int:
        return max(1, int(v * self._s))

    def _draw_stick_hud(
        self, state: ControllerState, center_x: int, center_y: int, radius: int
    ) -> None:
        cx = self._x(center_x)
        cy = self._y(center_y)
        r = self._r(radius)

        pygame.draw.circle(self._screen, self._color_panel, (cx, cy), r)
        pygame.draw.circle(self._screen, self._color_grid, (cx, cy), r, 2)
        pygame.draw.line(self._screen, self._color_grid, (cx - r, cy), (cx + r, cy), 1)
        pygame.draw.line(self._screen, self._color_grid, (cx, cy - r), (cx, cy + r), 1)

        pos_x = int(cx + (state.x * r))
        pos_y = int(cy + (state.y * r))

        pygame.draw.circle(self._screen, self._color_accent, (pos_x, pos_y), self._r(10))
        pygame.draw.circle(
            self._screen, (255, 255, 255), (pos_x, pos_y), self._r(4)
        )

    def _draw_throttle_bar(
        self, state: ControllerState, x: int, y: int, width: int, height: int
    ) -> None:
        norm_val = (1.0 - state.throttle) / 2.0
        x = self._x(x)
        y = self._y(y)
        w = self._r(width)
        h = self._r(height)
        fill_h = int(h * norm_val)

        pygame.draw.rect(self._screen, self._color_panel, (x, y, w, h))
        pygame.draw.rect(self._screen, self._color_grid, (x, y, w, h), 2)
        pygame.draw.rect(
            self._screen, self._color_accent, (x, y + h - fill_h, w, fill_h)
        )

        percent_txt = self._font_label.render(
            f"{int(norm_val * 100)}%", True, self._color_text
        )
        self._screen.blit(
            percent_txt, (x + (w // 2) - self._r(12), y + h + self._r(8))
        )

    def _draw_buttons(self, state: ControllerState, start_x: int, start_y: int) -> None:
        for slot, physical in enumerate(self.controller.calibration.buttons.layout):
            col = slot % 2
            row = slot // 2
            bx = self._x(start_x + (col * 140))
            by = self._y(start_y + (row * 35))
            bw = self._r(130)
            bh = self._r(28)

            editing = slot == self._editing_slot
            if editing:
                name = self._edit_buffer
                txt_color = (255, 255, 255)
                bg_color = self._color_panel
            else:
                is_pressed = (
                    state.buttons[physical] if physical < len(state.buttons) else False
                )
                bg_color = self._color_active if is_pressed else self._color_inactive
                txt_color = (255, 255, 255) if is_pressed else self._color_text
                name = self.controller.calibration.buttons.name_for_slot(slot)

            pygame.draw.rect(
                self._screen, bg_color, (bx, by, bw, bh), border_radius=self._r(5)
            )

            if editing:
                pygame.draw.rect(
                    self._screen,
                    (255, 255, 255),
                    (bx - 2, by - 2, bw + 4, bh + 4),
                    2,
                    border_radius=self._r(5),
                )

            lbl = self._font_btn.render(name, True, txt_color)
            self._screen.blit(lbl, (bx + self._r(10), by + self._r(7)))

    def _handle_click(self, pos: tuple[int, int]) -> None:
        mx, my = pos
        self._update_scale()
        dx = (mx - self._ox) / self._s
        dy = (my - self._oy) / self._s
        start_x, start_y = self._layout["button_start"]
        if dx < start_x or dy < start_y:
            if self._editing_slot is not None:
                self._cancel_edit()
            return

        col = int((dx - start_x) // 140)
        if col < 0 or col >= 2:
            if self._editing_slot is not None:
                self._cancel_edit()
            return

        local_x = (dx - start_x) % 140
        local_y = (dy - start_y) % 35
        row = int((dy - start_y) // 35)
        slot = row * 2 + col

        if (
            0 <= slot < len(self.controller.calibration.buttons.layout)
            and 0 <= local_x <= 130
            and 0 <= local_y <= 28
        ):
            self._start_edit(slot)
        else:
            if self._editing_slot is not None:
                self._cancel_edit()

    def _start_edit(self, slot: int) -> None:
        if self._editing_slot is not None:
            self._stop_edit()
        self._editing_slot = slot
        physical = self.controller.calibration.buttons.layout[slot]
        names = self.controller.calibration.buttons.names
        if physical < len(names):
            self._edit_buffer = names[physical]
        else:
            self._edit_buffer = f"Button {physical}"
        pygame.key.start_text_input()

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        if self._editing_slot is None:
            return
        if event.key == pygame.K_BACKSPACE:
            self._edit_buffer = self._edit_buffer[:-1]
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._confirm_edit()
        elif event.key == pygame.K_ESCAPE:
            self._cancel_edit()

    def _confirm_edit(self) -> None:
        if self._editing_slot is None:
            return
        physical = self.controller.calibration.buttons.layout[self._editing_slot]
        names = self.controller.calibration.buttons.names
        if physical < len(names):
            names[physical] = self._edit_buffer
        else:
            while len(names) <= physical:
                names.append(f"Button {len(names)}")
            names[physical] = self._edit_buffer
        self._stop_edit()
        if self.config_path:
            self.controller.calibration.to_file(self.config_path)

    def _cancel_edit(self) -> None:
        self._stop_edit()

    def _stop_edit(self) -> None:
        self._editing_slot = None
        self._edit_buffer = ""
        pygame.key.stop_text_input()

    def draw(self, surface: pygame.Surface, state: ControllerState) -> None:
        """Render the HUD into an existing surface (for embedding in a host app)."""
        self._screen = surface
        self.render(state)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle a host-provided event. Returns True if the HUD consumed it."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)
            return True
        if self._editing_slot is not None:
            if event.type == pygame.TEXTINPUT:
                self._edit_buffer += event.text
                return True
            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
                return True
        return False

    def close(self) -> None:
        """Stop editing and release the controller if we created it."""
        if self._editing_slot is not None:
            self._stop_edit()
        if self._owns_controller:
            self.controller.close()

    def render(self, state: ControllerState) -> None:
        """Render one frame at the current window scale and orientation."""
        self._update_scale()
        self._screen.fill(self._color_bg)

        layout = self._layout
        header = self._font_title.render(self.title, True, self._color_text)
        self._screen.blit(header, (self._x(layout["header"][0]), self._y(layout["header"][1])))

        self._draw_stick_hud(
            state,
            center_x=layout["stick_center"][0],
            center_y=layout["stick_center"][1],
            radius=layout["stick_radius"],
        )
        axis_lbl = self._font_label.render(
            f"X: {state.x:+.2f}  |  Y: {state.y:+.2f}", True, self._color_text
        )
        self._screen.blit(
            axis_lbl, (self._x(layout["axis_label"][0]), self._y(layout["axis_label"][1]))
        )

        tx, ty, tw, th = layout["throttle"]
        self._draw_throttle_bar(state, x=tx, y=ty, width=tw, height=th)
        throt_title = self._font_label.render("Throttle", True, self._color_text)
        self._screen.blit(
            throt_title, (self._x(tx - 10), self._y(ty - 25))
        )

        btn_title = self._font_label.render(
            "Button Matrix State (1–11)", True, self._color_text
        )
        self._screen.blit(
            btn_title, (self._x(layout["button_title"][0]), self._y(layout["button_title"][1]))
        )
        self._draw_buttons(
            state, start_x=layout["button_start"][0], start_y=layout["button_start"][1]
        )

        if self._editing_slot is not None:
            hint = "Editing: Enter to confirm, Esc to cancel"
        else:
            hint = "Click any button to rename it"
        help_lbl = self._font_label.render(hint, True, self._color_text)
        self._screen.blit(
            help_lbl, (self._x(layout["hint"][0]), self._y(layout["hint"][1]))
        )

    def run(self) -> None:
        """Run the HUD in its own window. For embedding, use draw() and handle_event()."""
        self._init_display()

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    flags = pygame.RESIZABLE if self.resizable else 0
                    self._screen = pygame.display.set_mode(event.size, flags)
                    self._update_scale()
                else:
                    self.handle_event(event)

            state = self.controller.read()
            self.render(state)
            pygame.display.flip()
            self._clock.tick(60)

        pygame.quit()
