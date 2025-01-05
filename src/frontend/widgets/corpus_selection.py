from typing import Any
from PySide6.QtCore import Signal, qDebug
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget
from backend.corpus.items import LabelType, MetaType
from frontend.project import ProjectWrapper as Project
from frontend.styles.colors import Colors
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
    selectionsUpdate = Signal(bool)

    def __init__(self, project: Project):
        super().__init__()
        self.project = project
        self.content_ref = {}
        self.selections_d = {}
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
        self.content_layout.setContentsMargins(0, 0, 0, 0)
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
                        corpus_label, connection=self.update_selections_d
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
            self.update_selections_d()

        filter_widget = MetaPropFilter(filter_l, remove_filter)

        self.filter_layout.addWidget(filter_widget)
        self.update_selections_d()

    def update_selections_d(self):
        self.selections_d = {}
        for prop_name in ("subfolders", "text_categories"):
            self.selections_d[prop_name] = [
                checkbox.label
                for name, checkbox in self.content_ref[prop_name].content_ref.items()
                if checkbox.is_checked()
            ]
        self.selections_d["meta_prop_filters"] = get_widgets(self.filter_layout)
        selections_update = self.display.show_selections(self.selections_d)
        self.selectionsUpdate.emit(selections_update)

    def get_selections(self) -> list[dict[str, list[str | dict]]]:
        selections = []
        if not self.selections_d:
            return []
        for subfolder_item in self.selections_d["subfolders"] or [None]:
            for text_cat_item in self.selections_d["text_categories"] or [None]:
                for meta_prop_filter in self.selections_d["meta_prop_filters"] or [
                    None
                ]:
                    selection = {}
                    if subfolder_item:
                        selection["subfolders"] = subfolder_item.text()
                    if text_cat_item:
                        selection["text_categories"] = text_cat_item.text()
                    if meta_prop_filter:
                        selection["meta_properties"] = meta_prop_filter.filter_l
                    if selection:
                        selections.append(selection)

        return selections


class CorpusSelectionDisplay(HScrollSection):
    def __init__(self):
        super().__init__(
            "Selections",
            {},
            content_spacing=15,
            placeholder_text="Whole corpus",
        )
        self.setFixedHeight(200)
        self.placeholder_widget.setStyleSheet("font-size: 25px; font-weight: bold;")
        self.last_selections = []

    def show_selections(self, selection: dict[str, list[CorpusLabel]]) -> bool:
        self.clear()
        self.last_selections = []
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
                            id=meta_prop_filter.filter_l,  # type: ignore
                            label_type=LabelType.META,
                        )
                        selection_frame.add_widget(widget)
                    content[(i1, i2, i3)] = selection_frame
                    self.last_selections.append(selection_frame)
        self.add_content(content)
        if not any(v for v in selection.values()):
            self.clear()
            return False
        return True


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

    def get_copy(self):
        new_frame = SelectionFrame()
        widgets = get_widgets(self.main_layout)
        for widget in widgets:
            if widget.label_type is LabelType.META:  # type: ignore
                new_frame.add_widget(QLabel(widget.tooltip))  # type: ignore
            else:
                new_frame.add_widget(widget.get_copy())  # type: ignore
        return new_frame
