from typing import Any

from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QTableView,
    QTabWidget,
    QLineEdit,
    QTabBar,
)
from PySide6.QtCore import (
    Qt,
    QSortFilterProxyModel,
    QAbstractTableModel,
    QModelIndex,
    qDebug,
)

from PySide6.QtGui import QFont

# from frontend.tabs.plot.display import ImageDisplayWidget
from frontend.widgets.layouts import HScrollArea
from frontend.widgets.small import ExportResultsWidget
from frontend.widgets.small import SmallXButton, ErrorDisplay


class ImageDisplayWidget:
    pass


class MultiResultsWidget(HScrollArea):
    def __init__(self) -> None:
        self.main_layout = QHBoxLayout()
        super().__init__(self.main_layout)

    def add_result(self, result_widget: QWidget, header: QWidget):
        top_layout = QHBoxLayout()
        top_layout.addWidget(header)
        top_layout.addStretch()
        # Results item for export
        if type(result_widget) is SearchableTable:
            results_item = result_widget.model
        elif type(result_widget) is ErrorDisplay:
            results_item = None
        elif type(result_widget) is ImageDisplayWidget:
            results_item = None
        if results_item:
            export_widget = ExportResultsWidget(
                "Export as...", results_item=results_item
            )
            top_layout.addWidget(export_widget)
        top_layout.setContentsMargins(0, 0, 10, 0)
        top_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        result_layout = QVBoxLayout()
        result_layout.setSpacing(0)
        result_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        result_layout.addLayout(top_layout)
        result_layout.addWidget(result_widget)
        if isinstance(result_widget, (ErrorDisplay, ImageDisplayWidget)):
            result_layout.addStretch()
        self.main_layout.addLayout(result_layout)


class ResultsTabWidget(QTabWidget):
    def __init__(self, tabs: dict[str, QWidget] | None = None):
        super().__init__()
        self.tab_bar = self.tabBar()
        self.tab_bar.setMouseTracking(True)  # type: ignore
        font = QFont()
        font.setPointSize(12)
        self.tab_bar.setFont(font)  # type: ignore

        if tabs:
            for label, widget in tabs.items():
                self.addTab(widget, label)

    def add_tab(self, widget, label):
        index = super().addTab(widget, label)

        remove_button = SmallXButton("Remove this tab")
        remove_button.clicked.connect(
            lambda: self.removeTab(self.tab_bar.currentIndex())  # type: ignore
        )
        remove_button.setVisible(False)
        setattr(self, f"remove_button_{index}", remove_button)
        self.tab_bar.setTabButton(  # type: ignore
            index, QTabBar.ButtonPosition.RightSide, remove_button
        )
        return index


class SearchableTable(QWidget):
    def __init__(self, headers: list[str], data: list[tuple[Any] | list[Any]]):
        super().__init__()

        self.table = QTableView()
        self.data = data

        self.model = TableModel(headers, data)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(-1)  # Search all columns.
        self.proxy_model.setSourceModel(self.model)

        # self.proxy_model.sort(0, Qt.AscendingOrder)

        self.table.setModel(self.proxy_model)

        self.searchbar = QLineEdit()
        self.searchbar.setPlaceholderText("Search...")

        # You can choose the type of search by connecting to a different slot here.
        # see https://doc.qt.io/qt-5/qsortfilterproxymodel.html#public-slots
        self.searchbar.textChanged.connect(self.proxy_model.setFilterFixedString)

        layout = QVBoxLayout()

        layout.addWidget(self.searchbar)
        layout.addWidget(self.table)
        self.setLayout(layout)


class TableModel(QAbstractTableModel):
    def __init__(self, headers, data):
        super().__init__()
        self.headers = headers
        self.data_ = data
        self.rows = len(data)

    def rowCount(self, parent=QModelIndex()):
        return self.rows

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            row = index.row()
            col = index.column()
            return self.data_[row][col] if row < self.rows else None

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.headers[section]
            else:
                return section + 1  # Row numbers starting from 1
        return None
