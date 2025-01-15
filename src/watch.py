"""Dev script for hot-reloading on save."""

import sys
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

TEST_FILE = "app.py"
# TEST_FILE = "test.py"


class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None

    def start_app(self):
        self.process = subprocess.Popen([sys.executable, TEST_FILE])

    def stop_app(self):
        if self.process:
            self.process.terminate()
            self.process.wait()

    def on_any_event(self, event):
        if event.event_type != "modified":
            return
        if event.src_path.endswith(".py"):  # type: ignore
            print(f"Change detected: {event.src_path}. Restarting app...")
            self.stop_app()
            self.start_app()


def monitor():
    event_handler = ChangeHandler()
    event_handler.start_app()

    observer = Observer()
    observer.schedule(event_handler, path="./", recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    monitor()
