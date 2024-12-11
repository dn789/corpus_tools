import spacy


class SentTokenizer:
    def __init__(self) -> None:
        self.nlp = spacy.load("en_core_web_sm")

    def sent_tokenize(self, text: str) -> list[str]:
        doc = self.nlp(text)
        return [sent.text for sent in doc.sents]
