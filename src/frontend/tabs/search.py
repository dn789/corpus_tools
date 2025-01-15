"""
"Search" tab

-Semantic search
- Will add filtering by corpus properties and regex

"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
)
from PySide6.QtCore import Qt, QThread, Signal

from backend.nlp_models.semantic import SemanticModel
from frontend.project import ProjectWrapper as Project
from frontend.widgets.small import (
    CheckBox,
    ImageButton,
    LargeHeading,
)
from frontend.styles.icons import Icons


class SearchThread(QThread):
    searchComplete = Signal(list)
    modelLoaded = Signal(SemanticModel)

    def __init__(
        self,
        query: str,
        type: str,
        project: Project,
        search_model: SemanticModel,
    ):
        super().__init__()
        self.query = query
        self.type = type
        self.project = project
        self.search_model = search_model
        self.corpus_selection = None

    def run(self):
        if self.type == "semantic":
            if not self.search_model:
                # sent_dicts = self.project.db.get_all_sents()['sent_dicts']
                self.search_model = SemanticModel()
                self.modelLoaded.emit(self.search_model)
            sent_ds = self.project.db.get_all_sents(include_embeddings=True)[
                "sent_dicts"
            ]  # type: ignore
            results = self.search_model.query_sents_from_db(self.query, sent_ds)
        else:
            results = []
        self.searchComplete.emit(results)


class SearchWidget(QWidget):
    def __init__(self, project):
        super().__init__()
        self.model = None
        self.project = project
        self.init_ui()

    def init_ui(self):
        self.setContentsMargins(20, 20, 20, 20)
        self.main_layout = QHBoxLayout()

        self.main_search_layout = QVBoxLayout()
        self.main_search_layout.addWidget(LargeHeading("Search"))
        options_layout = QHBoxLayout()
        self.search_layout = QHBoxLayout()

        # Search bar and button
        self.search_bar = QLineEdit(self)
        self.search_bar.setFixedWidth(400)
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.toggle_search_button)
        self.search_bar.returnPressed.connect(self.search)
        self.search_bar.setStyleSheet("font-size: 20px")
        self.search_layout.addWidget(
            self.search_bar, alignment=Qt.AlignmentFlag.AlignVCenter
        )

        self.search_button = ImageButton(Icons.search)
        self.search_button.clicked.connect(self.search)
        self.search_button.setDisabled(True)
        self.search_layout.addWidget(
            self.search_button, alignment=Qt.AlignmentFlag.AlignVCenter
        )

        self.search_layout.setSpacing(5)
        self.search_layout.addStretch()

        # Search options
        self.semantic_search_checkbox = CheckBox("Semantic (topic search)", print)
        self.semantic_search_checkbox.check_box.setChecked(True)

        options_layout.addWidget(self.semantic_search_checkbox)
        options_layout.addStretch()

        # Search button

        self.main_search_layout.addLayout(self.search_layout)
        self.main_search_layout.addLayout(options_layout)
        self.description = SearchDescriptionBox(
            "",
            height=30,
            style_sheet="background-color: transparent; font-style: italic;",
        )
        self.main_search_layout.addWidget(self.description)

        # Results table
        self.results_table = QTableWidget(self)
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(
            ["Result", "Filename", "Subfolder"]
        )
        self.results_table.horizontalHeader().setVisible(False)
        self.results_table.setColumnWidth(0, 500)
        self.results_table.setColumnWidth(1, 150)
        self.main_search_layout.addWidget(self.results_table)
        self.main_search_layout.setSpacing(15)
        self.main_layout.addLayout(self.main_search_layout)
        self.setLayout(self.main_layout)

    def toggle_search_button(self):
        text = self.search_bar.text().strip()
        self.search_button.setEnabled(bool(text))

    def resize_table_columns(self, event):
        total_width = self.results_table.width()
        self.results_table.setColumnWidth(0, int(total_width * 0.75))
        self.results_table.setColumnWidth(1, int(total_width * 0.25))
        super().resizeEvent(event)

    def search(self):
        self.search_button.setEnabled(False)
        self.query = self.search_bar.text().strip()  # Get the trimmed search text
        if not self.query:  # Only proceed if there is text
            return  # Do nothing if the search bar is empty
        search_type = (
            "semantic" if self.semantic_search_checkbox.is_checked() else "keyword"
        )
        self.search_thread = SearchThread(
            self.query,
            search_type,
            self.project,
            self.model,  # type: ignore
        )
        self.search_thread.searchComplete.connect(self.display_results)
        if not self.model:
            self.search_thread.modelLoaded.connect(self.load_model)
        self.search_thread.start()

    def load_model(self, model):
        self.model = model

    def display_results(self, results):
        self.results_table.horizontalHeader().setVisible(True)
        self.description.setText(f'Results for "{self.query}":')
        self.results_table.setRowCount(0)
        for i, (d) in enumerate(results):
            self.results_table.insertRow(i)
            self.results_table.setItem(i, 0, QTableWidgetItem(d["sentence"]))
            self.results_table.setItem(i, 1, QTableWidgetItem(d["file_path"].__str__()))
        self.search_button.setEnabled(True)
        self.search_thread.quit()


class SearchDescriptionBox(QTextEdit):
    def __init__(self, text, height=85, style_sheet: str | None = None):
        super().__init__()
        self.setReadOnly(True)
        self.setFixedHeight(height)
        self.setFontPointSize(11)
        self.setText(text)
        if style_sheet:
            self.setStyleSheet(style_sheet)
