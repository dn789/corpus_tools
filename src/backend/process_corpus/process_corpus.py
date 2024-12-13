from pathlib import Path

from tqdm import tqdm

from backend.db.db import DatabaseManager
from backend.project.config import CorpusConfig
from backend.process_corpus.process_doc import (
    file_to_doc,
    get_doc_level_meta_values,
    get_sents_from_doc,
)
from backend.nlp_models.semantic import SemanticModel
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

    def process_files(self) -> None:
        # Process corpus
        self.file_dicts = []
        for f in tqdm(list(self.corpus_path.rglob("*")), desc="Processing files"):  # type: ignore
            if f.is_file() and self.file_ext_filter(f):
                self.process_file(f)
        # Add to database
        self.db.setup()
        for fd in self.file_dicts:
            self.db.insert_file(fd)
        # Add sentence embeddings
        s_model = SemanticModel()
        sents = self.db.get_all_sents(sents_only=True)
        s_model.encode_sents(sents)  # type: ignore
        self.db.add_embeddings(s_model.sent_embeds)  # type: ignore

        self.db.close()

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

        # Initialize embeddings to zero
        for sd in sent_dicts:
            sd["embedding"] = None  # type: ignore
        file_d = {
            "sent_dicts": sent_dicts,
            "file_path": file_path,
            "meta_properties": doc_level_meta_values,
        }
        self.file_dicts.append(file_d)
