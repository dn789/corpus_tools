from typing import Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from backend.corpus.items import LabelType
from frontend.styles.colors import ColorSelectButton, random_color_rgb
from frontend.widgets.small import Button


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
    def __init__(self, key: Any, display_name: str, label_type: LabelType) -> None:
        super().__init__()
        self.setWindowTitle(f"Add to {label_type.name.lower()} labels")
        self.setFixedSize(400, 100)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        self.setLayout(layout)
        self.setStyleSheet("font-size: 18px;")

        line_and_color_layout = QHBoxLayout()
        line_and_color_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        line_and_color_layout.setSpacing(5)
        line_and_color_layout.addWidget(QLabel("Name"))

        self.label_name_select = QLineEdit(self)
        self.label_name_select.textChanged.connect(self.on_text_changed)
        self.label_name_select.setText(display_name)
        line_and_color_layout.addWidget(self.label_name_select)

        self.color = random_color_rgb()
        self.color_select_button = ColorSelectButton(self.color)  # type: ignore
        self.color_select_button.clicked.connect(self.select_color)
        line_and_color_layout.addWidget(self.color_select_button)
        layout.addLayout(line_and_color_layout)

        self.ok_button = Button("OK", self.accept)
        cancel_button = Button("Cancel", self.reject)
        button_layout = QHBoxLayout()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)

    def select_color(self):
        # Open the color dialog and get the selected color
        new_color = QColorDialog().getColor()

        # Check if the color is valid (not cancelled)
        if new_color.isValid():
            self.color = new_color
            self.color_select_button.change_color(self.color)

    def on_text_changed(self):
        if self.label_name_select.text().strip():
            self.ok_button.setEnabled(True)
        else:
            self.ok_button.setEnabled(False)

    def accept(self):
        # Proceed with the accept behavior if the input is valid (non-empty)
        if self.label_name_select.text().strip():
            super().accept()  # Proceed with accepting the dialog
        else:
            # If it's still empty, we won't accept
            pass

    def reject(self):
        super().reject()

    # def get_results(self) -> dict[str, str]:
    #     if type(self.color) is QColor:
    #         self.color = self.color.name()
    #     results = {"color": self.color, "name": self.label_name_select.text()}
    #     if self.meta:
    #         if self.radio_meta_type_text.isChecked():
    #             results["meta_type"] = "text"
    #         else:
    #             results["meta_type"] = "numerical"
    #     return results
