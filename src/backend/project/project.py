import json
from pathlib import Path
import shutil

from backend.corpus.corpus import Corpus
from backend.db.db import DatabaseManager
from backend.corpus.process.process_corpus import CorpusProcessor
from backend.project.config import Config


class Paths:
    def __init__(self, project_folder: Path):
        self.project_folder = project_folder
        self.corpus_db = project_folder / "corpus.db"


class Project:
    def __init__(
        self,
        default_config_path: Path,
        project_folder: Path,
    ) -> None:
        self.default_config_path = default_config_path
        self.project_folder = project_folder
        self.paths = Paths(self.project_folder)
        self.load_project()

    def load_project(self) -> None:
        """
        Makes project folder if it doesn't exist.
        """
        self.config_path = self.project_folder / "config.json"

        if not self.project_folder.is_dir():
            self.project_folder.mkdir()
            shutil.copy(self.default_config_path, self.config_path)

        config_d = json.load(self.config_path.open())
        self.config = Config.model_validate(config_d)
        self.corpus_config = self.config.corpus_config

    def save_config(self) -> None:
        self.config.save(self.config_path)

    def load_db_manager(self, new_db: bool = False):
        self.db = DatabaseManager(self.paths.corpus_db)
        if new_db:
            self.db.setup()
        else:
            self.db.connect()

    def load_corpus_processor(self, new_db: bool = False):
        self.load_db_manager(new_db=new_db)
        self.corpus_processor = CorpusProcessor(self.corpus_config, self.db)

    def process_corpus(self, add_embeddings: bool = True) -> None:
        self.load_corpus_processor(new_db=True)
        self.corpus_processor.process_files(add_embeddings=add_embeddings)
        self.corpus = Corpus(self.db, self.corpus_config, get_features=True)
