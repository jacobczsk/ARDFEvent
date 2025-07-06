import threading
from pathlib import Path

from PySide6.QtWidgets import QApplication

import registration
import ui.mainwin as mainwin

if __name__ == "__main__":
    rootdir = Path.home() / ".ardfevent"

    if not rootdir.exists():
        rootdir.mkdir()

    t = threading.Thread(target=registration.download)
    t.start()

    app = QApplication()
    win = mainwin.MainWindow()

    app.exec()
