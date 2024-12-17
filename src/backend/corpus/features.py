from enum import Enum
from pathlib import Path
from typing import Any, Optional

from frozendict import frozendict
from pydantic import BaseModel, model_validator


# General types


class MetaType(str, Enum):
    NUMERICAL = "NUMERICAL"
    CATEGORICAL = "CATEGORICAL"


class Folder(BaseModel):
    color: str
    path: Path
    display_name: Optional[str] = None

    @model_validator(mode="after")
    def set_display_name(cls, values):
        values.display_name = values.path.name
        return values


# Config types


class LabelType(str, Enum):
    TEXT = "TEXT"
    META = "META"


class DocLabel(BaseModel):
    name: str
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


# Processed corpus types


class TextCategory(BaseModel):
    # Same name as corresponding DocLabel
    name: str


class MetaProperty(BaseModel):
    name: str
    label_name: Optional[str] = None
    type: Optional[MetaType] = None
    # For numerical types
    min: Any = 0
    max: Any = 0
    # For categorical types
    cat_values: Optional[set[str]] = None
