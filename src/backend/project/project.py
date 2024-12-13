import json
from pathlib import Path

import shutil

from backend.db.db import DatabaseManager
from backend.process_corpus.process_corpus import CorpusProcessor
from backend.project.config import Config, DocLabel, LabelType


class Project:
    def __init__(
        self,
        default_config_path: Path,
        project_folder: Path,
    ) -> None:
        self.default_config_path = default_config_path
        self.project_folder = project_folder
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
        config_d["paths"]["project_folder"] = self.project_folder
        self.config = Config.model_validate(config_d)
        self.corpus_config = self.config.corpus_config

    def save_config(self) -> None:
        self.config.save(self.config_path)

    def get_text_labels(self, file_type: str | None = None) -> list[DocLabel]:
        text_labels = list(self.corpus_config.text_labels.values())
        if file_type:
            text_labels = [
                label for label in text_labels if label.file_type == file_type
            ]
        return text_labels

    def get_meta_labels(self, file_type: str | None = None) -> list[DocLabel]:
        meta_labels = list(self.corpus_config.meta_labels.values())
        if file_type:
            meta_labels = [
                label for label in meta_labels if label.file_type == file_type
            ]
        return meta_labels

    def get_doc_label(self, label_name: str, label_type: LabelType) -> DocLabel:
        """label_name is DocLabel.name attribute"""
        return self.corpus_config.label_type_dict[label_type][label_name]

    def process_corpus(self) -> None:
        self.db = DatabaseManager(self.config.paths.corpus_db)
        self.corpus_processor = CorpusProcessor(self.corpus_config, self.db)
        self.corpus_processor.process_files()
