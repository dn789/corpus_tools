from collections import Counter
from typing import Any

from numpy import ndarray, array
from sentence_transformers import SentenceTransformer, util


class SemanticModel:
    """Sbert model class for semantic search."""

    def __init__(
        self,
        model_name: str = "msmarco-distilbert-base-v4",
    ) -> None:
        self.model = SentenceTransformer(model_name)

    def encode_sents(self, sents: list[str]) -> None:
        print("\nEncoding sentences. This might take a while...")
        self.sent_embeds = self.model.encode(sents)

    def load_sent_embeds(self, sent_embeds: ndarray) -> None:
        self.sent_embeds = sent_embeds

    def query_sents(
        self,
        query: str | list[str],
        top_n: int | None = 25,
        return_scores: bool = False,
    ) -> list[int] | list[tuple[int, float]]:
        """
        If query is a list of strings, sentences will be ranked by their
        best score for any of the queries.
        """
        if type(query) is str:
            query = [query]
        all_scores = []
        for query_str in query:
            query_embed = self.model.encode(query_str)
            query_scores = (
                util.cos_sim(query_embed, self.sent_embeds)[  # type: ignore
                    0
                ]
                .cpu()
                .tolist()
            )  # type: ignore
            all_scores.append(query_scores)
        max_scores = [max(x) for x in zip(*all_scores)]
        counter = Counter({i: score for i, score in enumerate(max_scores)})
        results = []
        for i, score in counter.most_common(top_n):
            if return_scores:
                results.append((i, score))
            else:
                results.append(i)
        return results

    def query_sents_from_db(
        self,
        query: str | list[str],
        sent_dicts: list[dict[str, Any]],
        top_n: int | None = 25,
    ) -> list[dict[str, str]]:
        if type(query) is str:
            query = [query]
        all_scores = []
        embeds = [sent_d["embedding"] for sent_d in sent_dicts]
        embeds = array(embeds)
        for query_str in query:
            query_embed = self.model.encode(query_str)
            query_scores = (
                util.cos_sim(query_embed, embeds)[  # type: ignore
                    0
                ]
                .cpu()
                .tolist()
            )  # type: ignore
            all_scores.append(query_scores)
        max_scores = [max(x) for x in zip(*all_scores)]
        counter = Counter({i: score for i, score in enumerate(max_scores)})
        results = []
        for i, score in counter.most_common(top_n):
            sent_dict = sent_dicts[i]
            results.append(
                {"sentence": sent_dict["sentence"], "file_path": sent_dict["file_path"]}
            )
        return results
