from enum import Enum
from pathlib import Path
from typing import Optional

from frozendict import frozendict
from pydantic_settings import BaseSettings
from pydantic import Field, BaseModel, model_validator


class MetaType(str, Enum):
    NUMERICAL = "NUMERICAL"
    CATEGORICAL = "CATEGORICAL"


class LabelType(str, Enum):
    TEXT = "TEXT"
    META = "META"


class DocLabel(BaseModel):
    name: str
    display_name: str
    color: str
    label_name: str
    label_attrs: dict[str, str]
    file_type: str
    type: LabelType
    meta_type: Optional[MetaType] = None
    value_in_attrs: bool = False

    def match_label(self, label: str | int | bool | frozendict) -> bool:
        """Checks if self matches label

        For (str | int | bool ), returns self.label_name==label (matching from
            JSON files).

        For frozendict, checks if self.name matches frozendict['_tag'] and all
            self.label_attrs are present with same value in label (extra label
            values are okay)


        Args:
            label (str | int | bool| frozendict): Dictionary key (frozendict
                if parsed from XML doc)

        Returns:
            bool: Whether or not theere's a match
        """
        if isinstance(label, (str | int | bool)):
            return self.label_name == label
        else:
            if not self.label_name == label["_tag"]:
                return False
            for attr, value in self.label_attrs.items():
                if attr not in label or not label[attr] == value:
                    return False
            return True


class Folder(BaseModel):
    color: str
    value: Path
    display_name: Optional[str] = None

    @model_validator(mode="before")
    def set_display_name(cls, values):
        values["display_name"] = values["value"].name
        return values


class Paths(BaseModel):
    project_folder: Path
    corpus_db: Path

    @model_validator(mode="before")
    def resolve_paths(cls, values):
        for k, v in values.items():
            if k != "project_folder":
                values[k] = values["project_folder"] / v
        return values


class CorpusConfig(BaseSettings):
    corpus_path: Optional[Path] = None
    included_extensions: set[str] = Field(default_factory=set)
    ignored_extensions: set[str] = Field(default_factory=set)
    subfolders: dict[str, Folder] = Field(default_factory=dict)
    text_labels: dict[str, DocLabel] = Field(default_factory=dict)
    meta_labels: dict[str, DocLabel] = Field(default_factory=dict)

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


class Config(BaseSettings):
    paths: Paths
    corpus_config: CorpusConfig

    def save(self, path: Path) -> None:
        path.open("w").write(self.model_dump_json())
