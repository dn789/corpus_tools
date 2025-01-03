import spacy
from collections import Counter
from typing import Any, Iterable
from nltk import ngrams, word_tokenize
from nltk.corpus import stopwords


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


# N-Grams


def get_n_grams_from_sentence(sentence, n=2):
    tokens = word_tokenize(sentence)
    return list(ngrams(tokens, n))


def get_n_grams_from_corpus(
    sent_dicts: list[dict[str, Any]],
    n=2,
    ignore_stopword_pairs=True,
    frontend_connect: Any | None = None,
) -> list[tuple[str, int]]:
    if ignore_stopword_pairs:
        stop_words = set(stopwords.words("english"))
    n_grams = Counter()
    for sent_d in sent_dicts:
        sent_n_grams = get_n_grams_from_sentence(sent_d["sentence"], n=n)
        for n_gram in sent_n_grams:
            if ignore_stopword_pairs and stop_words.issuperset(
                [x.lower() for x in n_gram]
            ):
                continue
            n_gram = " ".join(n_gram)
            n_grams[n_gram] += 1

    return n_grams.most_common(1000)
