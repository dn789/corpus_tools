from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import QApplication, QStyle
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter


@dataclass
class Icons:
    arrow_up: Path = Path("./frontend/icons/arrow_up.svg")
    arrow_down: Path = Path("./frontend/icons/arrow_down.svg")
    x: Path = Path("./frontend/icons/x.svg")
    folder_open: Callable = lambda: QApplication.style().standardIcon(  # type: ignore
        QStyle.StandardPixmap.SP_DirOpenIcon
    )
    folder_closed: Callable = lambda: QApplication.style().standardIcon(  # type: ignore
        QStyle.StandardPixmap.SP_DirClosedIcon
    )
    file: Callable = lambda: QApplication.style().standardIcon(  # type: ignore
        QStyle.StandardPixmap.SP_FileIcon
    )
    file_checked: Callable = lambda: get_filed_checked_icon()


def get_filed_checked_icon() -> QIcon:
    # Load the default system file icon
    file_icon = QIcon.fromTheme(
        "text-plain"
    )  # Default system file icon (can be adjusted)

    # Load the check mark SVG
    checkmark_icon = QIcon("../src/frontend/icons/check.svg")

    # Convert both icons to QPixmap objects
    file_pixmap = file_icon.pixmap(25, 25)  # Scale the file icon
    checkmark_pixmap = checkmark_icon.pixmap(15, 15)  # Scale the checkmark icon

    # Create a QPixmap to combine the icons
    combined_pixmap = QPixmap(file_pixmap.size())
    combined_pixmap.fill(Qt.transparent)  # type: ignore

    # Paint the file icon onto the combined pixmap
    painter = QPainter(combined_pixmap)
    painter.drawPixmap(0, 0, file_pixmap)

    # Paint the checkmark icon on top of the file icon
    painter.drawPixmap(
        combined_pixmap.width() - checkmark_pixmap.width(),
        combined_pixmap.height() - checkmark_pixmap.height(),
        checkmark_pixmap,
    )

    painter.end()

    # Create a QIcon from the combined pixmap
    combined_icon = QIcon(combined_pixmap)

    return combined_icon
