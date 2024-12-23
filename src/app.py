import sys

from PySide6.QtWidgets import QApplication
from frontend.main import MainWindow
from frontend.startup import load_project


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow(load_project())
    window.show()
    sys.exit(app.exec())
