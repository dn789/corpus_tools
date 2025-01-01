from PySide6.QtCore import qDebug
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from frontend.project import ProjectWrapper as Project
from frontend.widgets.corpus_selection import CorpusSelectionWidget
from frontend.widgets.small import Button


class BasicAnalysisWidget(QWidget):
    def __init__(self, project: Project):
        super().__init__()
        self.project = project
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        right_layout.addWidget(QWidget())
        self.corpus_selection_widget = CorpusSelectionWidget(self.project)
        left_layout.addWidget(self.corpus_selection_widget)
        button = Button("Selections", connect=self.get_selections)
        button.setFixedSize(300, 300)
        left_layout.addWidget(button)

    def get_selections(self):
        widget_selections = self.corpus_selection_widget.selections
        if not widget_selections:
            return
        selections = {}
        for prop_name in ("subfolders", "text_categories"):
            selections[prop_name] = [
                item.text() for item in widget_selections[prop_name]
            ]
        selections["meta_properties"] = [
            filter_widget.filter_l
            for filter_widget in widget_selections["meta_prop_filters"]
        ]
        qDebug(str(selections))
