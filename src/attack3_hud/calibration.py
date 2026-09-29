import json
from dataclasses import asdict, dataclass, field
from typing import List


DEFAULT_BUTTON_NAMES = [
    "1 (Trigger)", "2 (Top L)", "3 (Top R)", "4 (Btm L)", "5 (Btm R)",
    "6 (Base 1)", "7 (Base 2)", "8 (Base 3)", "9 (Base 4)", "10 (Base 5)", "11 (Base 6)",
]

DEFAULT_BUTTON_LAYOUT = list(range(len(DEFAULT_BUTTON_NAMES)))


@dataclass
class AxisCalibration:
    """Per-axis calibration: deadzone, inversion, and scaling."""

    deadzone: float = 0.0
    invert: bool = False
    scale: float = 1.0

    def apply(self, value: float) -> float:
        if abs(value) < self.deadzone:
            return 0.0
        value = value * self.scale
        return -value if self.invert else value


@dataclass
class ButtonMap:
    """Named mapping and display layout for physical controller buttons."""

    names: List[str] = field(default_factory=lambda: DEFAULT_BUTTON_NAMES.copy())
    layout: List[int] = field(default_factory=lambda: DEFAULT_BUTTON_LAYOUT.copy())

    def __getitem__(self, index: int) -> str:
        if 0 <= index < len(self.names):
            return self.names[index]
        return f"Button {index}"

    def label(self, index: int) -> str:
        return self[index]

    def name_for_slot(self, slot: int) -> str:
        if 0 <= slot < len(self.layout):
            physical = self.layout[slot]
            if 0 <= physical < len(self.names):
                return self.names[physical]
            return f"Button {physical}"
        return f"Slot {slot}"


@dataclass
class Calibration:
    """Calibration bundle for the Attack 3 controller."""

    axes: List[AxisCalibration] = field(
        default_factory=lambda: [
            AxisCalibration(deadzone=0.05),
            AxisCalibration(deadzone=0.05),
            AxisCalibration(deadzone=0.05),
        ]
    )
    buttons: ButtonMap = field(default_factory=ButtonMap)

    def apply_axis(self, index: int, value: float) -> float:
        if 0 <= index < len(self.axes):
            return self.axes[index].apply(value)
        return value

    def button_name(self, index: int) -> str:
        return self.buttons[index]

    def to_file(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def from_file(cls, path: str) -> "Calibration":
        with open(path) as f:
            data = json.load(f)
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict) -> "Calibration":
        data["axes"] = [AxisCalibration(**a) for a in data["axes"]]
        data["buttons"] = ButtonMap(**data["buttons"])
        return cls(**data)
