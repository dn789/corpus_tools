from backend.utils.paths import DEFAULT_CONFIG_PATH
from frontend.project import ProjectWrapper


def load_project() -> ProjectWrapper:
    project = ProjectWrapper(DEFAULT_CONFIG_PATH)
    return project
