from enum import Enum
from pathlib import Path
from typing import Any, Optional

from frozendict import frozendict
from pydantic import BaseModel, model_validator


# General types


class GenericCorpusItem(BaseModel):
    name: str
    color: tuple[int, int, int]


class MetaType(str, Enum):
    QUANTITATIVE = "QUANTITATIVE"
    CATEGORICAL = "CATEGORICAL"


class Folder(BaseModel):
    color: tuple[int, int, int]
    path: Path
    name: Optional[str] = None

    @model_validator(mode="after")
    def set_display_name(cls, values):
        values.name = values.path.name
        return values


# Config types


class LabelType(str, Enum):
    TEXT = "TEXT"
    META = "META"


class DocLabel(BaseModel):
    name: str
    color: tuple[int, int, int]
    label_name: str
    label_attrs: dict[str, str]
    file_type: str
    type: LabelType
    meta_type: Optional[MetaType] = None
    value_in_attrs: bool = False

    def escape_xml(self, text):
        return text.replace("<", "&lt;").replace(">", "&gt;")

    def get_tooltip(self):
        if self.file_type == ".json":
            return f"Key <b>{self.label_name}</b> in <b>JSON</b> files"
        if self.file_type == ".xml":
            label_attrs = " ".join(
                f"<i>{k}</i>=<b>{v}</b>" for k, v in self.label_attrs.items()
            )
            label_attrs = f" {label_attrs}"
            value_in_attrs_str = ""
            if self.type is LabelType.META:
                value_in_attrs_str = "(Values in {})"
                if self.value_in_attrs:
                    value_in_attrs_str = value_in_attrs_str.format("attributes")
                else:
                    value_in_attrs_str = value_in_attrs_str.format("text content")
            return f"&lt;<b>{self.label_name}</b>{label_attrs}&gt; in <b>XML</b> files {value_in_attrs_str}"

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


# Processed corpus types


class TextCategory(BaseModel):
    # Same as corresponding DocLabel
    name: str
    color: tuple[int, int, int]


class MetaProperty(BaseModel):
    # name or name[0] same as corresponding DocLabel
    name: str
    label_name: str
    color: tuple[int, int, int]
    display_name: Optional[str] = None
    type: Optional[MetaType] = None
    # For QUANTITATIVE types
    min: Any = 0
    max: Any = 0
    # For categorical types
    cat_values: Optional[set[str]] = None

    @model_validator(mode="after")
    def set_display_name(cls, values):
        if not values.display_name:
            values.display_name = values.name
        return values


CorpusItem = Folder | DocLabel | TextCategory | MetaProperty | GenericCorpusItem
