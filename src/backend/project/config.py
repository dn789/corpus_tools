from pathlib import Path
from typing import Any, ClassVar, Optional

from PySide6.QtCore import qDebug
from pydantic_settings import BaseSettings
from pydantic import Field

from backend.corpus.items import (
    GenericCorpusItem,
    DocLabel,
    Folder,
    LabelType,
    MetaProperty,
    MetaType,
    TextCategory,
    CorpusItem,
)
from backend.utils.functions import is_quant
from frontend.styles.colors import random_color_rgb


class CorpusConfig(BaseSettings):
    """Corpus configuration"""

    # Corpus summary info
    summary: dict[str, Any]
    # Path to corpus foldere
    corpus_path: Optional[Path] = None
    # Extensions of files to be included in the analysis
    included_extensions: dict[str, GenericCorpusItem] = Field(default_factory=dict)
    # Not used for now
    ignored_extensions: set[str] = Field(default_factory=set)
    # Subfolders to be analyzed individually
    subfolders: dict[Path, Folder] = Field(default_factory=dict)
    # Document identifiers for text data
    text_labels: dict[str, DocLabel] = Field(default_factory=dict)
    # Document identifiers for meta data
    meta_labels: dict[str, DocLabel] = Field(default_factory=dict)
    # Objects representing text categories corresponding to text labels
    text_categories: dict[str, TextCategory] = Field(default_factory=dict)
    # Objects representing meta properties corresponding to meta labels.
    # Meta labels in HTML/XML files with attribute values can have multiple
    # child meta properties.
    meta_properties: dict[str, dict[str, MetaProperty]] = Field(default_factory=dict)

    display_ref: ClassVar = {
        "corpus_path": "Corpus path",
        "included_extensions": "Content file extensions",
        "subfolders": "Subfolders",
        "text_labels": "Text labels",
        "meta_labels": "Meta labels",
        "text_categories": "Text categories",
        "meta_properties": "Meta properties",
    }

    def get_display_name(self, field_name: str) -> str:
        return self.display_ref[field_name]

    @property
    def label_type_dict(self) -> dict:
        return {
            LabelType.TEXT: self.text_labels,
            LabelType.META: self.meta_labels,
        }

    def get_item_key(self, corpus_item: CorpusItem) -> Any:
        if type(corpus_item) is Folder:
            return corpus_item.path
        else:
            return corpus_item.name

    def get_doc_label(self, label_name: str, label_type: LabelType) -> DocLabel:
        """label_name is DocLabel.name attribute"""
        return self.label_type_dict[label_type][label_name]

    def get_extensions(self) -> list[GenericCorpusItem]:
        return [ext for name, ext in self.included_extensions.items()]

    def get_subfolders(self) -> list[Folder]:
        return list(self.subfolders.values())

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

    def get_meta_properties(
        self, as_dict: bool = False
    ) -> list[MetaProperty] | dict[tuple[str, str], MetaProperty]:
        meta_props = {} if as_dict else []
        for label, d in self.meta_properties.items():
            for meta_prop in d.values():
                if as_dict:
                    meta_props[(label, meta_prop.name)] = meta_prop  # type: ignore
                else:
                    meta_props.append(meta_prop)  # type: ignore
        return meta_props

    def get_subfolder_names_for_path(self, path: Path) -> list[str]:
        subfolder_names = []
        for folder in self.subfolders.values():
            if folder.path in path.parents:
                subfolder_names.append(folder.name)
        return subfolder_names

    def add_meta_property(self, meta_pro_ref: dict[str, Any]):
        label_name = meta_pro_ref["label_name"]
        name = meta_pro_ref["name"]
        value = meta_pro_ref["value"]
        if self.meta_labels.get(label_name):
            color = self.meta_labels[label_name].color
        else:
            color = random_color_rgb()
        meta_type = MetaType.QUANTITATIVE if is_quant(value) else MetaType.CATEGORICAL
        self.meta_properties.setdefault(label_name, {})
        self.meta_properties[label_name][name] = MetaProperty(
            name=name,
            label_name=label_name,
            type=meta_type,  # type: ignore
            color=color,  # type: ignore
        )

    def update_corpus_items(
        self,
        prop_name: str,
        content: CorpusItem | list[CorpusItem] | str | list[str],
        remove: bool = False,
    ) -> None:
        if prop_name == "corpus_path":
            self.corpus_path = content  # type: ignore
            return
        content = content if type(content) is list else [content]  # type: ignore
        if remove:
            for key in content:
                getattr(self, prop_name).pop(key)
        else:
            for corpus_item in content:
                getattr(self, prop_name)[self.get_item_key(corpus_item)] = corpus_item  # type: ignore


class Config(BaseSettings):
    """Main config. Mostly just corpus config for now."""

    status: dict[str, Any]
    corpus_config: CorpusConfig

    def save(self, path: Path) -> None:
        path.open("w").write(self.model_dump_json())
