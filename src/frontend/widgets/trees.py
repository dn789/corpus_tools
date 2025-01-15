"""Folder and document view trees for annotating/corpus configuration."""

from frozendict import frozendict
from pathlib import Path
from typing import Any, Callable

from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QMenu,
    QTreeWidget,
    QTreeWidgetItem,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QWidgetAction,
)


from backend.corpus.items import DocLabel, Folder, LabelType
from frontend.styles.colors import Colors, is_dark
from frontend.styles.icons import Icons

from frontend.project import ProjectWrapper as Project
from frontend.utils.functions import (
    change_style,
    clear_layout,
    make_corpus_item,
    prune_object,
)
from frontend.widgets.dialogs import MakeDocLabel
from frontend.widgets.small import CorpusLabel


class FolderTreeNode(QWidget):
    def __init__(self, name: str, icon: QIcon | None = None) -> None:
        super().__init__()
        self.name = name
        self.main_layout = QHBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.main_layout)
        self.icon_label = None

        if icon:
            self.set_icon(icon)

        self.text_label = QLabel(name)
        self.setStyleSheet(f"""
                    QLabel {{
                        font-size: 16px;
                        border-radius: 5px;
                        padding: 2px;
                    }}
                    QLabel:hover {{
                        background-color: {Colors.light_blue};
                    }}""")

        self.main_layout.addWidget(self.text_label)
        self.tag_layout = QHBoxLayout()
        self.main_layout.addLayout(self.tag_layout)

    def set_icon(self, icon: QIcon):
        if self.icon_label:
            self.main_layout.removeWidget(self.icon_label)
            self.icon_label.deleteLater()
        self.icon_label = QLabel()
        self.icon_label.setPixmap(icon.pixmap(25, 25))
        self.main_layout.insertWidget(0, self.icon_label)


class DocTreeNode(QWidget):
    def __init__(
        self,
        key: frozendict | str,
        file_type: str,
    ) -> None:
        super().__init__()
        self.key = key
        self.file_type = file_type
        self.main_layout = QHBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.label_frame = QFrame()
        self.label_frame_layout = QHBoxLayout()
        self.label_frame_layout.setContentsMargins(0, 5, 0, 5)
        self.label_frame_layout.setSpacing(5)
        self.label_frame.setLayout(self.label_frame_layout)
        self.setLayout(self.main_layout)
        self.main_layout.addWidget(self.label_frame)
        self.icon_label = None
        self.label_d = {"label_name": {}, "attrs": {}}
        self.doc_label_parents = {LabelType.TEXT: {}, LabelType.META: {}}

        if type(self.key) is frozendict:
            self.label_d["label_name"]["name"] = key["_tag"]  # type: ignore
            self.label_d["label_name"]["widget"] = QLabel(
                f"<b>{key['_tag']}</b>"  # type: ignore
            )  # type: ignore
            for k, v in self.key.items():
                if k == "_tag":
                    continue
                self.label_d["attrs"][k] = {
                    "value": v,
                    "widget": QLabel(f"<i>{k}</i>=<b>{v}</b>"),
                }

        else:
            self.label_d["label_name"]["name"] = key
            self.label_d["label_name"]["widget"] = QLabel(f"<b>{self.key}</b>")  # type: ignore

        self.setStyleSheet(f"""
                .QFrame {{
                    border-radius: 5px;
                    border: 1px solid black;
                }}
                QLabel {{
                    font-size: 16px;
                    border-radius: 5px;
                    padding-top: 5px;
                    padding-bottom: 5px;
                    margin: 0px;
                }}    
                QWidget:hover {{
                    background-color: {Colors.light_gray};
                }}""")

        if self.file_type == ".xml":
            self.label_frame_layout.addWidget(QLabel("&lt;"))
            self.label_frame_layout.addWidget(self.label_d["label_name"]["widget"])
            for d in self.label_d["attrs"].values():
                self.label_frame_layout.addWidget(d["widget"])
            self.label_frame_layout.addWidget(QLabel(">"))
        else:
            self.label_frame_layout.addWidget(self.label_d["label_name"]["widget"])

        self.tag_layout = QHBoxLayout()
        self.main_layout.addLayout(self.tag_layout)


