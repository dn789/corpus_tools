from typing import Any, Callable
from PySide6.QtCore import QThread, Qt, Signal, qDebug
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from backend.tasks.plot import get_plot_values
from backend.corpus.items import MetaProperty
from frontend.project import ProjectWrapper as Project
from frontend.styles.colors import Colors
from frontend.utils.functions import clear_layout, get_widgets
from frontend.widgets.corpus_selection import CorpusSelectionWidget
from frontend.widgets.layouts import HScrollSection, MainColumn, VSplitter
from frontend.widgets.plot import ImageDisplayWidget, plot_graph
from frontend.widgets.progress import ProgressWidget
from frontend.widgets.small import (
    Button,
    CheckBox,
    CorpusLabel,
    ErrorDisplay,
    LargeHeading,
    RadioButton,
    RadioButtonWithWidget,
)
from frontend.widgets.tables import (
    ResultsTabWidget,
)


class TaskThread(QThread):
    taskInfo = Signal(str, int)
    complete = Signal(dict)

    def __init__(
        self,
        project: Project,
        plot_d: dict[str, Any],
    ):
        super().__init__()
        self.project = project
        self.plot_d = plot_d

    def run(self):
        sent_batches = {}
        if self.plot_d["x_type"] == "Subfolders":
            x_label = "Subfolder"
            for path in self.plot_d["x_values"]:
                sent_batches[path.name] = [
                    sd["sentence"]
                    for sd in self.project.db.get_sents_by_named_subfolder(path.name)[
                        "sent_dicts"
                    ]
                ]
        elif self.plot_d["x_type"] == "Text":
            x_label = "Text category"
            for text_cat_name in self.plot_d["x_values"]:
                sent_batches[text_cat_name] = [
                    sd["sentence"]
                    for sd in self.project.db.get_sents_by_text_category(text_cat_name)[
                        "sent_dicts"
                    ]
                ]
        elif self.plot_d["x_type"] == "Meta":
            label_name, name = self.plot_d["x_values"][0]
            x_label = f"{label_name}-{name}"
            query_result = self.project.db.get_all_sents()
            for sent_d in query_result["sent_dicts"]:  # type: ignore
                meta_props = query_result["meta_properties"][  # type: ignore
                    sent_d["file_path"].__str__()
                ]
                for meta_prop in meta_props:
                    if (
                        meta_prop["label_name"] == label_name
                        and meta_prop["name"] == name
                    ):
                        sent_batches.setdefault(meta_prop["value"], [])
                        sent_batches[meta_prop["value"]].append(sent_d["sentence"])
                        break
        try:
            plot_values = get_plot_values(sent_batches, self.plot_d)
            results = {
                "plot_values": plot_values,
                "x_label": x_label,
                "y_label": self.plot_d["y_per"],
                "title": f'{ self.plot_d["y_type"]}: "{self.plot_d["y_func"]}"',
                "y_type": self.plot_d["y_type"],
                "plot_type": self.plot_d["plot_type"],
            }
        except Exception as e:
            error_message = f"{type(e).__name__}: {str(e)}"
            results = {"error": error_message, "y_type": self.plot_d["y_type"]}
        self.complete.emit(results)


