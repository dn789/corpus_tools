from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidgetItem,
    QFileDialog,
)
from PySide6.QtCore import Qt, qDebug


from backend.corpus.items import DocLabel, CorpusItem, Folder
from frontend.project import ProjectWrapper as Project
from frontend.widgets.layouts import HScrollSection, MainColumn, Splitter
from frontend.widgets.small import (
    CorpusTag,
    FolderSelectWidget,
    LargeHeading,
    MediumHeading,
)
from frontend.widgets.trees import FolderViewer, TreeContextMenu


class CorpusConfigTab(QWidget):
    def __init__(self, project: Project):
        super().__init__()
        self.project = project
        self.project.projectLoaded.connect(self.load_config)

        main_layout = QHBoxLayout()
        self.config_view = CorpusConfigView(self.project)
        tree_splitter = Splitter(orientation=Qt.Orientation.Vertical)

        # FolderViewer
        folder_widget_wrapper = QWidget()
        folder_widget_layout = QVBoxLayout()
        folder_widget_layout.addWidget(LargeHeading("Files"))
        self.folder_widget = FolderViewer(self.project)
        folder_widget_layout.addWidget(self.folder_widget)
        folder_widget_wrapper.setLayout(folder_widget_layout)
        tree_splitter.addWidget(folder_widget_wrapper)

        tree_splitter.addWidget(QWidget())
        main_layout.addWidget(self.config_view)
        main_layout.addWidget(tree_splitter)
        self.setLayout(main_layout)

        for widget in (self.folder_widget,):
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
        tree_item = widget.itemAt(pos)
        if tree_item:
            widget.context_menu.add_actions(tree_item)
            widget.context_menu.show(pos)

    def display_doc(self, item: QTreeWidgetItem) -> None:
        item_path = Path(item.data(0, 1))
        if item_path.is_file():
            try:
                self.doc_view_widget.display_file(item_path)
            except:
                pass


class CorpusConfigView(MainColumn):
    def __init__(self, project: Project) -> None:
        self.project = project
        self.config = project.corpus_config
        self.project.corpusConfigUpdated.connect(self.update_corpus_items)
        super().__init__("Configuration")
        self.ref = {}

        corpus_path_widget = QWidget()
        layout = QVBoxLayout()
        corpus_path_widget.setLayout(layout)
        layout.addWidget(MediumHeading("Corpus folder"))
        layout.addWidget(FolderSelectWidget(self.config.corpus_path))
        self.ref["corpus_path"] = corpus_path_widget
        self.add_widget(corpus_path_widget)

        for prop_name in (
            "included_extensions",
            "subfolders",
            "text_labels",
            "meta_labels",
        ):
            self.ref[prop_name] = {
                "widget": HScrollSection(
                    self.project.corpus_config.get_display_name(prop_name), {}
                ),
                "property": getattr(self.project.corpus_config, prop_name),
            }
            self.add_widget(self.ref[prop_name]["widget"])

    def load_config(self):
        if not self.config:
            return
        for prop_name in (
            "included_extensions",
            "subfolders",
            "text_labels",
            "meta_labels",
        ):
            self.ref[prop_name]["widget"].clear()
            self.update_corpus_items(
                prop_name, list(self.ref[prop_name]["property"].values())
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

                widget = CorpusTag(item, tooltip=tooltip, remove_func=remove_func)
                to_add[key] = widget
            prop_widget.add_content(to_add)

    def select_corpus_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self.parent(), "Select Folder")  # type: ignore
        if folder:
            folder = Path(folder)
            self.project.update_corpus_items("corpus_path", folder)