class DocText(QWidget):
    def __init__(self, text, index: int | None = None):
        super().__init__()
        layout = QHBoxLayout()
        self.label_text = text
        self.doc_label_parent = False
        if type(index) is int:
            self.label_text = f"<b>[{index}]</b>\t{text}"
        self.label = QLabel(self.label_text)
        self.label.setStyleSheet("""
            font-size: 16px;
            margin-left: 10px;
            border-radius: 5px;
            padding: 5px;
            background-color: transparent;
            """)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.label)
        self.setLayout(layout)


def highlight_tree_node(
    tree_node: FolderTreeNode | DocTreeNode,
    color: tuple[int, int, int] | None = None,
    reset: bool = False,
    target_label_or_name: DocLabel | str | None = None,
    target_label_type: LabelType | None = None,
) -> None:
    """
    Highlights/removes highlighting from Folder and Doc TreeNodes.

    - For FolderTreeNodes, just change stext and background color of the text label
    - For DocTreeNodes:
        - highlights/de-highlights XML tag/JSON key name
        - highlights/de-highlights any attributes that are part of the doc_label

        (If remove, target_label_or_name is just DocLabel.name, and
        target_label_type is needed to get the dictionary key in
        target_node.doc_label_parents.)
    Args:
        tree_node (FolderTreeNode | DocTreeNode): _description_
        color (tuple[int, int, int] | None, optional): _description_. Defaults to None.
        reset (bool, optional): _description_. Defaults to False.
        target_label_or_name (DocLabel | str | None, optional): _description_. Defaults to None.
        target_label_type (LabelType | None, optional): _description_. Defaults to None.
    """
    text_color = "black"
    if reset:
        color = "transparent"  # type: ignore
        color_lighter = "transparent"
    else:
        if is_dark(*color):  # type: ignore
            text_color = "white"
        color_lighter = f"rgba{color + (75,)}"  # type: ignore
        color = f"rgb{color}"  # type: ignore

    color_style_sheet = f"background-color: {color}; color: {text_color};"
    color_lighter_style_sheet = f"background-color: {color_lighter}; color: black;"

    if isinstance(tree_node, FolderTreeNode):
        tree_node.text_label.setStyleSheet(color_style_sheet)
    else:
        tree_node.label_d["label_name"]["widget"].setStyleSheet(color_style_sheet)
        if reset and isinstance(target_label_type, LabelType):
            for attr_name, d in tree_node.label_d["attrs"].items():
                if isinstance(widget := d["widget"], QLabel):
                    widget.setStyleSheet(color_style_sheet)
                else:
                    index = tree_node.label_frame_layout.indexOf(widget)
                    tree_node.label_frame_layout.removeWidget(widget)
                    widget.deleteLater()
                    d["widget"] = QLabel(f"<i>{attr_name}</i>=<b>{d['value']}</b>")
                    tree_node.label_frame_layout.insertWidget(index, d["widget"])

            widget = tree_node.doc_label_parents[target_label_type][
                target_label_or_name
            ]
            tree_node.main_layout.removeWidget(widget)
            widget.deleteLater()
            tree_node.doc_label_parents[target_label_type][
                target_label_or_name
            ].deleteLater()
            tree_node.doc_label_parents[target_label_type].pop(target_label_or_name)

        elif isinstance(target_label_or_name, DocLabel):
            for attr_name, d in tree_node.label_d["attrs"].items():
                if attr_name in target_label_or_name.label_attrs:
                    d["widget"].setStyleSheet(color_style_sheet)
                elif target_label_or_name.value_in_attrs:
                    old_widget = d["widget"]
                    index = tree_node.label_frame_layout.indexOf(old_widget)
                    tree_node.label_frame_layout.removeWidget(old_widget)
                    old_widget.deleteLater()
                    prop_name_label = QLabel(f"<i>{attr_name}</i>")
                    prop_name_label.setStyleSheet(color_style_sheet)
                    eq_label = QLabel("=")
                    eq_label.setStyleSheet("padding: 0px; margin: 0px;")
                    prop_value_label = QLabel(f"<b>{d['value']}</b>")
                    prop_value_label.setStyleSheet(color_lighter_style_sheet)
                    new_label_widget = QWidget()
                    layout = QHBoxLayout()
                    layout.setContentsMargins(5, 0, 5, 0)
                    layout.setSpacing(0)
                    new_label_widget.setLayout(layout)
                    for label in (prop_name_label, eq_label, prop_value_label):
                        label.setContentsMargins(0, 0, 0, 0)
                        layout.addWidget(label)
                    d["widget"] = new_label_widget
                    tree_node.label_frame_layout.insertWidget(index, d["widget"])

            label_text = (
                f"{target_label_or_name.name} ({target_label_or_name.type.name})"
            )
            label_widget = CorpusLabel(
                label_text, target_label_or_name.color, text_color
            )
            tree_node.doc_label_parents[target_label_or_name.type][
                target_label_or_name.name
            ] = label_widget
            tree_node.main_layout.addWidget(label_widget)


