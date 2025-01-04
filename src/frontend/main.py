from PySide6.QtWidgets import QWidget, QTabWidget, QMainWindow

from frontend.project import ProjectWrapper
from frontend.tabs.basic_analysis import BasicAnalysisWidget
from frontend.tabs.config_corpus import CorpusConfigTab
from frontend.tabs.overview import Overview
from frontend.widgets.menu_bar import MenuBar
from frontend.styles.colors import Colors


class MainWindow(QMainWindow):
    def __init__(self, project: ProjectWrapper):
        super().__init__()
        self.project = project
        self.setWindowTitle("Corpus Analysis")
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
            "Configure": corpus_config_tab,
            "Overview": Overview(self.project),
            "Analyze": BasicAnalysisWidget(self.project),
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
        self.tabBar().setCurrentIndex(2)

    def tab_change(self, index: int) -> None:
        self.tabBar().setCurrentIndex(index)
