from typing import Any
from backend.corpus.features import MetaProperty, TextCategory
from backend.db.db import DatabaseManager
from backend.project.config import CorpusConfig
from backend.utils.functions import get_meta_prop_value_info


class Corpus:
    """Processed corpus class"""

    def __init__(
        self, db: DatabaseManager, config: CorpusConfig, get_features: bool = False
    ):
        self.db = db
        self.config = config
        self.db.connect()
        self.setup(get_features=get_features)

    def setup(self, get_features: bool = False) -> None:
        if get_features:
            self.get_text_categories()
            self.get_meta_properties()

    def get_text_categories(self) -> None:
        self.config.text_categories = {}
        text_labels = self.config.get_text_labels()
        for t_l in text_labels:
            self.config.text_categories[t_l.name] = TextCategory(name=t_l.name)

    def get_meta_properties(self) -> None:
        self.config.meta_properties = {}
        meta_prop_values = {}
        results = self.db.get_all_sents()
        for filename, meta_prop_refs in results["meta_properties"].items():  # type: ignore
            for meta_prop_ref in meta_prop_refs:
                name = meta_prop_ref["name"]
                value = meta_prop_ref["value"]
                if name not in self.config.meta_properties:
                    self.add_meta_prop(meta_prop_ref)
                meta_prop_values.setdefault(name, set())
                meta_prop_values[name].add(value)

        for name, values in meta_prop_values.items():
            meta_prop_value_info = get_meta_prop_value_info(values)
            meta_prop = self.config.meta_properties[name]
            meta_prop.type = meta_prop_value_info["meta_type"]
            meta_prop.min = meta_prop_value_info["min"]
            meta_prop.max = meta_prop_value_info["max"]
            meta_prop.cat_values = meta_prop_value_info["cat_values"]

    def add_meta_prop(self, meta_prop_ref: dict[str, Any]) -> None:
        name = meta_prop_ref["name"]
        meta_label = self.config.meta_labels.get(name.split(".")[0])

        if meta_label:
            label_name = meta_label.name
            meta_type = meta_label.meta_type
        else:
            label_name = None
            meta_type = None

        self.config.meta_properties[meta_prop_ref["name"]] = MetaProperty(
            name=name,
            label_name=label_name,
            type=meta_type,  # type: ignore
        )
