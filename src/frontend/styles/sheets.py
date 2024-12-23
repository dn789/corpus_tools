from PySide6.QtWidgets import QWidget


TOOLTIP_STYLE = """
    QToolTip { 
        color: black;
        background-color: white;
        font-weight: normal;
        padding: 5px;
    }
"""

TOOLTIP_NO_WRAP_HTML = """
            <html>
                <style>
                    body {{ white-space: nowrap; }}
                </style>
                <body>
                   {}
                </body>
            </html>
"""


def no_wrap_tooltip(text: str) -> str:
    return TOOLTIP_NO_WRAP_HTML.format(text)


def add_tooltip(
    obj: QWidget, text: str, no_wrap: bool = True, add_style: bool = True
) -> None:
    """Adds tooltip with global tooltip style formatting to widget

    If setting a stylesheet on the widget, this will only work if called
    afterwards.

    Args:
        obj (QWidget): Widget to set the tooltip on
        text (str): Tooltip text
        no_wrap (bool, optional): Whether to disable line-wrapping on the
            tooltip. Defaults to True.
        add_style (bool, optional): Whether to add the global tooltip style.
            Set to False for updating tooltips when you just want to use
            no_wrap. Defaults to True.
    """
    if add_style:
        styleSheet = f"{obj.styleSheet()} {TOOLTIP_STYLE}"
        obj.setStyleSheet(styleSheet)
    text = no_wrap_tooltip(text) if no_wrap else text
    obj.setToolTip(text)
