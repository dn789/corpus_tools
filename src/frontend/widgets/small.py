from pathlib import Path
from typing import Any, Callable
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from backend.corpus.items import CorpusItem, MetaProperty, MetaType
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
                font-size: {font_size}px;
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
    def __init__(
        self,
        text,
        tooltip: str = "",
        font_style="normal",
        alignment=Qt.AlignmentFlag.AlignCenter,
    ):
        super().__init__(text)
        self.setStyleSheet(f"""
            color: {Colors.med_blue}; 
            font-weight: bold; 
            font-size: 24px;
            font-style: {font_style};
        """)
        self.setToolTip(tooltip)
        self.setAlignment(alignment)


class VLargeHeading(QLabel):
    def __init__(self, text, tooltip: str = ""):
        super().__init__(text)
        self.setStyleSheet(f"""
            color: {Colors.med_blue}; 
            font-weight: bold; 
            font-size: 30px;
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
        self,
        text,
        color: tuple[int, int, int],
        font_size: int = 16,
        tooltip: str = "",
        id: str | tuple[str, str] | None = None,
    ) -> None:
        super().__init__(text)
        self.color = color
        self.font_size = font_size
        self.tooltip = tooltip
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        text_color = "white" if is_dark(*color) else "black"
        self.setStyleSheet(f""" 
            QLabel {{
                background-color: rgb{color};
                color: {text_color};
                border-radius: 5px;
                padding: 5px;
                font-size: {font_size}px;
            }}    """)
        if tooltip:
            add_tooltip(self, tooltip)

    def get_copy(self):
        return CorpusLabel(text=self.text(), color=self.color, tooltip=self.tooltip)


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
    def __init__(
        self, image_path, icon_size: tuple[int, int] = (20, 20), tooltip: str = ""
    ):
        super().__init__()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.set_icon(image_path, icon_size)
        self.setText("")  # Ensure no text is displayed
        self.setStyleSheet("""
            QPushButton {
                border: none; 
                background: transparent; 
                padding: 0px; 
            }
            """)
        if tooltip:
            add_tooltip(self, tooltip)
        # Make button flat (no visual border effects)
        self.setFlat(True)

    def set_icon(self, image_path: Path, icon_size: tuple[int, int] = (20, 20)) -> None:
        pixmap = QPixmap(image_path)

        scaled_pixmap = pixmap.scaled(
            icon_size[0],
            icon_size[1],
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.setIcon(scaled_pixmap)

        self.setIconSize(scaled_pixmap.size())


class SmallXButton(ImageButton):
    def __init__(self, tooltip: str = ""):
        super().__init__(Icons.x, tooltip=tooltip)


class ArrowButton(ImageButton):
    def __init__(self, tooltip: str = "", down: bool = False):
        icon = Icons.arrow_down if down else Icons.arrow_up
        super().__init__(icon, tooltip=tooltip)

    def up(self):
        self.set_icon(Icons.arrow_up)

    def down(self):
        self.set_icon(Icons.arrow_down)


class FolderSelectWidget(QWidget):
    folderSelected = Signal()

    def __init__(
        self,
        path: Path | None = None,
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
        folder_select_button.clicked.connect(self.select_folder)
        layout.addWidget(folder_select_button)

    def select_folder(self):
        # Open a folder selection dialog
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder", str(self.path) if self.path else ""
        )

        # If a folder was selected, update the path and the label
        if folder:
            self.set_path(Path(folder))  # Update the path attribute and label
            self.path = Path(folder)  # Store the selected path in the path attribute
            self.folderSelected.emit()

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


class MetaPropertySelection(QWidget):
    def __init__(self, meta_prop: MetaProperty) -> None:
        super().__init__()
        self.meta_prop = meta_prop
        self.type = meta_prop.type
        layout = QVBoxLayout()
        self.setLayout(layout)

        text = f"{meta_prop.label_name}-{meta_prop.name}"
        self.label = CorpusLabel(text=text, color=meta_prop.color)
        layout.addWidget(self.label)

        selection_frame = QFrame()
        selection_frame_layout = QVBoxLayout()
        selection_frame.setLayout(selection_frame_layout)
        selection_frame.setStyleSheet(f"""
            border-radius: 5px;
            background-color: {Colors.light_tan};
            font-size: 16px;
        """)
        layout.addWidget(selection_frame)

        if self.type is MetaType.CATEGORICAL:
            self.cat_select = DropDownMenu()
            values = meta_prop.cat_values or []
            self.cat_select.addItems(values)  # type: ignore
            selection_frame_layout.addWidget(self.cat_select)
        else:
            self.min_max_select = MinMaxEntryWidget(
                int(self.meta_prop.min), int(self.meta_prop.max)
            )
            selection_frame_layout.addWidget(self.min_max_select)


class MinMaxEntryWidget(QWidget):
    def __init__(
        self,
        min_default: int = 0,
        max_default: int = 0,
        live_handle: Callable | None = None,
    ):
        super().__init__()
        self.min_default = min_default
        self.max_default = max_default
        self.live_handle = live_handle
        self.initUI()

    def initUI(self) -> None:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        self.min_input = QLineEdit()
        self.min_input.setContentsMargins(0, 0, 0, 0)
        self.min_input.setPlaceholderText(str(self.min_default))
        int_validator = QIntValidator(self.min_default, self.max_default)
        self.min_input.setValidator(int_validator)
        layout.addWidget(self.min_input)
        self.min_input.setStyleSheet("background-color: white;")
        self.min_input.setFixedWidth(50)
        layout.addWidget(QLabel("<b>&ndash;</b>"))
        self.max_input = QLineEdit()
        self.max_input.setContentsMargins(0, 0, 0, 0)
        self.max_input.setPlaceholderText(str(self.max_default))
        int_validator = QIntValidator(self.min_default, self.max_default)
        self.max_input.setValidator(int_validator)
        layout.addWidget(self.max_input)
        self.max_input.setStyleSheet("background-color: white;")
        self.max_input.setFixedWidth(50)

        if self.live_handle:
            self.min_input.textChanged.connect(self.live_handle)
            self.max_input.textChanged.connect(self.live_handle)

        self.setLayout(layout)

    def get_values(self) -> tuple[int, int]:
        min = int(self.min_input.text() or self.min_default)
        max = int(self.max_input.text() or self.max_default)
        return min, max


class CheckBox(QWidget):
    def __init__(
        self,
        item: str | CorpusLabel | MetaPropertySelection,
        connection: Callable | None = None,
        tooltip: str = "",
        font_size: int = 18,
    ):
        super().__init__()
        self.item = item
        # Create the QCheckBox
        self.check_box = QCheckBox()

        # Create the QLabel for the text
        if isinstance(item, str):
            if len(item) > 50:
                label_display_text = item[:50] + "..."
            else:
                label_display_text = item
            self.label = QLabel(label_display_text)
            self.label.setStyleSheet(f"font-size: {font_size}px;")
        else:
            self.label = item

        # Set the font size for the label

        # Set the layout for this widget
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
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
        if isinstance(item, CorpusLabel):
            item_name = item.text()
        elif isinstance(item, MetaPropertySelection):
            item_name = item.meta_prop.name
        else:
            item_name = item
        tooltip = tooltip or item_name
        add_tooltip(self, tooltip)

    def is_checked(self) -> bool:
        return self.check_box.isChecked()

    def uncheck(self) -> None:
        self.check_box.setChecked(False)


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

                QRadioButton:disabled {{
                   color: {Colors.gray}
                }}
                
                QRadioButton::indicator:disabled {{
                    background-color: {Colors.light_gray}; /* Background color when checked */
                }}

            """)
        if tooltip:
            add_tooltip(self, tooltip)