class FolderViewer(QTreeWidget):
    def __init__(self, project: Project) -> None:
        super().__init__()
        self.project = project
        self.header_placeholder = "Select content file extensions and subfolders here"
        self.setHeaderLabel(self.header_placeholder)
        self.path = None
        self.project.projectLoaded.connect(self.populate_tree)
        self.project.corpusConfigUpdated.connect(self.check_populate_tree)
        self.project.projectLoaded.connect(self.populate_tree)
        self.project.projectLoaded.connect(self.tag_nodes_on_project_load)
        self.project.corpusConfigUpdated.connect(self.tag_nodes)
        self.folder_icon = Icons.folder_closed()
        self.file_icon = Icons.file()
        self.file_checked_icon = Icons.file_checked()
        self.setStyleSheet("""
            QTreeWidget::item {
                margin-left: -30px;
            }
            QHeaderView {
                font-size: 20px;
                height: 50px;
            }
        """)

        self.populate_tree()

    def check_populate_tree(
        self,
        prop_name: str | None = None,
        content: Any | None = None,
        remove: bool = False,
    ) -> None:
        if prop_name == "corpus_path":
            self.populate_tree(content)
        # else:
        #     self.clear()

    def populate_tree(self, path: Path | None = None):
        self.clear()
        path = path or self.project.corpus_config.corpus_path
        if path:
            # self.path = Path(path)
            self.setHeaderLabel(path.__str__())
            self.add_node(self, path)
        else:
            self.setHeaderLabel(self.header_placeholder)
        self.expandAll()

    def add_node(self, parent, path: Path):
        for node_path in path.iterdir():
            node_name = node_path.name
            icon = self.folder_icon if node_path.is_dir() else self.file_icon
            widget = FolderTreeNode(node_name, icon)
            tree_item = QTreeWidgetItem(parent)
            self.setItemWidget(tree_item, 0, widget)

            tree_item.setData(0, 1, node_path)

            if node_path.is_dir():
                self.add_node(tree_item, node_path)

    def set_icon_on_tree_node(self, icon: QIcon, tree_node: FolderTreeNode) -> None:
        tree_node.set_icon(icon)

    def tag_nodes_on_project_load(self):
        self.tag_nodes(
            "included_extensions", self.project.corpus_config.get_extensions()
        )
        self.tag_nodes("subfolders", self.project.corpus_config.get_subfolders())

    def tag_nodes(self, prop_name, content, remove: bool = False):
        content = content if type(content) is list else [content]

        if prop_name == "included_extensions":
            if remove:
                targets = content

                def action_func(_: Any, tree_node_widget: FolderTreeNode) -> None:  # type: ignore
                    tree_node_widget.set_icon(self.file_icon)
            else:
                targets = [item.name for item in content]

                def action_func(_: Any, tree_node_widget: FolderTreeNode) -> None:  # type: ignore
                    tree_node_widget.set_icon(self.file_checked_icon)

            def filter_func(node: QTreeWidgetItem):  # type: ignore
                path = node.data(0, 1)
                return path and path.is_file() and path.suffix in targets

        elif prop_name == "subfolders":
            targets = content
            if remove:

                def action_func(_: Any, tree_node_widget: FolderTreeNode):  # type: ignore
                    highlight_tree_node(tree_node_widget, reset=True)
            else:

                def action_func(target: Folder, tree_node_widget: FolderTreeNode):
                    highlight_tree_node(tree_node_widget, target.color)

            def filter_func(node: QTreeWidgetItem) -> Folder | None:
                path = node.data(0, 1)
                for target in targets:
                    if type(target) is Folder:
                        if path == target.path:
                            return target
                    elif path == target:
                        return target
        else:
            return

        root = self.invisibleRootItem()

        self.tag_nodes_inner(
            root,
            filter_func,
            action_func,
        )

    def tag_nodes_inner(
        self,
        node: QTreeWidgetItem,
        filter_func: Callable,
        action_func: Callable,
    ):
        tree_node_widget: FolderTreeNode = self.itemWidget(node, 0)  # type: ignore
        if target := filter_func(node):
            action_func(target, tree_node_widget)

        for i in range(node.childCount()):  # Iterate through child items
            self.tag_nodes_inner(node.child(i), filter_func, action_func)


