from PySide6.QtCore import qDebug
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget
from backend.corpus.items import MetaProperty, MetaType
from frontend.project import ProjectWrapper as Project
from frontend.styles.colors import Colors
from frontend.widgets.layouts import HScrollSection, MainColumn, SmallHScrollArea
from frontend.widgets.small import (
    Button,
    CheckBox,
    CorpusLabel,
    DropDownMenu,
    MetaPropFilter,
    MetaPropertySelection,
)


class CorpusSelectionWidget(MainColumn):
    def __init__(self, project: Project):
        super().__init__("Corpus Selection")
        self.project = project
        self.content_ref = {}
        self.selection = {}
        self.project.projectLoaded.connect(self.add_widgets)
        self.display = CorpusSelectionDisplay()
        self.add_widgets()

        # Add filter
        self.add_filter_button = Button(
            "Add Filter",
            tooltip="Add meta property filter to selections",
            connect=self.add_filter,
        )
        add_filter_button_layout = QVBoxLayout()
        add_filter_button_layout.setContentsMargins(20, 0, 10, 0)
        add_filter_button_layout.addWidget(self.add_filter_button)
        self.add_filter_button.setDisabled(True)
        self.content_layout.addLayout(add_filter_button_layout)
        self.filter_frame = SmallHScrollArea()
        self.content_layout.addWidget(self.filter_frame)

        # Selection display
        self.content_layout.addWidget(self.display)  # type: ignore

    def add_widgets(self):
        for prop_name in ("subfolders", "text_categories", "meta_properties"):
            data = {}
            if prop_name == "meta_properties":
                for parent_name, properties_d in getattr(
                    self.project.corpus_config, prop_name
                ).items():
                    for name, item in properties_d.items():
                        meta_prop_selection = MetaPropertySelection(item)
                        data[(parent_name, name)] = CheckBox(
                            meta_prop_selection, connection=self.toggle_filter_button
                        )
            else:
                for name, item in getattr(
                    self.project.corpus_config, prop_name
                ).items():
                    corpus_label = CorpusLabel(item.name, item.color, id=name)
                    data[name] = CheckBox(
                        corpus_label, connection=self.update_selection
                    )
            if not data:
                continue
            widget = HScrollSection(
                self.project.corpus_config.get_display_name(prop_name),
                data,
                content_spacing=20,
            )
            self.content_ref[prop_name] = widget
            self.add_widget(widget)

    def toggle_filter_button(self) -> None:
        if any(
            checkbox.is_checked()
            for checkbox in self.content_ref["meta_properties"].content_ref.values()
        ):
            self.add_filter_button.setEnabled(True)
        else:
            self.add_filter_button.setDisabled(True)

    def add_filter(self) -> None:
        filter_d = {}
        for checkbox in self.content_ref["meta_properties"].content_ref.values():
            if checkbox.is_checked():
                qDebug("checkbox")
                item = checkbox.item
                meta_prop = item.meta_prop
                id = (meta_prop.label_name, meta_prop.name)
                filter_d[id] = {"meta_prop": meta_prop}
                if meta_prop.type is MetaType.CATEGORICAL:
                    filter_d[id]["value"] = item.cat_select.currentText()
                else:
                    min_, max_ = item.min_max_select.get_values()
                    filter_d[id]["value"] = {"min": min_, "max": max_}
                checkbox.uncheck()
        def remove_handle():
            
        self.filter_frame.add_widget(MetaPropFilter(filter_d))

    def update_selection(self):
        for prop_name in ("subfolders", "text_categories", "meta_properties"):
            self.selection[prop_name] = [
                checkbox.label
                for name, checkbox in self.content_ref[prop_name].content_ref.items()
                if checkbox.is_checked()
            ]
        self.display.populate(self.selection)


class CorpusSelectionDisplay(HScrollSection):
    def __init__(self):
        super().__init__(
            "Selections",
            {},
            content_spacing=15,
            placeholder_text="Whole corpus",
        )
        self.setFixedHeight(200)
        self.placeholder_widget.setStyleSheet("font-size: 20px;")

    def populate(self, selection: dict[str, list[CorpusLabel]]):
        self.clear()
        qDebug(str(selection))
        content = {}
        for i1, subfolder_item in enumerate(selection["subfolders"] or [None]):
            for i2, text_cat_item in enumerate(selection["text_categories"] or [None]):
                for i3, meta_prop_item in enumerate(
                    selection["meta_properties"] or [None]
                ):
                    selection_frame = QFrame()
                    selection_layout = QVBoxLayout()
                    selection_frame.setLayout(selection_layout)
                    if subfolder_item:
                        selection_layout.addWidget(subfolder_item.get_copy())
                    if text_cat_item:
                        selection_layout.addWidget(text_cat_item.get_copy())
                    if meta_prop_item:
                        selection_layout.addWidget(meta_prop_item.get_copy())
                    content[(i1, i2, i3)] = selection_frame
        self.add_content(content)
        if not any(v for v in selection.values()):
            self.placeholder_widget.show()
