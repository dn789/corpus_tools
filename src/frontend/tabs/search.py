from pathlib import Path
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
from styles.icons import Icons


class SearchThread(QThread):
    search_complete = Signal(list)
    model_loaded = Signal(SemanticModel)

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
                self.model_loaded.emit(self.search_model)

            results = self.search_model.query_sents(self.query)
        else:
            results = []
        self.search_complete.emit(results)


class SearchWidget(QWidget):
    def __init__(self, project):
        super().__init__()
        self.model = None
        self.project = project
        self.init_ui()
        # self.corpus_config = self.project.corpus_config

    def init_ui(self):
        # Create main layout
        self.setContentsMargins(20, 20, 20, 20)
        self.main_layout = QHBoxLayout()
        # self.corpus_select_widget = CorpusSelectWidget(self.project)
        # self.corpus_select_widget.selectionUpdated.connect(self.set_selection)
        # scroll_area = ScrollArea(self.corpus_select_widget)
        # scroll_area.setFixedWidth(475)
        # self.main_layout.addWidget(scroll_area)
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
        # self.loading_gif = LoadingGif()
        # self.search_layout.addWidget(self.loading_gif)
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
        # self.loading_gif.start()
        self.search_button.setEnabled(False)
        self.query = self.search_bar.text().strip()  # Get the trimmed search text
        if not self.query:  # Only proceed if there is text
            return  # Do nothing if the search bar is empty
        search_type = (
            "semantic" if self.semantic_search_checkbox.is_checked() else "keyword"
        )
        self.search_thread = SearchThread(
            self.query, search_type, self.project, self.model
        )
        self.search_thread.search_complete.connect(self.display_results)
        if not self.model:
            self.search_thread.model_loaded.connect(self.load_model)
        self.search_thread.start()

    def load_model(self, model):
        self.model = model

    def display_results(self, results):
        self.results_table.horizontalHeader().setVisible(True)
        self.description.setText(f'Results for "{self.query}":')
        self.results_table.setRowCount(0)
        subfolders = self.project.get_setting_value("corpus", "subfolders")
        for i, (result, filename, _) in enumerate(results):
            filename = Path(filename)
            for subfolder in subfolders:
                if subfolder in filename.parents:
                    break
            self.results_table.insertRow(i)
            self.results_table.setItem(i, 0, QTableWidgetItem(result))
            self.results_table.setItem(i, 1, QTableWidgetItem(filename.__str__()))
            self.results_table.setItem(i, 2, QTableWidgetItem(subfolder.name))
        # self.loading_gif.stop()
        self.search_button.setEnabled(True)
        self.search_thread.quit()

    # def set_selection(self, selection: dict[str, list[DisplayItem]]):
    #     for folder_selection in selection['folder']:
    #         for text_selection in selection['text']:
    #         for


class SearchDescriptionBox(QTextEdit):
    def __init__(self, text, height=85, style_sheet: str | None = None):
        super().__init__()
        self.setReadOnly(True)
        self.setFixedHeight(height)
        self.setFontPointSize(11)
        self.setText(text)
        if style_sheet:
            self.setStyleSheet(style_sheet)
