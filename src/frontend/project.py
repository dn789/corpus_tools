from pathlib import Path
from PySide6.QtCore import Signal, qDebug
from PySide6.QtWidgets import QWidget

from backend.project.project import Project
from backend.corpus.items import CorpusItem, GenericCorpusItem
from frontend.styles.colors import random_color_rgb


class ProjectWrapper(Project, QWidget):
    projectLoaded = Signal()
    projectSaved = Signal()
    configSaved = Signal()
    corpusConfigUpdated = Signal(str, object, bool)

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
        content: CorpusItem | list[CorpusItem] | str | list[str] | Path,
        remove: bool = False,
    ) -> None:
        if not remove:
            content = self.make_corpus_item(prop_name, content)  # type: ignore

        kwargs = {"prop_name": prop_name, "content": content, "remove": remove}
        self._update_corpus_items(**kwargs)
        self.corpusConfigUpdated.emit(prop_name, content, remove)

    def make_corpus_item(
        self, prop_name: str, content: str | list[str]
    ) -> list[CorpusItem]:
        content = [content] if type(content) is str else content
        items = []
        for item in content:
            if prop_name == "included_extensions":
                item = GenericCorpusItem(name=item, color=random_color_rgb())  # type: ignore
            items.append(item)
        return items
