from typing import Any
from PySide6.QtCore import Qt, qDebug
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSplitter,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
    QScrollArea,
)

from frontend.styles.colors import Colors
from frontend.widgets.small import (
    ArrowButton,
    DropDownMenu,
    LargeHeading,
    MediumHeading,
)


class VSplitter(QSplitter):
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
        self.view_buttons = []
        self.widgets = []
        self.widget_index = 0
        self.splitterMoved.connect(self.set_widgets_visible)
        self.margin = 40

    def add_widget(self, heading: str, widget: QWidget) -> None:
        self.widgets.append(widget)
        heading_layout = QHBoxLayout()
        heading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        widget_layout = QVBoxLayout()
        widget_layout.addLayout(heading_layout)
        widget_layout.addWidget(widget)

        heading_layout.addWidget(LargeHeading(heading))
        down = not self.widget_index
        view_button = ArrowButton(down=down)
        self.view_buttons.append(view_button)
        view_button.clicked.connect(
            lambda _, index=self.widget_index: self.adjust_splitter(index)
        )
        heading_layout.addWidget(view_button)

        wrapper = QWidget()
        wrapper.setLayout(widget_layout)
        self.addWidget(wrapper)

        self.widget_index += 1

    def adjust_splitter(self, index: int) -> None:
        if self.widgets[index].isVisible():
            if self.widgets[abs(index - 1)].isVisible():
                if index:
                    self.splitter_up()
                else:
                    self.splitter_down()
            else:
                if index:
                    self.splitter_down()
                else:
                    self.splitter_up()

        else:
            if not index:
                self.splitter_down()
            else:
                self.splitter_up()

    def splitter_down(self) -> None:
        self.widgets[0].setVisible(True)
        self.widgets[1].setVisible(False)
        self.view_buttons[0].up()
        self.view_buttons[1].up()
        expand_height = self.height() - self.margin
        collapse_height = self.margin
        self.setSizes([expand_height, collapse_height])

    def splitter_up(self) -> None:
        self.widgets[0].setVisible(False)
        self.widgets[1].setVisible(True)
        self.view_buttons[0].down()
        self.view_buttons[1].down()
        expand_height = self.height() - self.margin
        collapse_height = self.margin
        self.setSizes([collapse_height, expand_height])

    def set_widgets_visible(self) -> None:
        self.view_buttons[0].down()
        self.view_buttons[1].up()
        for widget in self.widgets:
            widget.setVisible(True)

    def show_bottom(self) -> None:
        if not self.widgets[1].height() or not self.widgets[1].isVisible():
            self.widgets[0].setVisible(True)
            self.widgets[1].setVisible(True)
            half_height = int(self.height() / 2)
            self.setSizes([half_height, half_height])


class MainColumn(QWidget):
    def __init__(self, heading_text: str | None = None) -> None:
        super().__init__()
        self.setFixedWidth(475)

        outer_layout = QVBoxLayout()
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        outer_layout.setSpacing(10)
        self.content_layout = QVBoxLayout()

        if heading_text:
            heading = LargeHeading(heading_text)
            outer_layout.addWidget(heading)

        scroll_area = ColumnScrollArea(self.content_layout)
        outer_layout.addWidget(scroll_area)

        self.setLayout(outer_layout)

    def add_widget(self, widget: QWidget) -> None:
        self.content_layout.addWidget(widget)

    def add_layout(self, layout: QVBoxLayout | QHBoxLayout | QStackedLayout) -> None:
        self.content_layout.addLayout(layout)


class HScrollSection(QWidget):
    def __init__(
        self,
        heading_text: str,
        content: dict[str, QWidget],
        background_color: str = Colors.light_blue,
        show_content_count: bool = True,
        placeholder_text: str = "None",
        large: bool = False,
        content_spacing: int = 5,
    ):
        super().__init__()
        # Content reference
        self.content_ref = {}

        # Outer layout
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.outer_layout = QVBoxLayout()
        self.setLayout(self.outer_layout)
        # Heading with content count
        self.heading_layout = QHBoxLayout()
        self.heading_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        if large:
            heading = LargeHeading(
                heading_text, font_style="italic", alignment=Qt.AlignmentFlag.AlignLeft
            )
            self.content_count = LargeHeading(
                "()", font_style="italic", alignment=Qt.AlignmentFlag.AlignLeft
            )
        else:
            heading = MediumHeading(heading_text)
            self.content_count = MediumHeading("()")
        if not show_content_count:
            self.content_count.hide()
        self.heading_layout.addWidget(heading)
        self.heading_layout.addWidget(self.content_count)
        self.outer_layout.addLayout(self.heading_layout)

        # Content widget
        self.content_layout = QHBoxLayout()
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.content_layout.setSpacing(content_spacing)
        content_widget = QWidget()
        content_widget.setLayout(self.content_layout)
        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setWidget(content_widget)
        content_widget.setObjectName("ContentScrollArea")
        # Scroll Wrapper
        self.scroll_wrapper = QFrame()
        scroll_wrapper_layout = QVBoxLayout()
        scroll_wrapper_layout.setContentsMargins(10, 0, 10, 0)
        scroll_wrapper_layout.addWidget(scroll_area)
        self.scroll_wrapper.setLayout(scroll_wrapper_layout)
        self.scroll_wrapper.setStyleSheet(f"""
            QFrame {{ 
                border-radius: 5px; 
                background-color: {background_color};
            }}

            QFrame QWidget#ContentScrollArea {{
                background-color: {background_color};
            }}

        """)

        self.outer_layout.addWidget(self.scroll_wrapper)

        self.placeholder_widget = QLabel(f"{placeholder_text}")

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
            self.content_layout.removeWidget(widget)
            widget.deleteLater()
        self.content_ref = {}
        self.content_count.setText(f"({len(self.content_ref)})")
        self.placeholder_widget.show()


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


class HScrollArea(QScrollArea):
    def __init__(self, content: QHBoxLayout | QWidget) -> None:
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

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.v_scroll_bar = self.verticalScrollBar()
        if type(content) is QHBoxLayout:
            content_widget = QWidget()
            content_widget.setObjectName("ContentWidget")
            content_widget.setLayout(content)
        elif type(content) is QWidget:
            content.setObjectName("ContentWidget")
            content_widget = content
        content_widget.layout().setAlignment(Qt.AlignmentFlag.AlignLeft)  # type: ignore
        self.setWidget(content_widget)
        self.main_widget = content_widget


class KeyValueTable(QFrame):
    def __init__(self, data: dict[str, Any]):
        super().__init__()
        self.setStyleSheet(f"""
            font-size: 18px;
            border-radius: 5px;
            padding: 5px;
            background-color: {Colors.light_tan};
""")
        main_layout = QHBoxLayout()
        key_layout = QVBoxLayout()
        value_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addLayout(key_layout)
        main_layout.addLayout(value_layout)
        for k, v in data.items():
            key_layout.addWidget(
                QLabel(f"<i>{k}</i>"), alignment=Qt.AlignmentFlag.AlignRight
            )
            if isinstance(v, set):
                drop_down = DropDownMenu()
                for item in v:
                    drop_down.addItem(item)
                value_layout.addWidget(drop_down)
            else:
                value_layout.addWidget(QLabel(f"<b>{v}</b>"))
