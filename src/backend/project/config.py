from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field

from backend.corpus.features import (
    DocLabel,
    Folder,
    LabelType,
    MetaProperty,
    TextCategory,
)


class CorpusConfig(BaseSettings):
    corpus_path: Optional[Path] = None
    included_extensions: set[str] = Field(default_factory=set)
    ignored_extensions: set[str] = Field(default_factory=set)
    subfolders: dict[str, Folder] = Field(default_factory=dict)
    text_labels: dict[str, DocLabel] = Field(default_factory=dict)
    meta_labels: dict[str, DocLabel] = Field(default_factory=dict)
    text_categories: dict[str, TextCategory] = Field(default_factory=dict)
    meta_properties: dict[str, MetaProperty] = Field(default_factory=dict)

    @property
    def label_type_dict(self) -> dict:
        return {
            LabelType.TEXT: self.text_labels,
            LabelType.META: self.meta_labels,
        }

    def get_doc_label(self, label_name: str, label_type: LabelType) -> DocLabel:
        """label_name is DocLabel.name attribute"""
        return self.label_type_dict[label_type][label_name]

    def get_text_labels(self, file_type: str | None = None) -> list[DocLabel]:
        text_labels = list(self.text_labels.values())
        if file_type:
            text_labels = [
                label for label in text_labels if label.file_type == file_type
            ]
        return text_labels

    def get_meta_labels(self, file_type: str | None = None) -> list[DocLabel]:
        meta_labels = list(self.meta_labels.values())
        if file_type:
            meta_labels = [
                label for label in meta_labels if label.file_type == file_type
            ]
        return meta_labels

    def get_subfolder_names_for_path(self, path: Path) -> list[str]:
        subfolder_names = []
        for folder in self.subfolders.values():
            if folder.path in path.parents:
                subfolder_names.append(folder.display_name)
        return subfolder_names


class Config(BaseSettings):
    corpus_config: CorpusConfig

    def save(self, path: Path) -> None:
        path.open("w").write(self.model_dump_json())
