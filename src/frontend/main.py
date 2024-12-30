from PySide6.QtWidgets import QWidget, QTabWidget, QMainWindow

from frontend.project import ProjectWrapper
from frontend.tabs.config_corpus import CorpusConfigTab
from frontend.widgets.menu_bar import MenuBar
from frontend.styles.colors import Colors


class MainWindow(QMainWindow):
    def __init__(self, project: ProjectWrapper):
        super().__init__()
        self.project = project
        self.setWindowTitle("Corpus Analysis")
        self.setMinimumHeight(1000)
        central_widget = MainTabWidget(self.project)
        self.setCentralWidget(central_widget)
        self.setMenuBar(MenuBar(self, self.project))


class MainTabWidget(QTabWidget):
    def __init__(self, project: ProjectWrapper) -> None:
        super().__init__()
        self.project = project
        # Tabs
        corpus_config_tab = CorpusConfigTab(self.project)
        corpus_config_tab.tabChange.connect(self.tab_change)

        self.tabs_dict = {
            "Configure Corpus": corpus_config_tab,
            "Overview": QWidget(),
            "Basic Analysis": QWidget(),
            "Plot": QWidget(),
            "Search": QWidget(),
        }
        self.setStyleSheet(f"""

            QTabBar::tab {{
                background-color: white;
                font-size: 17px;
                padding: 10px;
                margin-top: 10px;
            }}
            QTabBar::tab:!selected {{
                background-color: {Colors.light_gray};
            }}
            QTabBar::tab:!selected:hover {{
                background-color: {Colors.light_blue};
            }}

        """)

        for tab_name, widget in self.tabs_dict.items():
            self.addTab(widget, tab_name)
        self.tabBar().setCurrentIndex(0)

    def tab_change(self, index: int) -> None:
        self.tabBar().setCurrentIndex(index)
