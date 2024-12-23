from PySide6.QtWidgets import QLayout


def clear_layout(layout: QLayout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()  # type: ignore
            if widget is not None:
                widget.setParent(None)
            else:
                clear_layout(item.layout())  # type: ignore
