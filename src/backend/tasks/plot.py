from typing import Any, Callable
import re

from PySide6.QtCore import qDebug
from backend.utils.nlp import SpacyModel


def regex(
    sent_batches: dict[str, list[str]], pattern, per="total"
) -> list[tuple[Any, int | float]]:
    match_counts = []
    model = SpacyModel()
    for label, sents in sent_batches.items():
        sent_count = 0
        word_count = 0
        match_count = 0
        for sent in sents:
            sent_count += 1
            tokens = model.word_tokenize(sent)
            word_count += len(tokens)
            match_count += len(re.findall(pattern, sent))
        if per == "per sentence":
            value = match_count / sent_count
        elif per == "per word":
            value = match_count / word_count
        else:
            value = match_count
        try:
            label = float(label)
        except ValueError:
            pass
        match_counts.append((label, value))
    return match_counts


def custom(
    sent_batches: dict[str, list[str]], code_str: str, per="total"
) -> list[tuple[Any, int | float]]:
    code: Callable = eval(f"lambda sentence: {code_str}")
    counts = []
    model = SpacyModel()
    for label, sents in sent_batches.items():
        sent_count = 0
        word_count = 0
        count = 0
        for sent in sents:
            sent_count += 1
            tokens = model.word_tokenize(sent)
            word_count += len(tokens)
            result = code(sent)
            if result is True:
                count += 1
            elif type(result) in (int, float):
                count += result
        if per == "per sentence":
            value = count / sent_count
        elif per == "per word":
            value = count / word_count
        else:
            value = count
        try:
            label = float(label)
        except ValueError:
            pass
        counts.append((label, value))
    return counts


def get_plot_values(
    sent_batches: dict[str, Any], plot_d: dict[str, Any]
) -> list[tuple[Any, int | float]]:
    func = regex if plot_d["y_type"] == "Regex" else custom
    target = plot_d["y_func"]
    plot_values = func(sent_batches, target, plot_d["y_per"])
    return plot_values
