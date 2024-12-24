import json
from pathlib import Path
import shutil

from backend.corpus.corpus import Corpus
from backend.db.db import DatabaseManager
from backend.corpus.process.process_corpus import CorpusProcessor
from backend.project.config import Config
from backend.corpus.items import CorpusItem


class Paths:
    def __init__(self, project_folder: Path):
        self.project_folder = project_folder
        self.corpus_db = project_folder / "corpus.db"


class Project:
    def __init__(
        self,
        default_config_path: Path,
        project_folder: Path | None = None,
    ) -> None:
        self.default_config_path = default_config_path
        self.project_folder = project_folder
        self.config_path = None
        if self.project_folder:
            self._load_project()
        else:
            self._new_project()

    def _load_config(self) -> None:
        if not self.config_path:
            raise ValueError("No config path provided.")
        with self.config_path.open() as f:
            config_d = json.load(f)
        self.config = Config.model_validate(config_d)
        self.corpus_config = self.config.corpus_config

    def _new_project(self) -> None:
        self.project_folder = None
        self.config_path = self.default_config_path
        self._load_config()

    def _load_project(self, project_folder: Path | None = None) -> None:
        """
        Makes project folder if it doesn't exist.
        """
        self.project_folder = project_folder or self.project_folder
        if not self.project_folder:
            raise ValueError("No project folder provided")

        self.paths = Paths(self.project_folder)
        self.config_path = self.project_folder / "config.json"

        if not self.project_folder.is_dir():
            self.project_folder.mkdir()
            shutil.copy(self.default_config_path, self.config_path)

        self._load_config()

    def _save_config(self) -> None:
        if not self.config or not self.config_path:
            raise ValueError("No config or config path provided.")
        self.config.save(self.config_path)

    def _update_corpus_items(
        self,
        prop_name: str,
        content: CorpusItem | list[CorpusItem] | str | list[str] | Path,  # type: ignore
        remove: bool = False,
    ) -> None:
        self.corpus_config.update_corpus_items(prop_name, content, remove)  # type: ignore

    def _save_project_as(self, project_folder: Path) -> None:
        self.project_folder = project_folder
        self.paths = Paths(self.project_folder)
        self.config_path = self.project_folder / "config.json"
        self._save_config()

    def load_db_manager(self, new_db: bool = False):
        self.db = DatabaseManager(self.paths.corpus_db)
        if new_db:
            self.db.setup()
        else:
            self.db.connect()

    def load_corpus_processor(self, new_db: bool = False) -> None:
        self.load_db_manager(new_db=new_db)
        if not self.corpus_config:
            raise ValueError("No corpus config provided")
        self.corpus_processor = CorpusProcessor(self.corpus_config, self.db)  # type: ignore

    def process_corpus(self, add_embeddings: bool = True) -> None:
        self.load_corpus_processor(new_db=True)
        self.corpus_processor.process_files(add_embeddings=add_embeddings)  # type: ignore
        if not self.corpus_config:
            raise ValueError("No corpus config provided")
        self.corpus = Corpus(self.db, self.corpus_config, get_features=True)  # type: ignore
