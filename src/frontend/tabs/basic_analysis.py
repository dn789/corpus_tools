from PySide6.QtCore import QThread, Signal, qDebug
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from frontend.project import ProjectWrapper as Project
from frontend.widgets.corpus_selection import CorpusSelectionWidget


class TaskThread(QThread):
    task_started = Signal(str)
    task_finished = Signal(dict)
    thread_complete = Signal()

    def __init__(self, task_queue: list[dict]):
        super().__init__()
        self.queue = task_queue

    def run(self):
        for i, task in enumerate(self.queue):
            exception = ""
            self.task_started.emit(task["type"])
            try:
                results = task["task"](task["sents"], **task["kwargs"])
            except Exception as e:
                exception = repr(e)
                results = None
            self.task_finished.emit(
                {
                    "type": task["type"],
                    "header": task["header"],
                    "results": results,
                    "index": i,
                    "exception": exception,
                }
            )
        self.thread_complete.emit()


class BasicAnalysisWidget(QWidget):
    def __init__(self, project: Project):
        super().__init__()
        self.project = project
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        right_layout.addWidget(QWidget())
        self.corpus_selection_widget = CorpusSelectionWidget(self.project)
        left_layout.addWidget(self.corpus_selection_widget)

    def get_selections(self):
        selections = self.corpus_selection_widget.get_selections()
        # for selection in selections:
        # qDebug("----------------\n")
        # qDebug(str(selection))
        # qDebug("\n----------------\n")
        return selections
