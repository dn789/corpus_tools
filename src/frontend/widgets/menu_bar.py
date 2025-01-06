from pathlib import Path
from PySide6.QtWidgets import QWidget, QMenuBar, QFileDialog
from PySide6.QtGui import QAction

from frontend.project import ProjectWrapper
from frontend.styles.colors import Colors
from frontend.widgets.dialogs import (
    MessageBox,
)


class MenuBar(QMenuBar):
    def __init__(self, parent: QWidget, project: ProjectWrapper) -> None:
        super().__init__(parent)
        self.project = project
        self.setStyleSheet(f"""
            QMenuBar {{
                background-color: {Colors.dark_blue};
                color: white;
                font-size: 16px;
            }}
            QMenuBar::item {{
                padding: 5px 15px;
            }}
            QMenuBar::item:selected, QMenu::item:selected  {{
                background-color: {Colors.med_blue};
            }}
            QMenu {{
                padding: 5px;
                color: white;
                background-color: {Colors.dark_blue};
            }}
            QMenu::item:disabled {{
                color: {Colors.gray};
            }}
        """)
        file_menu = self.addMenu("Project")

        # Create actions
        self.load_action = QAction("Load Project", self)
        self.new_action = QAction("New Project", self)
        self.save_action = QAction("Save Project", self)
        self.save_as_action = QAction("Save Project As...", self)
        self.exit_action = QAction("Exit", self)

        # Connect actions
        self.load_action.triggered.connect(self.load_project)
        self.new_action.triggered.connect(self.new_project)
        self.save_action.triggered.connect(self.save_project)
        self.save_as_action.triggered.connect(self.save_project_as)
        self.exit_action.triggered.connect(parent.close)
        self.project.projectLoaded.connect(self.disable_save)
        self.project.corpusConfigUpdated.connect(self.enable_save)

        file_menu.addAction(self.load_action)
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addAction(self.exit_action)

        self.disable_save()

    def enable_save(self) -> None:
        if self.project.project_folder:
            self.save_action.setEnabled(True)

    def disable_save(self) -> None:
        self.save_action.setEnabled(False)

    def new_project(self) -> None:
        self.project.new_project()
        self.disable_save()

    def load_project(self) -> None:
        project_folder = QFileDialog.getExistingDirectory(
            self,
            "Load project",
            "",
        )
        if not project_folder:
            return
        project_folder = Path(project_folder)
        if project_folder.is_dir():
            try:
                self.project.load_project(project_folder)
                self.disable_save()
            except Exception as e:
                MessageBox.information(str(e), "Error opening folder")

    def save_project(self) -> None:
        "Currently only save_config"
        self.project.save_config()
        self.disable_save()

    def save_project_as(self) -> None:
        if self.project is None:
            MessageBox.information("No project to save", "Error")
            return

        project_folder = QFileDialog.getExistingDirectory(self, "Save Project", "")
        if not project_folder:
            return
        project_folder = Path(project_folder)
        if project_folder.is_dir():
            try:
                self.project._save_project_as(project_folder)
            except Exception as e:
                MessageBox.information(str(e), "Error saving project")

            print("Save project canceled")
