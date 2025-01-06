from pathlib import Path
import time

from PySide6.QtWidgets import (
    QLabel,
    QSizePolicy,
    QStackedLayout,
    QStackedWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidgetItem,
    QFileDialog,
)
from PySide6.QtCore import QThread, Qt, Signal, qDebug


from backend.corpus.process.process_doc import file_to_doc
from backend.corpus.items import DocLabel, CorpusItem, Folder
from frontend.project import ProjectWrapper as Project
from frontend.styles.colors import Colors
from frontend.widgets.layouts import HScrollSection, MainColumn, VSplitter
from frontend.widgets.progress import ProgressBackend, ProgressWidget
from frontend.widgets.small import (
    Button,
    CorpusTag,
    FolderSelectWidget,
    MediumHeading,
)
from frontend.widgets.trees import FolderViewer, DocViewer, TreeContextMenu


class ProcessCorpusThread(QThread):
    taskInfo = Signal(str, int)
    increment = Signal()
    complete = Signal()

    def __init__(self, project: Project):
        super().__init__()
        self.project = project
        self.progress_backend = ProgressBackend()
        self.progress_backend.taskInfo.connect(self.taskInfo)
        self.progress_backend.increment.connect(self.increment)

    def run(self):
        self.project.process_corpus(frontend_connect=self.progress_backend)
        self.project.save_config()
        self.complete.emit()


class CorpusConfigTab(QWidget):
    tabChange = Signal(int)

    def __init__(self, project: Project):
        super().__init__()
        self.project = project
        self.project.projectLoaded.connect(self.load_config)

        main_layout = QHBoxLayout()
        self.config_view = CorpusConfigView(self, self.project)
        self.tree_splitter = VSplitter(orientation=Qt.Orientation.Vertical)

        # FolderViewer
        self.folder_widget = FolderViewer(self.project)
        self.tree_splitter.add_widget("Files", self.folder_widget)

        self.doc_widget = DocViewer(self.project)
        self.tree_splitter.add_widget("Document", self.doc_widget)

        self.folder_widget.itemDoubleClicked.connect(self.display_doc)

        main_layout.addWidget(self.config_view)
        main_layout.addWidget(self.tree_splitter)

        self.setLayout(main_layout)

        for widget in (self.folder_widget, self.doc_widget):
            widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            widget.context_menu = TreeContextMenu(  # type: ignore
                widget, self.project
            )
            widget.customContextMenuRequested.connect(
                lambda pos, widget=widget: self.show_context_menu(pos, widget)
            )

        self.load_config()

    def load_config(self):
        self.config_view.load_config()

    def show_context_menu(self, pos, widget):
        tagged_text_under_node = False
        tree_item = widget.itemAt(pos)
        if tree_item:
            data = tree_item.data(0, 1)
            tree_item_widget = widget.itemWidget(tree_item, 0)
            if isinstance(widget, DocViewer):
                tagged_text_under_node = widget.check_for_tagged_text(tree_item)
            widget.context_menu.add_actions(  # type: ignore
                data, tree_item_widget, tagged_text_under_node
            )
            widget.context_menu.show(pos)  # type: ignore

    def display_doc(self, item: QTreeWidgetItem) -> None:
        item_path = Path(item.data(0, 1))
        if item_path.is_file():
            try:
                doc = file_to_doc(item_path)
                self.doc_widget.populate_tree(doc, item_path)  # type: ignore
            except NotImplementedError:
                pass
        self.tree_splitter.show_bottom()


