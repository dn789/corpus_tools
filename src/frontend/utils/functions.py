from typing import Any
from PySide6.QtCore import qDebug
from PySide6.QtWidgets import QDialog, QLayout

from frontend.styles.colors import random_color_rgb

from backend.corpus.items import Folder, GenericCorpusItem, CorpusItem
from frontend.widgets.dialogs import MakeDocLabel


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
    # elif prop_name in ("text_labels", "meta_labels"):
    #     dialog = MakeDocLabel("test", "test")
    #     if dialog.exec() == QDialog.accepted:
    #         qDebug("((()))")
    #         qDebug(str(dialog))
    #         qDebug(str(dialog.get_results()))
    #         qDebug("((()))")
    return item