class DocViewer(QTreeWidget):
    def __init__(
        self,
        project: Project,
        doc_data: dict[str, Any] | None = None,
        file_path: Path | None = None,
    ):
        super().__init__()
        self.project = project
        self.doc_data = doc_data
        self.project.corpusConfigUpdated.connect(self.tag_nodes)
        self.project.projectLoaded.connect(self.clear_)
        self.header_placeholder = "Select text and meta labels here"
        self.setHeaderLabel(self.header_placeholder)
        self.setStyleSheet("""
            QTreeWidget::item {
                margin-left: -30px;
            }
            QHeaderView {
                font-size: 20px;
                height: 50px;
            }
        """)
        if doc_data and file_path:
            self.populate_tree(doc_data, file_path)

    def clear_(self):
        self.clear()
        self.setHeaderLabel(self.header_placeholder)

    def populate_tree(self, data: dict[str, Any], file_path: Path):
        self.clear_()
        if data:
            header_label = file_path.name
            pruned_data = prune_object(data, 100)  # type: ignore
            if pruned_data != data:
                header_label = (
                    f"{header_label} (File too large. Only a portion is shown.)"
                )
            self.setHeaderLabel(header_label)
            self.file_type = file_path.suffix
            self.context_menu.file_type = file_path.suffix  # type: ignore

            self.add_node(self, pruned_data)
        self.expandAll()
        self.tag_nodes_on_doc_load()

    def add_node(self, parent, data: Any, level: int = 0):
        if isinstance(data, dict):
            for key, value in data.items():
                widget = DocTreeNode(key, file_type=self.file_type)
                tree_item = QTreeWidgetItem(parent)
                self.setItemWidget(tree_item, 0, widget)

                if value:
                    tree_item.setData(0, 1, key)
                    self.add_node(
                        tree_item, value, level + 1
                    )  # Recursively add nested dicts
                else:
                    tree_item.setData(0, 1, data)

        elif isinstance(data, list):
            for item in data:
                self.add_node(parent, item, level + 1)  # Recursively add list items

        else:
            widget = DocText(str(data))
            tree_item = QTreeWidgetItem(parent)
            self.setItemWidget(tree_item, 0, widget)
            tree_item.setData(0, 1, data)

    def tag_nodes_on_doc_load(self):
        self.tag_nodes(
            "text_labels",
            self.project.corpus_config.get_text_labels(file_type=self.file_type),
        )
        self.tag_nodes(
            "text_labels",
            self.project.corpus_config.get_meta_labels(file_type=self.file_type),
        )

    def check_for_tagged_text(self, tree_item: QTreeWidgetItem) -> bool | None:
        widget = self.itemWidget(tree_item, 0)
        if isinstance(widget, DocText):
            if widget.doc_label_parent:
                return True
        # if isinstance(widget, DocTreeNode):
        # for label_type, parents in widget.doc_label_parents.items():
        #     doc_labels = getattr(
        #         self.project.corpus_config, f"{label_type.name.lower()}_labels"
        #     )
        #     for label_name, widget in parents.items():
        #         doc_label = doc_labels[label_name]
        #         if not doc_label.value_in_attrs:
        #             return True

        for row in range(tree_item.childCount()):
            child = tree_item.child(row)
            if self.check_for_tagged_text(child):
                return True

    def tag_nodes(
        self,
        prop_name,
        targets: DocLabel | list[DocLabel] | str | list[str],
        remove: bool = False,
    ):
        targets = targets if isinstance(targets, list) else [targets]  # type: ignore
        # Need target_type to access widget from appropriate dictionary in
        # target_node.doc_label_parents when remove=True because no DocLabel is
        # provided.
        target_type = LabelType.META if prop_name == "meta_labels" else LabelType.TEXT

        if remove:

            def action_func(target: str, tree_node_widget: DocTreeNode) -> None:  # type: ignore
                highlight_tree_node(
                    tree_node_widget,
                    reset=True,
                    target_label_or_name=target,
                    target_label_type=target_type,
                )
        else:

            def action_func(target: DocLabel, tree_node_widget: DocTreeNode) -> None:
                highlight_tree_node(
                    tree_node_widget, target.color, target_label_or_name=target
                )

        def filter_func(tree_node_widget: DocTreeNode) -> DocLabel | str | None:
            for target in targets:
                if isinstance(target, DocLabel) and target.match_label(
                    tree_node_widget.key
                ):
                    return target
                elif (
                    isinstance(target, str)
                    and target in tree_node_widget.doc_label_parents[target_type]
                ):
                    return target

        root = self.invisibleRootItem()

        self.tag_nodes_inner(root, filter_func, action_func)

    def tag_nodes_inner(
        self,
        node: QTreeWidgetItem,
        filter_func: Callable,
        action_func: Callable,
        highlight_text: bool = False,
        highlight_color: tuple[int, int, int] | None = None,
    ):
        widget: DocTreeNode | DocText | None = self.itemWidget(node, 0)  # type: ignore
        if isinstance(widget, DocTreeNode):
            if target := filter_func(widget):
                action_func(target, widget)
                highlight_text = True
                if isinstance(target, DocLabel):
                    if not target.value_in_attrs:
                        highlight_color = target.color + (75,)  # type: ignore
                    else:
                        highlight_text = False
                else:
                    highlight_color = None

        elif isinstance(widget, DocText) and highlight_text:
            if highlight_color:
                widget.doc_label_parent = True  # type: ignore
                change_style(widget.label, "background-color", f"rgba{highlight_color}")
            else:
                widget.doc_label_parent = False  # type: ignore
                change_style(widget.label, "background-color", "transparent")

        for i in range(node.childCount()):  # Iterate through child items
            self.tag_nodes_inner(
                node.child(i),
                filter_func,
                action_func,
                highlight_text=highlight_text,
                highlight_color=highlight_color,
            )


