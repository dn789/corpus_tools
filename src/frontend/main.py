from PySide6.QtWidgets import QWidget, QTabWidget, QMainWindow

# from frontend.tabs.config_corpus.config_corpus import ConfigCorpus
# from frontend.tabs.basic_analysis.basic_analysis import BasicAnalysis
# from frontend.tabs.search.search import SearchWidget
# from frontend.tabs.plot.plot import PlotWidget
from frontend.project import ProjectWrapper
from frontend.tabs.config_corpus import CorpusConfigTab
from frontend.widgets.menu_bar import MenuBar
from frontend.styles.colors import Colors
# from frontend.startup import load_project


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
        # self.tabs_dict = {
        #     "Configure Corpus": ConfigCorpus(self.project),
        #     "Basic Analysis": BasicAnalysis(self.project),
        #     "Plot": PlotWidget(self.project),
        #     "Search": SearchWidget(self.project),
        # }
        self.tabs_dict = {
            "Configure Corpus": CorpusConfigTab(self.project),
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
