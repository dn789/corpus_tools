from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from frontend.project import ProjectWrapper as Project
from frontend.widgets.corpus_selection import CorpusSelectionWidget


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
        left_layout.addWidget(CorpusSelectionWidget(self.project))