class PlotTab(QWidget):
    def __init__(self, project: Project):
        super().__init__()
        self.project = project
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_widget.setFixedWidth(475)
        left_splitter = VSplitter(orientation=Qt.Orientation.Vertical)
        right_layout = QVBoxLayout()
        left_layout.addWidget(left_splitter)
        main_layout.addWidget(left_widget)
        main_layout.addLayout(right_layout)
        right_layout.addWidget(LargeHeading("Results"))
        right_layout.setContentsMargins(10, 9, 10, 10)
        self.results = ResultsTabWidget()
        right_layout.addWidget(self.results)
        self.corpus_selection_widget = CorpusSelectionWidget(self.project)
        left_splitter.add_widget("Corpus Selection", self.corpus_selection_widget)
        self.plot_widget = PlotWidget(self.project, self.start_plot)
        left_splitter.add_widget("Plot", self.plot_widget)
        left_splitter.splitter_up()

    def start_plot(self):
        self.plot_widget.progress_widget.load_task("Working", 0)
        self.plot_widget.progress_widget.show()

        self.task_thread = TaskThread(self.project, self.plot_widget.plot_d)
        self.task_thread.complete.connect(self.on_task_complete)
        self.task_thread.start()

    def on_task_complete(self, results):
        if error := results.get("error"):
            self.results.add_tab(ErrorDisplay(error), results["y_type"])
        elif results:
            image = plot_graph(
                results["plot_values"],
                plot_type=results["plot_type"],
                title=results["title"],
                x_label=results["x_label"],
                y_label=results["y_label"],
            )
            plot_display_widget = ImageDisplayWidget(image)
            self.results.add_tab(plot_display_widget, results["y_type"])
        self.task_thread.quit()
        self.plot_widget.progress_widget.hide()
        # self.plot_widget.tasks_finished_label.show()
        self.plot_widget.plot_button.setEnabled(True)


class PlotWidget(MainColumn):
    def __init__(self, project: Project, task_handle: Callable):
        super().__init__()
        self.project = project
        self.project.projectLoaded.connect(self.on_project_load)
        self.project.corpusProcessed.connect(self.on_project_load)
        self.corpus_selection_made = False
        self.tasks_selected = False
        self.task_handle = task_handle
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.task_ref = {}
        self.plot_type_select = PlotTypeSelect()
        self.add_widget(self.plot_type_select)
        self.x_select = None
        self.x_select = XSelect(self.project, handle=self.toggle_plot_button)
        self.add_widget(self.x_select)
        self.y_select = None
        self.y_select = YSelect(self.project, handle=self.toggle_plot_button)
        self.add_widget(self.y_select)

        self.plot_button = Button("Plot", self.start_plot, font_size=18)
        self.plot_button.setDisabled(True)
        self.button_layout = QHBoxLayout()
        self.button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.button_layout.setContentsMargins(10, 0, 0, 0)
        self.button_layout.addWidget(self.plot_button)
        self.content_layout.addLayout(self.button_layout)
        self.progress_widget = ProgressWidget()
        self.progress_widget.setContentsMargins(30, 10, 10, 10)
        self.progress_widget.hide()
        self.add_widget(self.progress_widget)
        self.tasks_finished_label = QLabel("Tasks finished")
        self.tasks_finished_label.setStyleSheet(
            f"font-weight: bold; font-size: 26px; color: {Colors.green}"
        )
        self.tasks_finished_label.setContentsMargins(30, 10, 10, 10)
        self.tasks_finished_label.hide()
        self.add_widget(self.tasks_finished_label)
        self.toggle_plot_button()

    def on_project_load(self):
        self.x_select.initUI()  # type: ignore
        self.y_select.initUI()  # type: ignore

    def toggle_plot_button(self):
        toggle_on_x = False
        toggle_on_y = False
        if not hasattr(self, "plot_button"):
            return
        for d in self.x_select.ref.values():  # type: ignore
            if d["radio_button"].isChecked():
                if any(
                    item.is_checked()
                    for item in d["items_options"].content_ref.values()
                ):
                    toggle_on_x = True
                    break
        for d in self.y_select.ref.values():  # type: ignore
            if d["radio_button"].isChecked():
                if d["items_options"].entry_widget.text().strip():
                    toggle_on_y = True
                    break

        if toggle_on_x and toggle_on_y:
            self.plot_button.setEnabled(True)
        else:
            self.plot_button.setDisabled(True)

    def start_plot(self):
        self.plot_d = {
            "x_values": [],
            "y_func": [],
            "plot_type": self.plot_type_select.get_plot_type(),
        }
        for name, d in self.x_select.ref.items():  # type: ignore
            if d["radio_button"].isChecked():
                self.plot_d["x_type"] = name
                for item, checkbox in d["items_options"].content_ref.items():
                    if checkbox.is_checked():
                        self.plot_d["x_values"].append(item)
                break
        for name, d in self.y_select.ref.items():  # type: ignore
            if d["radio_button"].isChecked():
                self.plot_d["y_type"] = name
                self.plot_d["y_func"] = d["items_options"].entry_widget.text().strip()
                if d["items_options"].per_sentence.isChecked():
                    self.plot_d["y_per"] = "per sentence"  # type: ignore
                elif d["items_options"].per_word.isChecked():
                    self.plot_d["y_per"] = "per word"  # type: ignore
                else:
                    self.plot_d["y_per"] = "total"  # type: ignore

        self.task_handle()

    def get_tasks(self) -> dict[str, Any]:
        tasks_dict = {}
        for task_name, task_widget in self.task_ref.items():
            if task_widget.checkbox.is_checked():
                tasks_dict[task_name] = task_widget.get_task_d()
        return tasks_dict


