from pathlib import Path
from typing import Any
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from backend.project.project import Project


class ProjectWrapper(Project, QWidget):
    """Wrapper for Project class (for signalling)"""

    projectLoaded = Signal()
    projectSaved = Signal()
    configSaved = Signal()
    corpusConfigUpdated = Signal(str, object, bool)
    corpusProcessed = Signal()

    def __init__(
        self, default_config_path: Path, project_folder: Path | None = None
    ) -> None:
        Project.__init__(self, default_config_path, project_folder)
        QWidget.__init__(self)

    def new_project(self) -> None:
        self._new_project()
        self.projectLoaded.emit()

    def load_project(self, project_folder: Path | None = None) -> None:
        self._load_project(project_folder)
        self.projectLoaded.emit()

    def save_config(self) -> None:
        self._save_config()
        self.configSaved.emit()

    def save_project_as(self, project_folder: Path) -> None:
        self._save_project_as(project_folder)
        self.projectSaved.emit()

    def update_corpus_items(
        self,
        prop_name: str,
        content: Any | list[Any],
        remove: bool = False,
    ) -> None:
        kwargs = {"prop_name": prop_name, "content": content, "remove": remove}
        self._update_corpus_items(**kwargs)
        self.corpusConfigUpdated.emit(prop_name, content, remove)
