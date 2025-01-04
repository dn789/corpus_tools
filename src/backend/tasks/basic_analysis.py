from frontend.widgets.tables import SearchableTable
from backend.nlp_models.grammar import GrammarTask
from backend.nlp_models.ner import NERModel
from backend.utils.nlp import get_n_grams_from_corpus, summary


TASK_DICT = {
    "Summary": {
        "func": summary,
        "tooltip": "Summary data",
        "display": lambda results: SearchableTable(["Feature", "Value"], results),
    },
    "N-grams": {
        "func": get_n_grams_from_corpus,
        "tooltip": "N-grams",
        "display": lambda results: SearchableTable(["N-gram", "Count"], results),
    },
    "Grammar": {
        "class": GrammarTask,
        "func": GrammarTask.get_errors,
        "tooltip": "Errors and corrections using Grammarly",
        "display": lambda results: SearchableTable(
            ["error type", "original", "edited", "sentence", "file"], results
        ),
    },
    "NER": {
        "class": NERModel,
        "func": NERModel.get_entities_from_sents,
        "tooltip": "Named entity recognition",
        "display": lambda results: SearchableTable(["word", "type", "count"], results),
    },
}
