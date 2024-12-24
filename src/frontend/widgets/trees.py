from pathlib import Path, PurePath
from typing import Any, Callable
import xml.etree.ElementTree as ET
import json

from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer, Qt, qDebug
from PySide6.QtWidgets import (
    QDialog,
    QMenu,
    QTreeWidget,
    QTreeWidgetItem,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QWidgetAction,
)

from backend.corpus.items import Folder
from frontend.styles.colors import Colors
from frontend.styles.icons import Icons

# from frontend.widgets.small import ContextMenuAction
from frontend.project import ProjectWrapper as Project
from frontend.widgets.small import CorpusTag
from frontend.utils.functions import (
    clear_layout,
    make_corpus_item,
    # get_xml_node_str_from_xml_node,
    # parse_xml_node_str,
)


class TreeNodeOld(QWidget):
    def __init__(
        self, name: str, icon: QIcon | None = None, tree_type: str = "folder"
    ) -> None:
        super().__init__()
        self.name = name
        self.tree_type = tree_type
        self.main_layout = QHBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.main_layout)
        self.icon_label = None

        if icon:
            self.set_icon(icon)

        self.text_label = QLabel(name)
        if self.tree_type == "folder":
            self.text_label.setStyleSheet(f"""
                    QWidget {{
                        font-size: 16px;
                        border-radius: 5px;
                        padding: 2px;
                    }}
                    QWidget:hover {{
                        background-color: {Colors.light_blue};
                    }}""")
        else:
            self.text_label.setStyleSheet(f"""
                    QWidget {{
                        font-size: 14px;
                        border-radius: 5px;
                        background-color: {Colors.light_blue};
                        padding: 3px;
                        border: 1px solid black;
                    }}
                    QWidget:hover {{
                        background-color: {Colors.light_gray};
                    }}""")

        self.main_layout.addWidget(self.text_label)
        self.tag_layout = QHBoxLayout()
        self.main_layout.addLayout(self.tag_layout)

    def set_icon(self, icon: QIcon):
        if self.icon_label:
            self.main_layout.removeWidget(self.icon_label)
            self.icon_label.deleteLater()
        self.icon_label = QLabel()
        # self.icon_label.setIcon(icon)
        self.icon_label.setPixmap(icon.pixmap(25, 25))
        self.main_layout.insertWidget(0, self.icon_label)


class TreeNode(QWidget):
    def __init__(
        self, name: str, icon: QIcon | None = None, tree_type: str = "folder"
    ) -> None:
        super().__init__()
        self.name = name
        self.tree_type = tree_type
        self.main_layout = QHBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.main_layout)
        self.icon_label = None

        if icon:
            self.set_icon(icon)

        self.text_label = QLabel(name)
        if self.tree_type == "folder":
            self.setStyleSheet(f"""
                    QLabel {{
                        font-size: 16px;
                        border-radius: 5px;
                        padding: 2px;
                    }}
                    QLabel:hover {{
                        background-color: {Colors.light_blue};
                    }}""")
        else:
            self.setStyleSheet(f"""
                    QWidget {{
                        font-size: 14px;
                        border-radius: 5px;
                        background-color: {Colors.light_blue};
                        padding: 3px;
                        border: 1px solid black;
                    }}
                    QWidget:hover {{
                        background-color: {Colors.light_gray};
                    }}""")

        self.main_layout.addWidget(self.text_label)
        self.tag_layout = QHBoxLayout()
        self.main_layout.addLayout(self.tag_layout)

    def set_icon(self, icon: QIcon):
        if self.icon_label:
            self.main_layout.removeWidget(self.icon_label)
            self.icon_label.deleteLater()
        self.icon_label = QLabel()
        # self.icon_label.setIcon(icon)
        self.icon_label.setPixmap(icon.pixmap(25, 25))
        self.main_layout.insertWidget(0, self.icon_label)


