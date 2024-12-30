from pathlib import Path
from typing import Any

from tqdm import tqdm

from backend.corpus.items import MetaType
from backend.db.db import DatabaseManager
from backend.corpus.process.process_cha import process_cha_file
from backend.project.config import CorpusConfig
from backend.corpus.process.process_doc import (
    file_to_doc,
    get_doc_level_meta_props,
    get_sents_from_doc,
)
from backend.nlp_models.semantic import SemanticModel
from backend.utils.functions import is_quant
from backend.utils.nlp import SentTokenizer


class CorpusProcessor:
    """
    Processes corpus, creating a database of all sentences, their embeddings,
    associated text, meta categories, and subfolders.
    """

    def __init__(self, config: CorpusConfig, db: DatabaseManager) -> None:
        self.config = config
        self.db = db
        self.corpus_path = config.corpus_path
        self.included_extensions = config.included_extensions
        self.ignored_extensions = config.ignored_extensions
        self.subfolders = config.subfolders
        self.text_categories = config.text_labels
        self.meta_categories = config.meta_labels

        if not self.corpus_path:
            raise ValueError("No corpus path specified.")

        if self.included_extensions:

            def file_ext_filter(f):
                return f.suffix in self.included_extensions
        elif self.ignored_extensions:

            def file_ext_filter(f):
                return f.suffix not in self.included_extensions
        else:
            raise ValueError("Must specify either included or ignored extensions.")
        self.file_ext_filter = file_ext_filter

        self.sent_tokenizer = SentTokenizer()

    def process_files(
        self, add_embeddings: bool = True, frontend_connect: Any = None
    ) -> None:
        files = list(self.corpus_path.rglob("*"))  # type: ignore
        if frontend_connect:
            frontend_connect.taskInfo.emit("Processing files", len(files))
        for f in tqdm(files, desc="Processing files"):
            if f.is_file() and self.file_ext_filter(f):
                self.process_file(f)
            if frontend_connect:
                frontend_connect.increment.emit()

        if add_embeddings:
            self.add_embeddings()

        self.set_meta_prop_value_attrs()
        self.db.close()

    def process_file(self, file_path: Path) -> None:
        file_type = file_path.suffix

        if file_type == ".cha":
            file_d = process_cha_file(file_path)
        else:
            doc = file_to_doc(file_path)
            try:
                sent_dicts = get_sents_from_doc(
                    doc,
                    self.config.get_text_labels(file_type=file_type),
                    self.sent_tokenizer,
                )
                meta_prop_refs = get_doc_level_meta_props(
                    doc, self.config.get_meta_labels(file_type=file_type)
                )

            except ValueError as e:
                raise ValueError(f"{str(e)} {file_path}")

            file_d = {
                "sent_dicts": sent_dicts,
                "file_path": file_path,
                "meta_properties": meta_prop_refs,
            }

        for meta_prop_ref in file_d["meta_properties"]:
            label_name = meta_prop_ref["label_name"]
            name = meta_prop_ref["name"]
            if not self.config.meta_properties.get(label_name, {}).get(name):
                self.config.add_meta_property(meta_prop_ref)

        if file_d.get("error"):
            # Log errors here.
            pass
        else:
            file_d["subfolders"] = self.config.get_subfolder_names_for_path(file_path)
            self.db.insert_file_entry(file_d)

    def add_embeddings(self):
        s_model = SemanticModel()
        sents = self.db.get_all_sents(sents_only=True)
        s_model.encode_sents(sents)  # type: ignore
        self.db.add_embeddings(s_model.sent_embeds)  # type: ignore

    def get_meta_prop_value_info(self, values: list[Any]) -> dict[str, Any]:
        """
        Returns a dict of {
            "meta_type" : MetaType.QUANTITATIVE or MetaType.CATEGORICAL,
            "min": minimum value (if QUANTITATIVE) or None,
            "max": maximum value (if QUANTITATIVE) or None,
            "cat_values": all values (if categorical) or None
        }

        """
        if any(not isinstance(value, (int, float, str)) for value in values):
            raise ValueError("Incompatible Meta property value")

        quant_count = len([value for value in values if is_quant(value)])
        if quant_count / len(values) > 0.75:
            meta_type = MetaType.QUANTITATIVE
        else:
            meta_type = MetaType.CATEGORICAL

        if meta_type == MetaType.QUANTITATIVE:
            min_, max_ = min(values), max(values)
            cat_values = None

        else:
            min_, max_ = None, None
            cat_values = values

        return {
            "meta_type": meta_type,
            "min": min_,
            "max": max_,
            "cat_values": cat_values,
        }

    def set_meta_prop_value_attrs(self) -> None:
        meta_prop_values = {}
        results = self.db.get_all_sents()
        for filename, meta_prop_refs in results["meta_properties"].items():  # type: ignore
            for meta_prop_ref in meta_prop_refs:
                label_name = meta_prop_ref["label_name"]
                name = meta_prop_ref["name"]
                value = meta_prop_ref["value"]
                meta_prop_values.setdefault((label_name, name), set())
                meta_prop_values[(label_name, name)].add(value)

        for (label_name, name), values in meta_prop_values.items():
            value_info = self.get_meta_prop_value_info(values)
            meta_prop = self.config.meta_properties[label_name][name]
            if meta_prop.type != value_info["meta_type"]:
                # Handle discrepancy here, for now just overrwite meta_type
                pass
            meta_prop.type = value_info["meta_type"]
            meta_prop.min = value_info["min"]
            meta_prop.max = value_info["max"]
            meta_prop.cat_values = value_info["cat_values"]
