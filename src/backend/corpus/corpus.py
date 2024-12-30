from backend.corpus.items import MetaProperty, TextCategory
from backend.db.db import DatabaseManager
from backend.project.config import CorpusConfig


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

    def get_text_categories(self) -> None:
        self.config.text_categories = {}
        text_labels = self.config.get_text_labels()
        for t_l in text_labels:
            self.config.text_categories[t_l.name] = TextCategory(
                name=t_l.name, color=t_l.color
            )
