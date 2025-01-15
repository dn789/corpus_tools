from collections import Counter
from typing import Any
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification


class NERModel:
    """Named entity recognition"""

    def __init__(self):
        tokenizer = AutoTokenizer.from_pretrained(
            "xlm-roberta-large-finetuned-conll03-english"
        )
        model = AutoModelForTokenClassification.from_pretrained(
            "xlm-roberta-large-finetuned-conll03-english"
        )
        self.classifier = pipeline(
            "ner", model=model, tokenizer=tokenizer, device="cuda:0"
        )

    def get_entities(
        self, text: str | list, raw: bool = False, batch_size=8
    ) -> list[dict] | list[list[dict]] | None:
        raw_entities = self.classifier(text, batch_size=batch_size)
        if raw:
            return raw_entities  # type: ignore
        else:
            if not raw_entities:
                return
            entities = []
            if type(text) is str:
                to_combine = [raw_entities]
            else:
                to_combine = raw_entities
            for raw_ents in to_combine:
                entities.extend(self.combine_entities(raw_ents))  # type: ignore
            return entities

    def combine_entities(self, entities: dict[int, Any]):
        combined_entities = []
        current_word = ""
        current_entity = ""

        for i in range(len(entities)):
            entity = entities[i]
            word = entity["word"]
            # Get the entity type (ignore "I-" or "O-")
            entity_type = entity["entity"][2:]

            if i > 0 and entities[i - 1]["end"] == entity["start"]:
                # If the end of the previous entity matches the start of the current one, combine
                # Remove the leading separator if present
                current_word += word.lstrip("▁")
            else:
                # If not, save the current entity (if any) and start a new one
                if current_word:
                    combined_entities.append(
                        {"type": current_entity, "word": current_word}
                    )
                current_word = word.lstrip("▁")  # Start a new word
                current_entity = entity_type  # Set the new entity type

        # Add the last combined entity if it exists
        if current_word:
            combined_entities.append({"type": current_entity, "word": current_word})

        return combined_entities

    def get_entities_from_sents(
        self,
        sent_dicts: dict[str, Any],
        batch_size: int = 8,
        frontend_connect: Any | None = None,
    ):
        model = NERModel()
        sents = [sent_d["sentence"] for sent_d in sent_dicts]  # type: ignore
        if frontend_connect:
            frontend_connect.taskInfo.emit(
                "Finding named entities. This might take a while...", None
            )
        entities = model.get_entities(sents, batch_size=batch_size)
        if not entities:
            return []
        entity_type_tuples = [
            (entity["word"], entity["type"])  # type: ignore
            for entity in entities
        ]
        entities_counter = Counter(entity_type_tuples)
        results = []
        for (word, ent_type), count in entities_counter.most_common():
            results.append((word, ent_type, count))
        return results