class DropDownMenu(QComboBox):
    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet(f"""
            QComboBox QAbstractItemView {{
                border-radius: 5px;
                background-color: white; 
                outline: 0;
            }}
                           
            QComboBox {{
                background-color: white;  
            }}
            
            QComboBox::item:selected {{
                color: black;
            }}
                           
            QComboBox::drop-down {{
                background-color: white;
                border-radius: 5px;
            }}

            QComboBox::down-arrow {{
                image: url({Icons.arrow_down});
                width: 20px;
                height: 20px;
            }}
                           
        """)


class MetaPropFilter(QWidget):
    def __init__(self, filter_d: dict[str, Any], remove_handle: Callable) -> None:
        super().__init__()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        tag = SmallXButton("Remove filter")
        tag.connect(remove_handle)
        main_layout.addWidget(tag)
        self.setLayout(main_layout)
        for name, d in filter_d.items():
            layout = QHBoxLayout()
            name = "-".join(name)
            prop_label = CorpusLabel(text=name, color=d["meta_prop"].color)
            if isinstance(d["value"], dict):
                value_label = QLabel(f"{d['value']['min']}-{d['value']['max']}")
            else:
                value_label = QLabel(d["value"])
            layout.addWidget(prop_label)
            layout.addWidget(value_label)
            main_layout.addLayout(layout)
