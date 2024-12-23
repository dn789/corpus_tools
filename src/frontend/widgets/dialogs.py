from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout, QWidget

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