class CorpusConfigView(MainColumn):
    def __init__(self, parent: QWidget, project: Project) -> None:
        self.parent = parent  # type: ignore
        self.project = project
        self.config = project.corpus_config
        self.project.corpusConfigUpdated.connect(self.update_corpus_items)
        super().__init__("Configuration")
        self.ref = {}

        # Corpus path widget
        corpus_path_widget_wrapper = QWidget()
        layout = QVBoxLayout()
        corpus_path_widget_wrapper.setLayout(layout)
        layout.addWidget(MediumHeading("Corpus folder"))
        corpus_path_widget = FolderSelectWidget(self.config.corpus_path)
        corpus_path_widget.folderSelected.connect(self.new_project_from_corpus_path)
        layout.addWidget(corpus_path_widget)
        self.ref["corpus_path"] = corpus_path_widget
        self.add_widget(corpus_path_widget_wrapper)

        for prop_name, placeholder_text in (
            ("included_extensions", "Extensions of files to include in the analysis"),
            ("subfolders", "Subfolders to analyze individually"),
            (
                "text_labels",
                "Document labels (e.g. nodes in XML files or keys in JSON files) representing text content",
            ),
            (
                "meta_labels",
                'Document labels representing meta content, such as "age" or  "education level" ',
            ),
        ):
            self.ref[prop_name] = {
                "widget": HScrollSection(
                    self.project.corpus_config.get_display_name(prop_name),
                    {},
                    placeholder_text=placeholder_text,
                ),
                "prop_name": prop_name,
            }
            self.add_widget(self.ref[prop_name]["widget"])

        self.make_process_corpus_layout()

    def make_process_corpus_layout(self):
        self.process_corpus_widget = QStackedWidget()
        self.process_corpus_widget.setContentsMargins(35, 30, 10, 10)
        self.process_corpus_widget.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.add_widget(self.process_corpus_widget)

        self.process_corpus_button = Button(
            "Process corpus",
            font_size=24,
            tooltip="Click to process corpus after configuring",
        )
        self.process_corpus_button.setFixedSize(200, 50)
        self.process_corpus_button.clicked.connect(self.process_corpus_thread)
        self.process_corpus_widget.addWidget(self.process_corpus_button)

        self.progress_widget = ProgressWidget()
        self.process_corpus_widget.addWidget(self.progress_widget)

        self.processing_complete_widget = QWidget()
        processing_complete_layout = QVBoxLayout()
        processing_complete_layout.setSpacing(10)
        processing_complete_layout.setContentsMargins(0, 0, 0, 0)
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        button_layout.setSpacing(15)

        processing_complete_label = QLabel("Corpus processed")
        processing_complete_label.setStyleSheet(
            f"font-weight: bold; font-size: 26px; color: {Colors.green}"
        )
        processing_complete_layout.addWidget(processing_complete_label)

        process_again_button = Button(
            "Process again",
            font_size=20,
            connect=self.process_corpus_thread,
            tooltip="Process corpus again",
        )
        button_layout.addWidget(process_again_button)
        overview_button = Button(
            "Go to overview",
            font_size=20,
            connect=lambda: self.parent.tabChange.emit(1),
            tooltip="Go to processed corpus overview",
        )

        button_layout.addWidget(overview_button)
        processing_complete_layout.addLayout(button_layout)

        self.processing_complete_widget.setLayout(processing_complete_layout)
        self.process_corpus_widget.addWidget(self.processing_complete_widget)
        self.process_corpus_widget.setCurrentWidget(self.processing_complete_widget)

    def process_corpus_thread(self):
        self.process_corpus_button.setDisabled(True)
        self.process_corpus_button.hide()
        self.process_corpus_widget.setCurrentWidget(self.progress_widget)
        thread = ProcessCorpusThread(self.project)
        thread.taskInfo.connect(self.progress_widget.load_task)
        thread.increment.connect(self.progress_widget.increment)
        thread.start()
        thread.complete.connect(lambda: thread.quit())
        thread.complete.connect(self.on_corpus_processed)

    def on_corpus_processed(self) -> None:
        self.progress_widget.complete()
        self.process_corpus_widget.setCurrentWidget(self.processing_complete_widget)
        self.process_corpus_button.setEnabled(True)
        self.project.config.status["corpus_processed"] = True
        # self.process_corpus_button.show()
        self.project.corpusProcessed.emit()

    def new_project_from_corpus_path(self):
        self.project.new_project()
        self.project.update_corpus_items("corpus_path", self.ref["corpus_path"].path)

    def load_config(self):
        if not self.config:
            return
        self.ref["corpus_path"].set_path(self.project.corpus_config.corpus_path)
        for prop_name in (
            "included_extensions",
            "subfolders",
            "text_labels",
            "meta_labels",
        ):
            self.ref[prop_name]["widget"].clear()
            self.update_corpus_items(
                prop_name, list(getattr(self.project.corpus_config, prop_name).values())
            )
        if not self.project.config.status["corpus_processed"]:
            self.processing_complete_widget.hide()
            self.process_corpus_button.show()

    def update_corpus_items(
        self,
        prop_name: str,
        content: CorpusItem | list[CorpusItem] | str | list[str] | Path,
        remove: bool = False,
    ):
        if prop_name == "corpus_path":
            self.ref["corpus_path"].set_path(content)
            return
        prop_widget = self.ref[prop_name]["widget"]
        content = content if type(content) is list else [content]  # type: ignore
        if remove:
            for name in content:  # type: ignore
                prop_widget.remove_content(name)
        else:
            corpus_items: list[CorpusItem] = content  # type: ignore
            to_add = {}
            for item in corpus_items:
                key = self.project.corpus_config.get_item_key(item)
                # Get tooltip text
                if type(item) is DocLabel:
                    tooltip = item.get_tooltip() or item.name
                elif type(item) is Folder:
                    tooltip = item.path.__str__()
                else:
                    tooltip = item.name

                def remove_func(
                    prop_name=prop_name,
                    remove_key=key,
                ):
                    return self.project.update_corpus_items(
                        prop_name, remove_key, remove=True
                    )

                widget = CorpusTag(item, tooltip=tooltip, remove_func=remove_func)  # type: ignore
                to_add[key] = widget
            prop_widget.add_content(to_add)

    def select_corpus_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self.parent(), "Select Folder")  # type: ignore
        if folder:
            folder = Path(folder)
            self.project.update_corpus_items("corpus_path", folder)
