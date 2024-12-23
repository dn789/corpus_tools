from PySide6.QtWidgets import QApplication, QStyle


def get_folder_open_icon():
    return QApplication.style().standardIcon(  # type: ignore
        QStyle.StandardPixmap.SP_DirOpenIcon
    )


def get_folder_closed_icon():
    return QApplication.style().standardIcon(  # type: ignore
        QStyle.StandardPixmap.SP_DirClosedIcon
    )


def get_file_icon():
    return QApplication.style().standardIcon(  # type: ignore
        QStyle.StandardPixmap.SP_FileIcon
    )