class FolderViewer(QTreeWidget):
    def __init__(self, project: Project):
        super().__init__()
        self.project = project
        self.setHeaderHidden(True)
        self.path = None
        self.project.projectLoaded.connect(self.populate_tree)
        self.project.projectLoaded.connect(self.tag_nodes_on_project_load)
        self.project.corpusConfigUpdated.connect(self.tag_nodes)
        self.folder_icon = Icons.folder_closed()
        self.file_icon = Icons.file()
        self.file_checked_icon = Icons.file_checked()
        self.action_ref = ActionRef(self.project, "FolderViewer")
        self.setStyleSheet("""
            QTreeWidget::item {
                margin-left: -30px;
            }
            QHeaderView {
                font-size: 16px;
            }
        """)

        self.populate_tree()

    def populate_tree(self, path: Path | None = None):
        self.clear()
        path = path or self.project.corpus_config.corpus_path
        if path:
            self.path = path
            self.setHeaderLabel(path.__str__())
            self.setHeaderHidden(False)
            self.add_node(self, path)
        self.expandAll()

    def add_node(self, parent, path: Path):
        for node_path in path.iterdir():
            node_name = node_path.name

            icon = self.folder_icon if node_path.is_dir() else self.file_icon
            widget = TreeNode(node_name, icon)
            tree_item = QTreeWidgetItem(parent)
            self.setItemWidget(tree_item, 0, widget)

            tree_item.setData(0, 1, node_path)

            if node_path.is_dir():
                self.add_node(tree_item, node_path)

    # def tag_nodes_on_project_load(self):
    #     for setting in self.project.settings["corpus"].values():
    #         if setting.type not in ("folder", "ext"):
    #             continue
    #         update_dict = {"setting_name": setting.name, "update": setting.value}
    #         self.tag_nodes(update_dict)

    def set_icon_on_tree_node(self, icon: QIcon, tree_node: TreeNode) -> None:
        tree_node.set_icon(icon)

    def tag_nodes_on_project_load(self):
        qDebug("loading")
        self.tag_nodes(
            "included_extensions", self.project.corpus_config.get_extensions()
        )
        self.tag_nodes("subfolders", self.project.corpus_config.get_subfolders())

    def tag_nodes(self, prop_name, content, remove: bool = False):
        content = content if type(content) is list else [content]

        if prop_name == "included_extensions":
            if remove:
                targets = content

                def action_func(_: Any, tree_node_widget: TreeNode) -> None:  # type: ignore
                    tree_node_widget.set_icon(self.file_icon)
            else:
                targets = [item.name for item in content]

                def action_func(_: Any, tree_node_widget: TreeNode) -> None:  # type: ignore
                    tree_node_widget.set_icon(self.file_checked_icon)

            def filter_func(node: QTreeWidgetItem):  # type: ignore
                path = node.data(0, 1)
                return path and path.is_file() and path.suffix in targets

        elif prop_name == "subfolders":
            targets = content
            if remove:

                def action_func(_: Any, tree_node_widget: TreeNode):  # type: ignore
                    tree_node_widget.text_label.setStyleSheet("background-color: none;")
            else:

                def action_func(target: Folder, tree_node_widget: TreeNode):
                    # node_widget: TreeNode = self.itemWidget(node, 0)
                    tree_node_widget.text_label.setStyleSheet(
                        f"background-color: rgb{target.color};"
                    )

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
        tree_node_widget: TreeNode = self.itemWidget(node, 0)  # type: ignore
        if target := filter_func(node):
            action_func(target, tree_node_widget)

        for i in range(node.childCount()):  # Iterate through child items
            self.tag_nodes_inner(node.child(i), filter_func, action_func)