class PlotTypeSelect(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        self.setLayout(layout)
        layout.addWidget(
            LargeHeading("Plot Type", font_style="italic"),
            alignment=Qt.AlignmentFlag.AlignLeading,
        )
        self.radio_layout = QHBoxLayout()
        self.radio_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(self.radio_layout)
        for plot_type in ("line", "bar"):
            radio_button = RadioButton(plot_type)
            if plot_type == "line":
                radio_button.setChecked(True)
            self.radio_layout.addWidget(radio_button)

    def get_plot_type(self):
        for widget in get_widgets(self.radio_layout):
            if widget.isChecked():  # type: ignore
                return widget.text()  # type: ignore


class XSelect(QWidget):
    def __init__(self, project: Project, handle: Callable):
        super().__init__()
        self.project = project
        self.ref = {}
        self.handle = handle
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 10, 10, 10)
        self.setLayout(self.main_layout)
        self.setFixedWidth(450)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        heading = LargeHeading(
            "X", font_style="italic", alignment=Qt.AlignmentFlag.AlignLeft
        )
        heading.setContentsMargins(10, 10, 10, 10)
        self.main_layout.addWidget(heading)
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self.content_layout)
        self.initUI()

    def initUI(self):
        self.ref = {}
        clear_layout(self.content_layout)
        x_choices_layout = QHBoxLayout()
        x_choices_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        x_choices_layout.setContentsMargins(10, 0, 10, 0)
        x_choices_layout.setSpacing(15)
        self.x_choices_items_widget = QStackedWidget()
        for i, (prop_name, items) in enumerate(
            (
                ("Subfolders", self.project.corpus_config.subfolders),
                ("Text", self.project.corpus_config.text_categories),
                ("Meta", self.project.corpus_config.get_meta_properties(as_dict=True)),
            )
        ):
            radio_button = RadioButton(prop_name, connection=self.on_radio_select)
            if not i:
                radio_button.setChecked(True)
            x_choices_layout.addWidget(radio_button)
            content = {}
            if prop_name == "Meta":
                button_group = QButtonGroup(self)
            for items_i, (name, item) in enumerate(items.items()):  # type: ignore
                if type(item) is MetaProperty:
                    label_name = "-".join(name)  # type: ignore
                else:
                    label_name = item.name
                corpus_label = CorpusLabel(label_name, item.color, id=name)  # type: ignore
                if prop_name == "Meta":
                    item_radio_button = RadioButtonWithWidget(
                        corpus_label, connection=self.handle
                    )
                    content[name] = item_radio_button
                    button_group.addButton(item_radio_button.radio_button)
                    if not items_i:
                        item_radio_button.radio_button.setChecked(True)
                else:
                    checkbox = CheckBox(corpus_label, connection=self.handle)
                    content[name] = checkbox
                    checkbox.check()
            items_options = HScrollSection(content=content)

            items_options.content_layout.setSpacing(15)
            self.x_choices_items_widget.addWidget(items_options)
            self.ref[prop_name] = {
                "radio_button": radio_button,
                "items_options": items_options,
            }

        self.x_choices_items_widget.setCurrentIndex(0)
        self.content_layout.addLayout(x_choices_layout)
        self.content_layout.addWidget(self.x_choices_items_widget)
        self.X_choices_group = QButtonGroup(x_choices_layout)
        self.X_choices_group.setExclusive(True)

    def on_radio_select(self):
        for entry in self.ref.values():
            if entry["radio_button"].isChecked():
                self.x_choices_items_widget.setCurrentWidget(entry["items_options"])
        self.handle()


