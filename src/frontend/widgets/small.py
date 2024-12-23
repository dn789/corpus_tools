from pathlib import Path
from typing import Callable
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget

from backend.corpus.items import CorpusItem
from frontend.styles.colors import Colors, is_dark, random_color_rgb
from frontend.styles.icons import get_folder_closed_icon
from frontend.styles.sheets import add_tooltip
from frontend.utils.paths import Icons


class Button(QPushButton):
    def __init__(self, text: str, connect: Callable | None = None):
        super().__init__(text)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.clicked.connect(connect)
        # self.setStyleSheet(f"""""")


class LargeHeading(QLabel):
    def __init__(self, text, tooltip: str = ""):
        super().__init__(text)
        self.setStyleSheet(f"""
            color: {Colors.med_blue}; 
            font-weight: bold; 
            font-size: 24px;
        """)
        self.setToolTip(tooltip)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class MediumHeading(QLabel):
    def __init__(self, text, tooltip: str = ""):
        super().__init__(text)
        self.setStyleSheet(f"""
            color: {Colors.med_blue}; 
            font-weight: bold; 
            font-size: 20px;
            font-style: italic;
        """)
        self.setToolTip(tooltip)


class CorpusTag(QWidget):
    def __init__(
        self, obj: CorpusItem, tooltip: str = "", remove_func: Callable | None = None
    ) -> None:
        super().__init__()
        text_color = "white" if is_dark(*obj.color) else "black"  # type: ignore
        self.setStyleSheet(f"""
            QWidget {{
                padding: 5px;
                background-color: rgb{obj.color};
                font-weight: bold;
                color: {text_color};
                font-size: 16px;
            }}
        """)
        add_tooltip(self, tooltip)
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.label = QLabel(obj.name)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        layout.setSpacing(0)

        if remove_func:
            tag = SmallXButton(f'Remove "{obj.name}"')
            tag.pressed.connect(remove_func)
            layout.addWidget(tag)


class ImageButton(QPushButton):
    def __init__(self, image_path, icon_size=(20, 20), tooltip: str = ""):
        super().__init__()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # Load the image as a QPixmap
        pixmap = QPixmap(image_path)

        # Scale the pixmap to the desired icon size
        scaled_pixmap = pixmap.scaled(
            icon_size[0],
            icon_size[1],
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        # Set the scaled image as the button icon
        self.setIcon(scaled_pixmap)

        # Set the icon size to the scaled size
        self.setIconSize(scaled_pixmap.size())

        # Remove text and borders
        self.setText("")  # Ensure no text is displayed
        self.setStyleSheet("""
            QPushButton {
                border: none; 
                background: transparent; 
                padding: 0px; 
            }
            """)
        add_tooltip(self, tooltip)
        # Make button flat (no visual border effects)
        self.setFlat(True)


class SmallXButton(ImageButton):
    def __init__(self, tooltip: str = ""):
        super().__init__(Icons.x, tooltip=tooltip)


class FolderSelectWidget(QWidget):
    def __init__(
        self,
        path: Path | None = None,
        handle: Callable | None = None,
    ) -> None:
        super().__init__()
        self.setFixedHeight(50)
        self.path = path
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setLayout(layout)

        self.default_text = "Select folder"
        if path and path != Path("."):
            text = f"...{path.__str__()[-40:]}"
        else:
            text = self.default_text
        self.text_label = QLabel(text)
        self.text_label.setStyleSheet(f"""
               QLabel {{ 
                padding: 5px;
                font-weight: bold;
                border-radius: 5px;
                border: 1px solid black;
                background-color: {Colors.v_light_blue};
            }}
        """)
        add_tooltip(self.text_label, path.__str__())
        layout.addWidget(self.text_label)

        folder_select_button = FolderSelectButton()
        if handle:
            folder_select_button.clicked.connect(handle)
        layout.addWidget(folder_select_button)

    def set_path(self, path: str | Path):
        text = str(path)
        self.text_label.setText(text[-40:])
        add_tooltip(self.text_label, text, add_style=False)


class FolderSelectButton(QPushButton):
    def __init__(self, tooltip: str = "Select Folder"):
        super().__init__()
        icon = get_folder_closed_icon()
        self.setIcon(icon)
        self.setIconSize(icon.pixmap(25, 25).size())
        self.setStyleSheet("QPushButton {border: none;}")
        add_tooltip(self, tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
