from pathlib import Path

import json

from backend.process_corpus.process_corpus import CorpusProcessor
from backend.project.types import Config, DocLabel, LabelType


class Project:
    def __init__(
        self,
        default_config_path: Path,
        project_path: Path | None = None,
    ) -> None:
        self.default_config_path = default_config_path
        self.project_path = project_path
        self.load_project()

    def load_project(self) -> None:
        """
        Get settings from project file if it exists, otherwise from default
        settings file.
        """
        if self.project_path:
            project_dict = json.load(self.project_path.open())
            settings_dict = project_dict.get("config")
        else:
            settings_dict = json.load(self.default_config_path.open())

        self.config = Config.model_validate(settings_dict)

    def save_project(self) -> None:
        if not self.project_path:
            raise ValueError("No project path specified.")

        # Nothing else in project_dict atm
        project_dict = {}
        project_dict["settings"] = self.config.to_dict()
        json.dump(project_dict, self.project_path.open("w"))

    def get_text_labels(self, file_type: str | None = None) -> list[DocLabel]:
        text_labels = list(self.config.text_labels.values())
        if file_type:
            text_labels = [
                label for label in text_labels if label.file_type == file_type
            ]
        return text_labels

    def get_meta_labels(self, file_type: str | None = None) -> list[DocLabel]:
        meta_labels = list(self.config.meta_labels.values())
        if file_type:
            meta_labels = [
                label for label in meta_labels if label.file_type == file_type
            ]
        return meta_labels

    def get_doc_label(self, label_name: str, label_type: LabelType) -> DocLabel:
        """label_name is DocLabel.name attribute"""
        return self.config.label_type_dict[label_type][label_name]

    def process_corpus(self):
        self.corpus_processor = CorpusProcessor(self.config)
        self.corpus_processor.process_files()
