from dataclasses import dataclass
import random

from PySide6.QtCore import Qt, qDebug
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QPushButton

from frontend.styles.sheets import add_tooltip


@dataclass
class Colors:
    dark_blue: str = "#2c3e50"
    med_blue: str = "#406d99"
    light_blue: str = "#dff0f5"
    v_light_blue: str = "#edf5f7"
    light_gray: str = "#dcdfe0"
    gray: str = "gray"
    test_blue: str = "#3a7cbd"


def random_color_rgb(return_tuple: bool = True) -> tuple[int, int, int] | str:
    """Generates a random RGB color tuple or string."""
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    if return_tuple:
        return r, g, b
    return f"rgb{(r, g, b)}"


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a hex color string to RGB values."""
    hex_color = hex_color.lstrip("#")  # Remove '#' if present
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore


def get_luminance(r: float, g: float, b: float) -> float:
    """Calculate the luminance of a color."""
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def is_dark(r: float, g: float, b: float) -> bool:
    """Determine if the color is dark or light."""
    # r, g, b = hex_to_rgb(hex_color)  # Convert hex to RGB
    luminance = get_luminance(r, g, b)
    return luminance < 128


class ColorSelectButton(QPushButton):
    def __init__(self, color: tuple[int, int, int]):
        super().__init__()
        stylesheet = f"""
            QPushButton {{
                border-radius: 5px;
                background-color: rgb{color};
            }}"""
        self.setStyleSheet(stylesheet)
        add_tooltip(self, "Select color")

        self.setFixedHeight(30)
        self.setFixedWidth(30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def change_color(self, color: QColor) -> None:
        rgb_color = color.toTuple()[:-1]  # type: ignore
        # qDebug(str(color.toRgb().toTuple()))
        stylesheet = f"""
            QPushButton {{
                border-radius: 5px;
                background-color: rgb{rgb_color}; 
        }}"""
        self.setStyleSheet(stylesheet)
        add_tooltip(self, "Select color")
