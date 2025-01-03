from typing import Any, Callable
from PySide6.QtCore import QThread, Qt, Signal, qDebug
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from backend.utils.functions import get_default_func_args
from frontend.project import ProjectWrapper as Project
from frontend.utils.functions import clear_layout
from frontend.widgets.corpus_selection import CorpusSelectionWidget
from frontend.widgets.layouts import HScrollSection, MainColumn, VSplitter
from frontend.widgets.progress import ProgressBackend, ProgressWidget
from frontend.widgets.small import (
    Button,
    CheckBox,
    LargeHeading,
    MediumHeading,
    NumberEntryWidget,
)
from backend.tasks.basic_analysis import TASK_DICT
from frontend.widgets.tables import ResultsTabWidget


class TaskThread(QThread):
    taskInfo = Signal(str, int)
    increment = Signal()
    results = Signal(dict)
    complete = Signal()

    def __init__(
        self,
        project: Project,
        tasks_dict: dict[str, Any],
        selections: list[dict[str, Any]],
    ):
        super().__init__()
        self.project = project
        self.tasks_dict = tasks_dict
        self.selections = selections
        self.progress_backend = ProgressBackend()
        self.progress_backend.taskInfo.connect(self.taskInfo)

    def run(self):
        sent_dicts_l = []
        for selection in self.selections:
            sent_dicts = self.project.corpus_query(selection)["sent_dicts"]
            sent_dicts_l.append(sent_dicts)

        count = 0
        for task_name, task_dict in self.tasks_dict.items():
            if class_ := task_dict.get("class"):
                obj = class_()

                def func(sent_dicts):
                    return task_dict["func"](
                        obj,
                        sent_dicts,
                        **task_dict["args"],
                        frontend_connect=self.progress_backend,
                    )
            else:

                def func(sent_dicts):
                    return task_dict["func"](
                        sent_dicts,
                        **task_dict["args"],
                        frontend_connect=self.progress_backend,
                    )

            for sent_dicts in sent_dicts_l:
                results = func(sent_dicts)
                qDebug(str(results))
                with open(f"{count}.txt", "w") as f:
                    if type(results) is list:
                        f.write("\n".join(str(x) for x in results))
                    else:
                        f.write(str(results))
                count += 1

        self.complete.emit()


class BasicAnalysisWidget(QWidget):
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
        self.task_widget = TaskWidget(self.project, self.start_task_thread)
        left_splitter.add_widget("Tasks", self.task_widget)

    def get_selections(self):
        selections = self.corpus_selection_widget.get_selections()
        return selections

    def start_task_thread(self):
        self.task_widget.progress_widget.show()
        self.task_widget.tasks_button.setDisabled(True)
        tasks_dict = self.task_widget.get_tasks()
        selections = self.get_selections()
        self.task_thread = TaskThread(self.project, tasks_dict, selections)
        self.task_thread.taskInfo.connect(self.task_widget.progress_widget.load_task)
        self.task_thread.complete.connect(self.reset)
        self.task_thread.start()

    def reset(self):
        self.task_thread.quit()
        self.task_widget.progress_widget.hide()
        self.task_widget.tasks_button.setEnabled(True)


class TaskWidget(MainColumn):
    def __init__(self, project: Project, task_handle: Callable):
        super().__init__()
        self.corpus_selection_made = False
        self.tasks_selected = False
        self.task_handle = task_handle
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.task_ref = {}
        for task_name, task_d in TASK_DICT.items():
            task_d["args"] = get_default_func_args(task_d["func"])
            widget = TaskDisplay(task_name, task_d)
            widget.toggleCheck.connect(self.toggle_tasks_button)
            self.task_ref[task_name] = widget
            self.add_widget(widget)

        self.tasks_button = Button("Run Tasks", self.task_handle, font_size=18)
        self.tasks_button.setDisabled(True)
        self.button_layout = QHBoxLayout()
        self.button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.button_layout.setContentsMargins(10, 0, 0, 0)
        self.button_layout.addWidget(self.tasks_button)
        self.content_layout.addLayout(self.button_layout)
        self.progress_widget = ProgressWidget()
        self.progress_widget.hide()
        self.add_widget(self.progress_widget)

    def toggle_tasks_button(self):
        if any(widget.checkbox.is_checked() for widget in self.task_ref.values()):
            self.tasks_button.setEnabled(True)
        else:
            self.tasks_button.setDisabled(True)

    def get_tasks(self) -> dict[str, Any]:
        tasks_dict = {}
        for task_name, task_widget in self.task_ref.items():
            if task_widget.checkbox.is_checked():
                tasks_dict[task_name] = task_widget.get_task_d()
        return tasks_dict


class TaskDisplay(HScrollSection):
    toggleCheck = Signal()

    def __init__(self, heading_text: str, task_d: dict[str, Any]) -> None:
        super().__init__(heading_text, {}, show_content_count=False)
        clear_layout(self.heading_layout)
        self.checkbox = CheckBox(
            MediumHeading(heading_text), connection=self.toggle_select
        )
        self.heading_layout.addWidget(self.checkbox)
        self.content_layout.setSpacing(30)
        self.scroll_wrapper.hide()
        self.task_d = task_d
        d = {}
        for arg_name, value in task_d["args"].items():
            if type(value) is bool:
                d[arg_name] = CheckBox((arg_name))
                if value:
                    d[arg_name].check()
            elif isinstance(value, (int, float)):
                d[arg_name] = NumberEntryWidget(arg_name, default=value)
        self.add_content(d)

    def toggle_select(self) -> None:
        if self.checkbox.is_checked():
            self.scroll_wrapper.show()
        else:
            self.scroll_wrapper.hide()
        self.toggleCheck.emit()

    def get_task_d(self):
        args = {}
        for arg, widget in self.content_ref.items():
            if type(widget) is CheckBox:
                value = True if widget.is_checked() else False
            elif type(widget) is NumberEntryWidget:
                value = widget.get_value()
            args[arg] = value
        self.task_d["args"] = args
        return self.task_d
