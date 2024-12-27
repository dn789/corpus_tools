from PySide6.QtCore import Qt, qDebug
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QScrollArea,
)

from frontend.styles.colors import Colors
from frontend.widgets.small import LargeHeading, MediumHeading


class Splitter(QSplitter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.setHandleWidth(15)
        self.setStyleSheet(f"""
            QSplitter::handle:vertical {{
                border: 1px dashed black;
                border-radius: 5px;
                background-color: {Colors.v_light_blue};
            }}
        """)


class MainColumn(QWidget):
    def __init__(self, heading_text: str) -> None:
        super().__init__()
        self.setFixedWidth(475)

        outer_layout = QVBoxLayout()
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        outer_layout.setSpacing(10)
        self.content_layout = QVBoxLayout()

        heading = LargeHeading(heading_text)
        outer_layout.addWidget(heading)

        scroll_area = ColumnScrollArea(self.content_layout)
        outer_layout.addWidget(scroll_area)

        self.setLayout(outer_layout)

    def add_widget(self, widget: QWidget) -> None:
        self.content_layout.addWidget(widget)

    def add_layout(self, layout: QVBoxLayout | QHBoxLayout) -> None:
        self.content_layout.addLayout(layout)


class HScrollSection(QWidget):
    def __init__(
        self,
        heading_text: str,
        content: dict[str, QWidget],
        background_color: str = Colors.light_blue,
        show_content_count: bool = True,
        placeholder_text: str = "None",
    ):
        super().__init__()
        # Content reference
        self.content_ref = {}

        # Outer layout
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.outer_layout = QVBoxLayout()
        self.setLayout(self.outer_layout)

        # Heading with content count
        heading_layout = QHBoxLayout()
        heading_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        heading = MediumHeading(heading_text)
        self.content_count = MediumHeading("()")
        if not show_content_count:
            self.content_count.hide()
        heading_layout.addWidget(heading)
        heading_layout.addWidget(self.content_count)
        self.outer_layout.addLayout(heading_layout)

        # Content widget
        self.content_layout = QHBoxLayout()
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.content_layout.setSpacing(5)
        content_widget = QWidget()
        content_widget.setLayout(self.content_layout)
        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setWidget(content_widget)
        content_widget.setObjectName("ContentScrollArea")
        # Scroll Wrapper
        scroll_wrapper = QFrame()
        scroll_wrapper_layout = QVBoxLayout()
        scroll_wrapper_layout.setContentsMargins(10, 0, 10, 0)
        scroll_wrapper_layout.addWidget(scroll_area)
        scroll_wrapper.setLayout(scroll_wrapper_layout)
        scroll_wrapper.setStyleSheet(f"""
            QFrame {{ 
                border-radius: 5px; 
                background-color: {background_color};
            }}

            QFrame QWidget#ContentScrollArea {{
                background-color: {background_color};
            }}

        """)

        self.outer_layout.addWidget(scroll_wrapper)

        self.placeholder_widget = QLabel(f"<i>{placeholder_text}</i>")
        self.placeholder_widget.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum
        )
        self.placeholder_widget.setWordWrap(True)
        self.placeholder_widget.setStyleSheet("font-size: 16px;")
        self.placeholder_widget.hide()
        self.content_layout.addWidget(self.placeholder_widget)
        self.add_content(content)

    def add_content(self, content: dict[str, QWidget]) -> None:
        for key, widget in content.items():
            # qDebug("adding")
            self.content_ref[key] = widget
            self.content_layout.addWidget(widget)
        if self.content_ref:
            self.placeholder_widget.hide()
        else:
            self.placeholder_widget.show()
        self.content_count.setText(f"({len(self.content_ref)})")

    def remove_content(self, content_key: str | list[str]) -> None:
        widget = self.content_ref.pop(content_key)
        self.content_layout.removeWidget(widget)
        widget.deleteLater()
        if not self.content_ref:
            self.placeholder_widget.show()
        self.content_count.setText(f"({len(self.content_ref)})")

    def clear(self) -> None:
        for key, widget in self.content_ref.items():
            # qDebug(str(key))
            # qDebug(str(widget))
            # qDebug("\n---------------\n")
            self.content_layout.removeWidget(widget)
            widget.deleteLater()
        self.content_ref = {}


class ColumnScrollArea(QScrollArea):
    def __init__(self, content: QVBoxLayout | QWidget) -> None:
        super().__init__()
        self.setObjectName("MyScrollArea")
        self.setStyleSheet("""
           
            QWidget#MyScrollArea {
                border: none;            
            }
            QWidget#MyScrollArea QWidget#ContentWidget {
                background-color: white;
            }
        """)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.v_scroll_bar = self.verticalScrollBar()
        if type(content) is QVBoxLayout:
            content_widget = QWidget()
            content_widget.setObjectName("ContentWidget")
            content_widget.setLayout(content)
        elif type(content) is QWidget:
            content.setObjectName("ContentWidget")
            content_widget = content
        content_widget.layout().setAlignment(Qt.AlignmentFlag.AlignTop)  # type: ignore
        self.setWidget(content_widget)
        self.main_widget = content_widget
