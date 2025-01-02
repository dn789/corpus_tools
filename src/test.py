from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget


class Test(QWidget):
    increment = Signal()

    def __init__(self) -> None:
        super().__init__()
