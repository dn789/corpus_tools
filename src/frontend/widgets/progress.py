from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from frontend.widgets.small import Button


class ProgressBackend(QWidget):
    increment = Signal()
    taskInfo = Signal(str, int)
    complete = Signal()

    def __init__(self) -> None:
        super().__init__()


class ProgressWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet("""
            font-size: 20px;

        """)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bar_layout = QHBoxLayout()
        self.setLayout(main_layout)

        self.message = QLabel("Message...")
        main_layout.addWidget(self.message)
        main_layout.addLayout(bar_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        bar_layout.addWidget(self.progress_bar)

        self.cancel_button = Button("Cancel")
        main_layout.addWidget(self.cancel_button)

        self.counter = QLabel("0/0")
        bar_layout.addWidget(self.counter)

    def load_task(self, message: str, total_count: int) -> None:
        self.progress_bar.setValue(0)
        self.message.setText(message)
        if total_count:
            self.progress_bar.setMaximum(total_count)
            self.counter.setText(f"0/{total_count}")
        else:
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(0)

    def increment(self) -> None:
        current_count = self.progress_bar.value() + 1
        self.progress_bar.setValue(current_count)
        self.counter.setText(f"{current_count}/{self.progress_bar.maximum()}")

    def complete(self) -> None:
        self.cancel_button.hide()