class DocViewer(QTreeWidget):
    def __init__(self, project: Project):
        super().__init__()
        self.project = project
        self.file_type = None
        self.setHeaderHidden(True)
        self.project.corpusSettingUpdated.connect(self.tag_nodes)
        self.action_ref = ActionRef(self.project, "DocViewer")
        self.setStyleSheet("""
            QTreeWidget::item {
                margin-left: -30px;
            }
            QHeaderView {
                font-size: 16px;
            }
        """)

    def display_file(self, filepath: Path):
        self.file_type = filepath.suffix
        self.context_menu.file_type = self.file_type  # type: ignore
        self.action_ref.file_type = self.file_type  # type: ignore

        content = filepath.open().read()
        filename = filepath.name
        if filepath.suffix == ".xml":
            try:
                tree_struct = ET.fromstring(content)
            except ET.ParseError as e:
                print(f"Error parsing XML: {e}")
        elif filepath.suffix == ".json":
            try:
                tree_struct = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
        else:
            # Need support for other file types
            return
        self.setHeaderLabel(filename)
        self.setHeaderHidden(False)
        self.populate_tree(tree_struct)
        self.tag_nodes_on_display()

    def populate_tree(self, data):
        """Recursively populate the tree widget with XML nodes or dictionary entries."""
        self.clear()
        if isinstance(data, ET.Element):
            self.add_node_to_tree(data, self)
        elif isinstance(data, dict):
            self.add_dict_to_tree(data, self)
        else:
            print("Unsupported data type for tree population.")
        self.expandAll()

    def add_node_to_tree(self, xml_node, parent_item):
        """Add XML node to the tree widget, including text and attributes."""
        # Prepare the display text for the node
        node_str = get_xml_node_str_from_xml_node(xml_node)
        node_text = xml_node.text.strip() if xml_node.text else ""
        widget = TreeNode(node_str, tree_type="doc")
        item = QTreeWidgetItem(parent_item)

        # Set the custom widget to the item
        self.setItemWidget(item, 0, widget)

        # Store the XML node in the item
        item.setData(0, 1, xml_node)

        if node_text:
            text_widget = DocText(node_text)
            text_item = QTreeWidgetItem(item)
            self.setItemWidget(text_item, 0, text_widget)
            text_item.setData(0, 1, node_text)

        for child in xml_node:
            self.add_node_to_tree(child, item)

    def add_dict_to_tree_old(self, dictionary, parent_item):
        """Add dictionary entries to the tree widget."""
        for key, value in dictionary.items():
            widget = TreeNode(key, tree_type="doc")

            item = QTreeWidgetItem(parent_item)
            # Set the custom widget to the item
            self.setItemWidget(item, 0, widget)

            item.setData(0, 1, key)  # Store the value in the item

            # Recursively add nested dictionaries or lists
            if isinstance(value, dict):
                self.add_dict_to_tree(value, item)
            elif isinstance(value, list):
                self.add_list_to_tree(value, item)
            else:
                text_widget = DocText(str(value))
                text_item = QTreeWidgetItem(item)
                self.setItemWidget(text_item, 0, text_widget)
                text_item.setData(0, 1, None)

    def add_dict_to_tree(self, dictionary, parent_item):
        """Add dictionary entries to the tree widget, but limit to the first 500 keys."""
        max_keys = 250  # Limit the number of keys to display
        keys_added = 0  # Counter for the keys added

        for key, value in dictionary.items():
            if keys_added >= max_keys:
                break  # Stop once we have added 500 keys

            widget = TreeNode(key, tree_type="doc")
            item = QTreeWidgetItem(parent_item)
            # Set the custom widget to the item
            self.setItemWidget(item, 0, widget)
            item.setData(0, 1, key)  # Store the value in the item

            # Recursively add nested dictionaries or lists
            if isinstance(value, dict):
                self.add_dict_to_tree(value, item)
            elif isinstance(value, list):
                self.add_list_to_tree(value, item)
            else:
                text_widget = DocText(str(value))
                text_item = QTreeWidgetItem(item)
                self.setItemWidget(text_item, 0, text_widget)
                text_item.setData(0, 1, None)

            keys_added += 1  # Increment the key counter

    def add_list_to_tree(self, lst, parent_item):
        """Add list entries to the tree widget."""
        for i, item_value in enumerate(lst):
            if isinstance(item_value, dict):
                self.add_dict_to_tree(item_value, parent_item)
            elif isinstance(item_value, list):
                self.add_list_to_tree(item_value, parent_item)
            else:
                text_widget = DocText(str(item_value), index=i)
                text_item = QTreeWidgetItem(parent_item)
                self.setItemWidget(text_item, 0, text_widget)
                text_item.setData(0, 1, None)

    def tag_nodes_on_display(self):
        for setting in self.project.settings["corpus"].values():
            if setting.type not in ("text", "meta"):
                continue
            update_dict = {"setting_name": setting.name, "update": setting.value}
            self.tag_nodes(update_dict)

    def tag_nodes(self, update_dict):
        if update_dict.get("remove_setting"):
            setting = update_dict["setting"]
        else:
            setting = self.project.get_setting("corpus", update_dict["setting_name"])
        if setting.type not in ("text", "meta"):
            return
        item_func = self.action_ref.setting_type_to_item_func.get(setting.type)
        if not item_func:
            return
        tag_text = setting.display_name.split()[0]
        color = setting.color
        target_str = update_dict["update"]
        remove = update_dict.get("remove")
        root = self.invisibleRootItem()

        update = update_dict["update"]
        if type(update) is str:
            update = [update]
        for target_str in update:
            self.tag_nodes_inner(
                root,
                target_str,
                tag_text,
                color=color,
                item_func=item_func,
                remove=remove,
            )

    def tag_nodes_inner(
        self,
        node,
        target_str: str,
        tag_text: str,
        color: str,
        item_func: Callable,
        remove: bool = False,
    ):
        widget: TreeNode | DocText = self.itemWidget(node, 0)  # type: ignore
        if type(widget) is TreeNode:
            item_str = item_func(node.data(0, 1))
            if item_str == target_str:
                if not remove:
                    widget.add_tag(tag_text, color)
                else:
                    widget.remove_tag(tag_text)

        elif type(widget) is DocText:
            pass

        # Recursively iterate through child items
        for i in range(node.childCount()):  # Iterate through child items
            self.tag_nodes_inner(
                node.child(i),
                target_str,
                tag_text,
                color=color,
                item_func=item_func,
                remove=remove,
            )