class YSelect(QWidget):
    def __init__(self, project: Project, handle: Callable):
        super().__init__()
        self.project = project
        self.ref = {}
        self.handle = handle
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(10)
        self.setLayout(self.main_layout)
        self.setFixedWidth(450)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        heading = LargeHeading(
            "Y", font_style="italic", alignment=Qt.AlignmentFlag.AlignLeft
        )
        heading.setContentsMargins(0, 10, 10, 10)

        self.main_layout.addWidget(heading)
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self.content_layout)
        self.initUI()

    def initUI(self):
        self.ref = {}
        clear_layout(self.content_layout)
        self.y_choices_layout = QHBoxLayout()
        self.y_choices_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.y_choices_layout.setContentsMargins(10, 0, 10, 0)
        self.y_choices_layout.setSpacing(15)
        self.y_choices_items_widget = QStackedWidget()
        for i, (name, widget, tooltip) in enumerate(
            (
                (
                    "Misc",
                    QWidget(),
                    "Miscellaneous",
                ),
                (
                    "Regex",
                    YValueWidget("Regex", self.handle),
                    "Regular expression",
                ),
                (
                    "Python code",
                    YValueWidget("<i>lambda</i>  <b>sentence</b>", self.handle),
                    "Plot a custom variable",
                ),
            )
        ):
            radio_button = RadioButton(
                name, connection=self.on_radio_select, tooltip=tooltip
            )
            if not i:
                radio_button.setDisabled(True)
            elif i == 1:
                radio_button.setChecked(True)
            self.y_choices_layout.addWidget(radio_button)

            self.y_choices_items_widget.addWidget(widget)
            self.ref[name] = {
                "radio_button": radio_button,
                "items_options": widget,
            }

        self.y_choices_items_widget.setCurrentIndex(1)
        self.content_layout.addLayout(self.y_choices_layout)
        self.content_layout.addWidget(self.y_choices_items_widget)
        self.y_choices_group = QButtonGroup(self.y_choices_layout)
        self.y_choices_group.setExclusive(True)

    def on_radio_select(self):
        for entry in self.ref.values():
            if entry["radio_button"].isChecked():
                self.y_choices_items_widget.setCurrentWidget(entry["items_options"])
        self.handle()


class YValueWidget(QFrame):
    def __init__(self, label: str, handle: Callable):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.light_tan};
                border-radius: 5px;
                font-size: 18px;
                padding: 10px;
            }}
        """)
        # self.setFixedHeight(125)
        self.setFixedWidth(420)
        self.handle = handle
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        entry_layout = QHBoxLayout()
        # entry_layout.setContentsMargins(, 0, 0, 0)
        entry_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        entry_layout.addWidget(QLabel(label))
        self.entry_widget = QLineEdit()
        self.entry_widget.textChanged.connect(self.handle)
        self.entry_widget.setFixedHeight(30)
        self.entry_widget.setStyleSheet(
            "font-size: 18px; border: 1px solid black; border-radius: 5px; background-color: white;"
        )
        entry_layout.addWidget(self.entry_widget)
        # entry_layout.addStretch()
        main_layout.addLayout(entry_layout)
        radio_layout = QHBoxLayout()
        radio_layout.setContentsMargins(10, 0, 0, 0)
        main_layout.addLayout(radio_layout)
        self.per_sentence = RadioButton("per sentence")
        self.per_sentence.setChecked(True)
        self.per_word = RadioButton("per word")
        self.total = RadioButton("total")
        for r_b in (self.per_sentence, self.per_word, self.total):
            radio_layout.addWidget(r_b)
