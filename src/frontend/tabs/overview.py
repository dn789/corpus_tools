from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from backend.corpus.items import (
    CorpusItem,
    Folder,
    MetaProperty,
    MetaType,
    TextCategory,
)
from frontend.project import ProjectWrapper as Project
from frontend.styles.colors import is_dark
from frontend.utils.functions import clear_layout
from frontend.widgets.layouts import HScrollSection, KeyValueTable
from frontend.widgets.small import CorpusLabel, VLargeHeading


class Overview(QWidget):
    def __init__(self, project: Project) -> None:
        super().__init__()
        self.project = project
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.content_layout = QVBoxLayout()
        self.main_layout.addWidget(VLargeHeading("Corpus Overview"))
        self.main_layout.addLayout(self.content_layout)
        self.project.projectLoaded.connect(self.add_widgets)
        self.project.corpusProcessed.connect(self.add_widgets)
        self.main_layout.setContentsMargins(100, 50, 100, 100)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.add_widgets()

    def add_widgets(self):
        clear_layout(self.content_layout)
        for prop_name in ("subfolders", "text_categories", "meta_properties"):
            data = {}
            if prop_name == "meta_properties":
                for parent_name, properties_d in getattr(
                    self.project.corpus_config, prop_name
                ).items():
                    for name, item in properties_d.items():
                        data[(parent_name, name)] = CorpusOverviewItem(
                            item, name=f"{parent_name}-{name}"
                        )
            else:
                for name, item in getattr(
                    self.project.corpus_config, prop_name
                ).items():
                    data[name] = CorpusOverviewItem(item)
            widget = HScrollSection(
                self.project.corpus_config.get_display_name(prop_name), data, large=True
            )
            self.content_layout.addWidget(widget)


class CorpusOverviewItem(QWidget):
    def __init__(self, item: CorpusItem, name: str | None = None) -> None:
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        name = name or item.name
        label = CorpusLabel(text=name, color=item.color, font_size=20)
        layout.addWidget(label)
        info_layout = QVBoxLayout()
        layout.addLayout(info_layout)
        if isinstance(item, (Folder, TextCategory)):
            data = {"Sentence count": item.sent_count, "Word count": item.word_count}
            info_layout.addWidget(KeyValueTable(data))
        elif isinstance(item, MetaProperty):
            data = {
                "parent label": item.label_name,
                "type": item.type.name.lower(),  # type: ignore
            }
            if item.type is MetaType.QUANTITATIVE:
                data.update({"value range": f"{item.min} - {item.max}"})
            else:
                data.update({"values": item.cat_values})  # type: ignore
            info_layout.addWidget(KeyValueTable(data))