class DocText(QLabel):
    def __init__(self, text, index: int | None = None):
        super().__init__()
        self.setStyleSheet("""
            font-size: 14px;
            padding: 10px;
            margin-left: 10px;
                           """)
        label_text = text
        if type(index) is int:
            label_text = f"<b>[{index}]</b>\t{text}"
        self.setText(label_text)


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

    def add_actions(self, tree_item: QTreeWidgetItem):
        clear_layout(self.actions_layout)

        clicked_item = tree_item.data(0, 1)
        actions = []

        for prop_name in (
            "included_extensions",
            "subfolders",
            "text_labels",
            "meta_labels",
        ):
            menu_item = None
            menu_item_display_name = None
            remove = False

            if self.type == "folder":
                if clicked_item.is_file() and prop_name == "included_extensions":
                    menu_item = clicked_item.suffix
                    menu_item_display_name = menu_item

                elif clicked_item.is_dir() and prop_name == "subfolders":
                    self.add_multi_subfolder_action(clicked_item, actions)
                    menu_item = clicked_item
                    menu_item_display_name = clicked_item.name

            else:
                # Need to figure this out
                menu_item = clicked_item

            if menu_item:
                if menu_item in getattr(
                    self.project.corpus_config,
                    prop_name,  # type: ignore
                ):
                    remove = True
                    verb = ("Remove", "from")
                else:
                    verb = ("Add", "to")

                prop_display_name = self.project.corpus_config.get_display_name(
                    prop_name
                )
                text = f"{verb[0]} <b>{menu_item_display_name}</b> {verb[1]} {prop_display_name.lower()}"

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


