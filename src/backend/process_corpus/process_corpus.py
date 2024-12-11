from pathlib import Path

from tqdm import tqdm
import pandas as pd

from backend.project.types import Config
from backend.process_corpus.process_doc import (
    file_to_doc,
    get_doc_level_meta_values,
    get_sents_from_doc,
)
from backend.utils.nlp import SentTokenizer


class CorpusProcessor:
    """
    Processes corpus, creating a database of all sentences, their embeddings,
    associated text, meta categories, and subfolders.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
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

    def process_files(self) -> None:
        self.df_rows = []
        for f in tqdm(list(self.corpus_path.rglob("*")), desc="Processing files"):  # type: ignore
            if f.is_file() and self.file_ext_filter(f):
                self.process_file(f)
        df = pd.DataFrame(self.df_rows)
        self.df = df

    def process_file(self, file_path: Path) -> None:
        doc = file_to_doc(file_path)
        suffix = file_path.suffix

        try:
            sent_dicts = get_sents_from_doc(
                doc, self.config.get_text_labels(file_type=suffix), self.sent_tokenizer
            )
            doc_level_meta_values = get_doc_level_meta_values(
                doc, self.config.get_meta_labels(file_type=suffix)
            )
        except ValueError as e:
            raise ValueError(f"{str(e)} {file_path}")

        for sent_d in sent_dicts:
            sent_d["filename"] = file_path  # type: ignore
            sent_d["meta_properties"] = doc_level_meta_values  # type: ignore
            self.df_rows.append(sent_d)
