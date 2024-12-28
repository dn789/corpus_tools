from typing import Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from backend.corpus.items import DocLabel, LabelType
from frontend.styles.colors import ColorSelectButton, Colors, random_color_rgb
from frontend.widgets.small import Button, CheckBox, RadioButton, WideButton


class MessageBox(QDialog):
    def __init__(
        self,
        message: str,
        window_title: str = "",
        button_text: str = "OK",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(window_title)
        layout = QVBoxLayout(self)
        button_layout = QHBoxLayout()

        label_text = QLabel(message)
        layout.addWidget(label_text)

        ok_button = Button(button_text, self.accept)
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.resize(200, 100)

    @staticmethod
    def information(
        message: str,
        window_title: str = "",
        button_text: str = "OK",
        parent: QWidget | None = None,
    ) -> int:
        dialog = MessageBox(message, window_title, button_text, parent)
        return dialog.exec()


class MakeDocLabel(QDialog):
    def __init__(
        self, key: Any, display_name: str, label_type: LabelType, file_type: str
    ) -> None:
        super().__init__()
        self.setWindowTitle(f"Add to {label_type.name.lower()} labels")
        self.setFixedWidth(500)
        self.setContentsMargins(15, 15, 15, 15)
        # self.setFixedSize(400, 300)
        layout = QVBoxLayout()
        layout.setSpacing(20)
        self.setLayout(layout)
        self.setStyleSheet("font-size: 18px;")

        self.label_attrs_and_checkboxes = {}
        self.value_in_attrs = False
        self.label_type = label_type
        self.file_type = file_type

        line_and_color_layout = QHBoxLayout()
        line_and_color_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        line_and_color_layout.setSpacing(5)
        line_and_color_layout.addWidget(QLabel("Name"))

        # DocLabel name select
        self.doc_label_name_select = QLineEdit(self)
        self.doc_label_name_select.setText(display_name)
        line_and_color_layout.addWidget(self.doc_label_name_select)

        # Color select
        self.color = random_color_rgb()
        self.color_select_button = ColorSelectButton(self.color)  # type: ignore
        self.color_select_button.clicked.connect(self.select_color)
        line_and_color_layout.addWidget(self.color_select_button)
        layout.addLayout(line_and_color_layout)

        # Label name identifier
        file_type_label_name_type_d = {".json": "key", ".xml": "tag"}
        label_name_type = file_type_label_name_type_d.get(file_type, "key")
        self.label_name = key if isinstance(key, str) else key["_tag"]
        label_name_label = QLabel(
            f"{file_type[1:].upper()} {label_name_type}: <b>{self.label_name}</b>"
        )
        layout.addWidget(label_name_label)

        if isinstance(key, dict) and len(key) > 1:
            # Add attributes to label definition
            attr_select_frame = QFrame()
            attr_select_frame.setStyleSheet(
                f"border-radius: 5px; background-color: {Colors.light_blue}"
            )
            attr_select_layout = QVBoxLayout()
            attr_select_frame.setLayout(attr_select_layout)
            attr_select_layout.setSpacing(15)
            instructions = QLabel(
                "<b><i>Add attribute-value pairs to label definition:</i></b>"
            )
            instructions.setWordWrap(True)
            attr_select_layout.addWidget(instructions)
            attr_layout_inner = QVBoxLayout()
            attr_layout_inner.setContentsMargins(20, 0, 0, 0)
            attr_layout_inner.setSpacing(5)
            attr_select_layout.addLayout(attr_layout_inner)
            for attr_name, value in key.items():
                if attr_name == "_tag":
                    continue
                self.label_attrs_and_checkboxes[attr_name] = {
                    "value": value,
                    "checkbox": CheckBox(f"<i>{attr_name}</i>=<b>{value}</b>"),
                }
                attr_layout_inner.addWidget(
                    self.label_attrs_and_checkboxes[attr_name]["checkbox"]
                )

            layout.addWidget(attr_select_frame)

        if isinstance(key, dict):
            # Select value location
            value_location_frame = QFrame()
            value_location_frame.setStyleSheet(
                f"border-radius: 5px; background-color: {Colors.light_blue}"
            )
            value_location_layout = QVBoxLayout()
            value_location_frame.setLayout(value_location_layout)
            value_location_layout.setSpacing(15)
            instructions = QLabel("<b><i>Value location:</i></b>")
            value_location_layout.addWidget(instructions)
            radio_layout = QHBoxLayout()
            radio_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value_location_layout.addLayout(radio_layout)
            text_radio = RadioButton(
                "text content", lambda: self.toggle_attrs_in_values(False)
            )
            attrs_radio = RadioButton(
                "attributes", lambda: self.toggle_attrs_in_values(True)
            )
            text_radio.setChecked(True)
            radio_layout.addWidget(text_radio)
            radio_layout.addWidget(attrs_radio)
            layout.addWidget(value_location_frame)

        # OK and Cancel buttons
        self.ok_button = WideButton("Add", self.accept)
        cancel_button = WideButton("Cancel", self.reject)
        button_layout = QHBoxLayout()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)

        # Connect name entry change to OK button
        self.doc_label_name_select.textChanged.connect(self.on_text_changed)

    def toggle_attrs_in_values(self, bool_: bool) -> None:
        self.value_in_attrs = bool_

    def select_color(self):
        # Open the color dialog and get the selected color
        new_color = QColorDialog().getColor()

        # Check if the color is valid (not cancelled)
        if new_color.isValid():
            self.color = new_color.toTuple()[:-1]  # type: ignore
            self.color_select_button.change_color(self.color)  # type: ignore

    def on_text_changed(self):
        if self.doc_label_name_select.text().strip():
            self.ok_button.setEnabled(True)
        else:
            self.ok_button.setEnabled(False)

    def accept(self):
        if self.doc_label_name_select.text().strip():
            super().accept()  # Proceed with accepting the dialog
        else:
            pass

    def reject(self):
        super().reject()

    def get_results(self) -> DocLabel:
        results = {}
        results["name"] = self.doc_label_name_select.text()
        results["color"] = self.color
        results["label_name"] = self.label_name

        results["label_attrs"] = {}
        for attr_name, d in self.label_attrs_and_checkboxes.items():
            if d["checkbox"].check_box.isChecked():
                results["label_attrs"][attr_name] = d["value"]

        results["file_type"] = self.file_type
        results["type"] = self.label_type
        results["value_in_attrs"] = self.value_in_attrs

        return DocLabel(**results)