class TreeContextMenu(QMenu):
    def __init__(self, parent, project: Project):
        super().__init__(parent)
        self.parent = parent
        self.type = "folder" if type(parent) is FolderViewer else "doc"

        self.file_type = None
        self.project = project
        self.setStyleSheet("font-size: 14px;")

        self.actions_layout = QVBoxLayout()
        self.actions_layout.setSpacing(10)  # Remove spacing
        self.actions_widget = QWidget(self)  # Widget to contain buttons
        self.actions_widget.setLayout(self.actions_layout)
        self.widget_action = QWidgetAction(self)

    def add_actions(
        self,
        data: Any,
        tree_item_widget: FolderTreeNode | DocTreeNode | DocText,
        tagged_text_under_node: bool = False,
    ):
        clear_layout(self.actions_layout)

        actions = []

        for prop_name in (
            "included_extensions",
            "subfolders",
            "text_labels",
            "meta_labels",
        ):
            menu_item = None
            menu_item_name = None
            remove = False

            if self.type == "folder":
                if data.is_file() and prop_name == "included_extensions":
                    menu_item = data.suffix
                    menu_item_name = menu_item

                elif data.is_dir() and prop_name == "subfolders":
                    self.add_multi_subfolder_action(data, actions)
                    menu_item = data
                    menu_item_name = data.name

                if not menu_item:
                    continue

                if menu_item in getattr(
                    self.project.corpus_config,
                    prop_name,  # type: ignore
                ):
                    remove = True

            elif self.type == "doc":
                if isinstance(tree_item_widget, DocTreeNode) and prop_name in (
                    "text_labels",
                    "meta_labels",
                ):
                    label_type = (
                        LabelType.META if prop_name == "meta_labels" else LabelType.TEXT
                    )
                    if d := tree_item_widget.doc_label_parents[label_type]:
                        remove = True
                        menu_item = list(d.keys())[0]
                        menu_item_name = menu_item
                    else:
                        if tagged_text_under_node:
                            if prop_name == "text_labels" or self.file_type != ".xml":
                                continue
                        menu_item = tree_item_widget.key
                        menu_item_name = tree_item_widget.label_d["label_name"]["name"]

                if not menu_item:
                    continue

            if remove:
                verb = ("Remove", "from")
            else:
                verb = ("Add", "to")

            prop_display_name = self.project.corpus_config.get_display_name(prop_name)
            text = f"{verb[0]} <b>{menu_item_name}</b> {verb[1]} {prop_display_name.lower()}"

            if prop_name in ("meta_labels, text_labels"):
                if not remove:

                    def func(  # type: ignore
                        _,
                        menu_item=menu_item,
                        menu_item_name=menu_item_name,
                        label_type=label_type,
                        file_type=self.file_type,
                    ):
                        return self.get_doc_label_action_func(
                            menu_item,
                            menu_item_name,  # type: ignore
                            label_type,
                            file_type,  # type: ignore
                            tagged_text_under_node,
                        )
                else:

                    def func(  # type: ignore
                        _,
                        prop_name=prop_name,
                        content=menu_item_name,
                        remove=remove,
                    ):
                        return self.project.update_corpus_items(
                            prop_name, content, remove=remove
                        )

            else:
                if not remove:
                    content = make_corpus_item(prop_name, menu_item)
                else:
                    content = menu_item

                def func(_, prop_name=prop_name, content=content, remove=remove):
                    return self.project.update_corpus_items(
                        prop_name, content, remove=remove
                    )

            action = ContextMenuAction(self, text, func)
            actions.append(action)

        for action in actions:
            self.actions_layout.addWidget(action)

        self.check_if_empty()

    def check_if_empty(self):
        if self.actions_layout.isEmpty():
            QTimer.singleShot(0, self.close)

    def get_doc_label_action_func(
        self,
        menu_item: Any,
        menu_item_name: str,
        label_type: LabelType,
        file_type: str,
        tagged_text_under_node: bool = False,
    ):
        dialog = MakeDocLabel(
            menu_item, menu_item_name, label_type, file_type, tagged_text_under_node
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            doc_label = dialog.get_results()
            prop_name = "text_labels" if label_type is LabelType.TEXT else "meta_labels"
            self.project.update_corpus_items(prop_name, doc_label)

    def add_multi_subfolder_action(self, path: Path, actions: list) -> None:
        remove = False
        subfolders = [subpath for subpath in path.iterdir() if subpath.is_dir()]
        if not subfolders:
            return
        added_subfolders = [
            folder
            for folder in subfolders
            if folder in self.project.corpus_config.subfolders
        ]
        if added_subfolders:
            remove = True
            subfolders = added_subfolders
        else:
            subfolders = [
                make_corpus_item("subfolders", subfolder) for subfolder in subfolders
            ]
        verb = ("Remove", "from") if remove else ("Add", "to")
        text = f"{verb[0]} subfolders of <b>{path.name}</b> {verb[1]} subfolders"

        def func(_, prop_name="subfolders", content=subfolders, remove=remove):
            return self.project.update_corpus_items(prop_name, content, remove=remove)

        action = ContextMenuAction(self, text, func)
        actions.append(action)

    def show(self, pos):
        # Remove any existing QWidgetAction first to prevent stacking actions
        if self.widget_action in self.actions():
            self.removeAction(self.widget_action)
        # Use QWidgetAction to embed the button layout inside the context menu
        self.widget_action.setDefaultWidget(self.actions_widget)
        # Add the QWidgetAction to the menu
        self.addAction(self.widget_action)
        # Show the context menu at the correct position
        self.exec(self.parent.viewport().mapToGlobal(pos))


class ContextMenuAction(QLabel):
    def __init__(self, parent, text: str, func: Callable) -> None:
        super().__init__(parent)
        self.parent = parent
        self.setText(text)
        self.func = func
        self.setStyleSheet(f"""
            QLabel {{
                padding: 10px;
                background-color: transparent;
                border: 1px solid black;
                border-radius: 5px;
                font-size: 16px;
            }}
            QLabel:hover {{
                background-color:  {Colors.light_blue};
            }}
        """)

        # Make it clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # Reimplement mousePressEvent to handle clicks
        self.mousePressEvent = self.handleClick  # type: ignore

    def handleClick(self, event):
        self.func(None)  # Call the function associated with this action
        self.parent.close()  # Close the parent (assuming it's a context menu or similar)
