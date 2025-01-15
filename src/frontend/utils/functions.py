from typing import Any
from PySide6.QtWidgets import QHBoxLayout, QLayout, QVBoxLayout, QWidget

from frontend.styles.colors import random_color_rgb

from backend.corpus.items import Folder, GenericCorpusItem, CorpusItem


def clear_layout(layout: QLayout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()  # type: ignore
            if widget is not None:
                widget.setParent(None)
            else:
                clear_layout(item.layout())  # type: ignore


def make_corpus_item(prop_name: str, raw_item: Any) -> CorpusItem:
    if prop_name == "included_extensions":
        item = GenericCorpusItem(name=raw_item, color=random_color_rgb())  # type: ignore
    elif prop_name == "subfolders":
        item = Folder(color=random_color_rgb(), path=raw_item, name=raw_item.name)  # type: ignore
    return item


def change_style(widget: QWidget, style: str, new_value: Any) -> None:
    "Convenience functin for changing a single style in a QSS stylesheet."
    stylesheet = widget.styleSheet().split("\n")
    for i, line in enumerate(stylesheet):
        if line.split(":")[0].strip() == style:
            stylesheet[i] = f"{style}: {new_value};"
    widget.setStyleSheet("\n".join(stylesheet))


def prune_object(obj: dict | list, max_keys):
    """
    Recursively prunes a nested dictionary/list to a maximum of `max_keys` at
    each level. Used for displaying pruned versions of file and document trees.

    Args:
        obj (dict | list):  The nested dictionary or list object to be pruned
        max_keys (_type_): The maximum number of keys or elements to display at each level.

    Returns:
        dict | list: The pruned object.
    """

    if isinstance(obj, dict):
        # If the object is a dictionary, prune it to the max_keys number of keys
        pruned_dict = {}
        for idx, (key, value) in enumerate(obj.items()):
            if idx >= max_keys:
                break
            pruned_dict[key] = prune_object(value, max_keys)
        return pruned_dict

    elif isinstance(obj, list):
        # If the object is a list, prune it to the max_keys number of elements
        return [prune_object(item, max_keys) for item in obj[:max_keys]]

    else:
        # If it's neither a dictionary nor a list, return the object as-is
        return obj


def get_widgets(layout: QVBoxLayout | QHBoxLayout) -> list[QWidget]:
    """Convenience function for getting widgets from a layout."""
    widgets = []
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item.widget():
            sub_widget = item.widget()
            widgets.append(sub_widget)
    return widgets
