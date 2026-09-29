import os
from dataclasses import dataclass
from typing import List, Optional

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")

import pygame

from .calibration import Calibration


@dataclass
class ControllerState:
    """Snapshot of the Attack 3 controller at a single point in time."""

    x: float
    y: float
    throttle: float
    buttons: List[bool]
    name: str = ""
    axes_count: int = 0
    button_count: int = 0


class Attack3Controller:
    """Pollable interface for the Logitech Attack 3 joystick."""

    def __init__(
        self,
        index: int = 0,
        calibration: Optional[Calibration] = None,
        require_device: bool = True,
    ):
        self.index = index
        self.calibration = calibration or Calibration()

        if not pygame.get_init():
            pygame.init()
        if not pygame.joystick.get_init():
            pygame.joystick.init()

        if require_device and pygame.joystick.get_count() == 0:
            raise RuntimeError(
                "No USB Joystick detected! Please plug in the Logitech Attack 3."
            )

        self._joystick = None
        if pygame.joystick.get_count() > index:
            self._joystick = pygame.joystick.Joystick(index)
            self._joystick.init()

    @property
    def is_connected(self) -> bool:
        return self._joystick is not None

    def close(self) -> None:
        """Release the joystick handle. Safe to call multiple times."""
        if self._joystick is not None:
            self._joystick.quit()
            self._joystick = None

    def read(self) -> ControllerState:
        if self._joystick is None:
            if pygame.joystick.get_count() > self.index:
                self._joystick = pygame.joystick.Joystick(self.index)
                self._joystick.init()
            else:
                return ControllerState(
                    x=0.0,
                    y=0.0,
                    throttle=0.0,
                    buttons=[],
                    name="",
                    axes_count=0,
                    button_count=0,
                )

        joystick = self._joystick
        try:
            axes_count = joystick.get_numaxes()
            button_count = joystick.get_numbuttons()

            x = joystick.get_axis(0) if axes_count > 0 else 0.0
            y = joystick.get_axis(1) if axes_count > 1 else 0.0
            throttle = joystick.get_axis(2) if axes_count > 2 else 0.0

            x = self.calibration.apply_axis(0, x)
            y = self.calibration.apply_axis(1, y)
            throttle = self.calibration.apply_axis(2, throttle)

            buttons = [joystick.get_button(i) for i in range(button_count)]
        except pygame.error:
            self._joystick = None
            return ControllerState(
                x=0.0,
                y=0.0,
                throttle=0.0,
                buttons=[],
                name="",
                axes_count=0,
                button_count=0,
            )

        return ControllerState(
            x=x,
            y=y,
            throttle=throttle,
            buttons=buttons,
            name=joystick.get_name(),
            axes_count=axes_count,
            button_count=button_count,
        )
