from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidgetItem,
    QFileDialog,
)
from PySide6.QtCore import Qt, qDebug


from backend.corpus.process.process_doc import file_to_doc
from backend.corpus.items import DocLabel, CorpusItem, Folder
from frontend.project import ProjectWrapper as Project
from frontend.widgets.layouts import HScrollSection, MainColumn, VSplitter
from frontend.widgets.small import (
    CorpusTag,
    FolderSelectWidget,
    MediumHeading,
)
from frontend.widgets.trees import FolderViewer, DocViewer, TreeContextMenu


class CorpusConfigTab(QWidget):
    def __init__(self, project: Project):
        super().__init__()
        self.project = project
        self.project.projectLoaded.connect(self.load_config)

        main_layout = QHBoxLayout()
        self.config_view = CorpusConfigView(self.project)
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
    def __init__(self, project: Project) -> None:
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