class ActionRef:
    """
    Action reference for trees and context menus
    """

    def __init__(self, project: Project, parent_type: str) -> None:
        self.project = project
        self.setting_type_to_item_func = {
            "ext": self.get_suffix,
            "folder": self.return_if_is_dir,
            "text": self.process_doc_tree_item,
            "meta": self.process_doc_tree_item,
        }
        self.parent_type = parent_type
        if self.parent_type == "FolderViewer":
            self.relevant_setting_types = ["ext", "folder"]
            self.relevant_setting_names = [
                "included_exts",
                "ignored_exts",
                "subfolders",
            ]
        else:
            self.relevant_setting_types = ["text", "meta"]
            self.relevant_setting_names = ["default_text_category"]
        self.file_type = None

    def get_action_setups(self, unset_item: Any) -> list[dict[str, Callable]]:
        action_setups = []
        type_to_item_dict = {
            setting_type: item_func(unset_item)
            for setting_type, item_func in self.setting_type_to_item_func.items()
            if setting_type in self.relevant_setting_types
        }
        # Add / remove from setting actions
        for setting in self.project.settings["corpus"].values():
            if not setting.default:
                continue
            if setting.type not in self.relevant_setting_types:
                continue
            item = type_to_item_dict[setting.type]
            if not item:
                continue

            setting_text = setting.display_name
            if setting.type == "text" and setting.name != "default_text_category":
                setting_text = setting_text + " (text)"

            if item in setting.value:
                remove = True
                text = f"Remove <b>{item}</b> from <b>{setting_text}</b>"
            else:
                remove = False
                text = f"Add <b>{item}</b> to <b>{setting_text}</b>"

            def func(  # type: ignore
                _, setting_name=setting.name, update=item, remove=remove
            ):
                return self.project.update_setting(
                    "corpus", setting_name, update, remove
                )

            self.add_to_action_setups(text, func, action_setups)

        # Add / remove from subfolders actions
        if "folder" in self.relevant_setting_types:
            item = type_to_item_dict["folder"]
            if folder := item:
                subfolders = set(s for s in folder.iterdir() if s.is_dir())

                subfolders_to_add = subfolders.difference(
                    self.project.get_setting_value("corpus", "subfolders")
                )

                subfolders_to_remove = subfolders.intersection(
                    self.project.get_setting_value("corpus", "subfolders")
                )

                if subfolders_to_add:
                    text = f"Add subfolders of <b>{folder.name}</b> to Subfolders"

                    def func(  # type: ignore
                        _, subfolders=subfolders_to_add
                    ):
                        return self.add_or_remove_subfolders(subfolders)

                    self.add_to_action_setups(text, func, action_setups)

                if subfolders_to_remove:
                    text = f"Remove subfolders of <b>{folder.name}</b> from Subfolders"

                    def func(  # type: ignore
                        _, subfolders=subfolders_to_remove
                    ):
                        return self.add_or_remove_subfolders(subfolders, remove=True)

                    self.add_to_action_setups(text, func, action_setups)

        if self.parent_type == "DocViewer":
            for setting_type in ("text", "meta"):
                item = type_to_item_dict[setting_type]
                if not item:
                    continue
                text = f"Add <b>{item}</b> to new <b>{setting_type}</b> category"

                def func(
                    _,
                    update=item,
                    setting_type=setting_type,
                ):
                    return self.create_new_setting(update, setting_type)

                self.add_to_action_setups(text, func, action_setups)

        return action_setups

    def add_to_action_setups(
        self, text: str, func: Callable, action_setups: list[dict[str, Callable]]
    ) -> None:
        action_setup = {"text": text, "func": func}
        action_setups.append(action_setup)

    def process_doc_tree_item(self, item: Any) -> str | None:
        if self.file_type == ".xml":
            if type(item) is not ET.Element:
                return
            return get_xml_node_str_from_xml_node(item)
        else:
            return item

    def get_suffix(self, item: Path):
        if item.is_file():
            return item.suffix

    def return_if_is_dir(self, item: Path):
        if item.is_dir():
            return item

    def add_or_remove_subfolders(self, subfolders: set[Path], remove: bool = False):
        for subfolder in subfolders:
            if subfolder.is_dir():
                self.project.update_setting(
                    "corpus", "subfolders", subfolder, remove=remove
                )

    def show_xml_node_select_options(self, node_str: str):
        tag_name, xml_node_dict = parse_xml_node_str(node_str)
        dialog = XMLNodeSelectDialog(tag_name, xml_node_dict)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tag_name, attribute_values = dialog.get_attribute_value_pairs()
            # node_str = get_xml_node_str_from_tag_name_and_node_dict(tag_name)

    def create_new_setting(self, update: str, setting_type: str) -> None:
        dialog = AddSettingDialog(
            f"Add {setting_type} category", update, meta=setting_type == "meta"
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_results()
            setting_name = results["name"]
            color = results["color"]

            display_name = setting_name

            if setting_type == "meta":
                display_name = f'{display_name} ({results.get("meta_type")})'

            new_setting_attrs = {
                "display_name": display_name,
                "type": setting_type,
                "value": set(),
                "color": color,
                "meta_type": results.get("meta_type"),
                "value_type": "set",
                "tooltip": f"{setting_type} category <b>{setting_name}</b>",
            }
            self.project.update_setting(
                "corpus", setting_name, update, new_setting_attrs=new_setting_attrs
            )
