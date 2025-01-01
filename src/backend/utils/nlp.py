import spacy


class SpacyModel:
    def __init__(self) -> None:
        self.nlp = spacy.load("en_core_web_sm")

    def sent_tokenize(self, text: str) -> list[str]:
        doc = self.nlp(text)
        return [sent.text for sent in doc.sents]

    def word_tokenize(self, sentence: str) -> list[str]:
        doc = self.nlp(sentence)
        return [token.text for token in doc if token.is_alpha]

    def word_count(self, sentence: str) -> int:
        return len(self.word_tokenize(sentence))
