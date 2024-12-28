from pathlib import Path
from typing import Callable
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics, QPainter, QPixmap, QTextLayout
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QWidget,
)

from backend.corpus.items import CorpusItem
from frontend.styles.colors import Colors, is_dark
from frontend.styles.icons import Icons
from frontend.styles.sheets import add_tooltip


class Button(QPushButton):
    def __init__(
        self,
        text: str,
        connect: Callable | None = None,
        tooltip: str | None = None,
        font_size: int = 18,
    ):
        super().__init__(text)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.clicked.connect(connect)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                font_size: {font_size}px;
            }}
""")
        if tooltip:
            add_tooltip(self, tooltip)


class WideButton(QPushButton):
    def __init__(
        self,
        text: str,
        connect: Callable | None = None,
        tooltip: str | None = None,
        font_size: int = 20,
    ):
        super().__init__(text)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.clicked.connect(connect)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                font-size: {font_size}px;
                font-weight: bold;
                padding: 5px 40px 5px 40px;
                border-radius: 5px;
                border: 1px solid black;
            }}

            QPushButton::hover {{
                background-color: {Colors.v_light_blue}
            }}
""")
        if tooltip:
            add_tooltip(self, tooltip)


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


class CorpusLabel(QLabel):
    def __init__(
        self, text, color: tuple[int, int, int], text_color: str = "black"
    ) -> None:
        super().__init__(text)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(f""" 
            QLabel {{
                background-color: rgb{color};
                color: {text_color};
                border-radius: 5px;
            }}    """)


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

    def set_path(self, path: str | Path | None = None):
        if not path:
            text = self.default_text
        else:
            text = str(path)
        self.text_label.setText(text[-40:])
        add_tooltip(self.text_label, text, add_style=False)


class FolderSelectButton(QPushButton):
    def __init__(self, tooltip: str = "Select Folder"):
        super().__init__()
        icon = Icons.folder_closed()
        self.setIcon(icon)
        self.setIconSize(icon.pixmap(25, 25).size())
        self.setStyleSheet("QPushButton {border: none;}")
        add_tooltip(self, tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class CheckBox(QWidget):
    def __init__(
        self,
        label_text,
        connection: Callable | None = None,
        tooltip: str = "",
        font_size: int = 18,
    ):
        super().__init__()

        # Create the QCheckBox
        self.check_box = QCheckBox()

        # Create the QLabel for the text
        if len(label_text) > 50:
            label_display_text = label_text[:50] + "..."
        else:
            label_display_text = label_text
        self.label = QLabel(label_display_text)

        # Set the font size for the label
        self.label.setStyleSheet(f"font-size: {font_size}px;")

        # Set the layout for this widget
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self.check_box)
        layout.addWidget(self.label)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Set the widget's layout
        self.setLayout(layout)

        # Set the cursor to a pointing hand on hover
        self.check_box.setCursor(Qt.CursorShape.PointingHandCursor)

        # Connect to the provided callback if needed
        if connection:
            self.check_box.stateChanged.connect(connection)

        # Custom styling for the checkbox
        self.check_box.setStyleSheet(f"""  
            QCheckBox {{
                font-size: {font_size}px;  /* Font size for the checkbox */
                spacing: 5px;
            }}
            QCheckBox::indicator {{
                background-color: white;
                width: 20px;     
                height: 20px;  
                border-radius: 5px;
                border: 2px solid black;
            }}
            QCheckBox::indicator:checked {{
                background-color: {Colors.med_blue};
            }}
        """)

        tooltip = tooltip or label_text
        add_tooltip(self, tooltip)


class RadioButton(QRadioButton):
    def __init__(self, label, connection: Callable | None = None, tooltip: str = ""):
        super().__init__()
        self.setText(str(label))
        self.label = label
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if connection:
            self.toggled.connect(connection)
        self.setStyleSheet(f"""  
                QRadioButton {{
                    font-size: 18px;  
                    color: black;    
                    spacing: 5px;   
                }}
                           
                QRadioButton::indicator {{
                    width: 20px;
                    height: 20px;
                    border: 2px solid black; /* Border for the indicator */
                    border-radius: 12px; /* Ensure the indicator is circular */
                    background-color: white; /* Default background */
                    margin: 0px;
                }}

                QRadioButton::indicator:checked {{
                    background-color: {Colors.med_blue}; /* Background color when checked */
                }}

            """)
        if tooltip:
            add_tooltip(self, tooltip)
