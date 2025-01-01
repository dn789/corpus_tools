from PySide6.QtCore import qDebug
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget
from frozendict import frozendict
from backend.corpus.items import MetaType
from frontend.project import ProjectWrapper as Project
from frontend.styles.colors import Colors, random_color_rgb
from frontend.utils.functions import get_widgets
from frontend.widgets.layouts import HScrollSection, MainColumn
from frontend.widgets.small import (
    Button,
    CheckBox,
    CorpusLabel,
    MetaPropFilter,
    MetaPropertySelection,
)


class CorpusSelectionWidget(MainColumn):
    def __init__(self, project: Project):
        super().__init__("Corpus Selection")
        self.project = project
        self.content_ref = {}
        self.selections = {}
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
        self.filter_layout = QVBoxLayout()
        self.filter_layout.setContentsMargins(10, 0, 10, 0)
        self.content_layout.addLayout(self.filter_layout)

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
            if prop_name == "meta_properties":
                heading_text = "Add meta property filters"
            else:
                heading_text = self.project.corpus_config.get_display_name(prop_name)
            widget = HScrollSection(
                heading_text, data, content_spacing=20, show_content_count=False
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
        filter_l = []
        for checkbox in self.content_ref["meta_properties"].content_ref.values():
            if checkbox.is_checked():
                sub_filter_d = {}
                item = checkbox.item
                meta_prop = item.meta_prop
                sub_filter_d["label_name"] = meta_prop.label_name
                sub_filter_d["name"] = meta_prop.name
                sub_filter_d["meta_prop"] = meta_prop
                if meta_prop.type is MetaType.CATEGORICAL:
                    sub_filter_d["value"] = item.cat_select.currentText()
                else:
                    min_, max_ = item.min_max_select.get_values()
                    sub_filter_d.update({"min": min_, "max": max_})
                filter_l.append(sub_filter_d)
                checkbox.uncheck()

        def remove_filter():
            filter_widget.setParent(None)
            filter_widget.deleteLater()
            self.update_selection()

        filter_widget = MetaPropFilter(filter_l, remove_filter)

        self.filter_layout.addWidget(filter_widget)
        self.update_selection()

    def update_selection(self):
        for prop_name in ("subfolders", "text_categories"):
            self.selections[prop_name] = [
                checkbox.label
                for name, checkbox in self.content_ref[prop_name].content_ref.items()
                if checkbox.is_checked()
            ]
        self.selections["meta_prop_filters"] = get_widgets(self.filter_layout)
        self.display.populate(self.selections)


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
        content = {}
        for i1, subfolder_item in enumerate(selection["subfolders"] or [None]):
            for i2, text_cat_item in enumerate(selection["text_categories"] or [None]):
                for i3, meta_prop_filter in enumerate(
                    selection["meta_prop_filters"] or [None]
                ):
                    selection_frame = SelectionFrame()
                    if subfolder_item:
                        selection_frame.add_widget(subfolder_item.get_copy())
                    if text_cat_item:
                        selection_frame.add_widget(text_cat_item.get_copy())
                    if meta_prop_filter:
                        widget = CorpusLabel(
                            text=f"filter {i3 + 1}",
                            color=meta_prop_filter.color,
                            tooltip=meta_prop_filter.toolTip(),
                        )
                        selection_frame.add_widget(widget)
                    content[(i1, i2, i3)] = selection_frame
        self.add_content(content)
        if not any(v for v in selection.values()):
            self.clear()


class SelectionFrame(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.setStyleSheet(f"""
            QFrame {{
                border-radius: 5px;
                background-color: {Colors.light_tan};          
            }}

    """)

    def add_widget(self, widget: QWidget) -> None:
        self.main_layout.addWidget(widget)
