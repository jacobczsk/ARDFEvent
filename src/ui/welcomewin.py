from datetime import datetime
from pathlib import Path

import sqlalchemy
from PySide6.QtWidgets import (
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import api
import models


class WelcomeWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        lay = QVBoxLayout()
        self.setLayout(lay)

        lay.addWidget(QLabel("Vítejte v aplikaci ARDFEvent!"))

        new_btn = QPushButton("Nový závod")
        new_btn.clicked.connect(self._new_race)
        lay.addWidget(new_btn)

        self.races_list = QListWidget()
        self.races_list.itemDoubleClicked.connect(self._open_race)
        lay.addWidget(self.races_list)

        self.races = []

        for file in (Path.home() / ".ardfevent").glob("*.sqlite"):
            try:
                self.db = sqlalchemy.create_engine(
                    f"sqlite:///{file}", max_overflow=-1
                )

                title = f"{datetime.fromisoformat(api.get_basic_info(self.db)["date_tzero"]).strftime('%d.%m.%Y %H:%M')} - {api.get_basic_info(self.db)["name"]} ({file.name})"
                self.races.append((title, file))

                self.races_list.addItem(QListWidgetItem(title))
            except:
                ...

    def _new_race(self):
        title, ok = QInputDialog.getText(self, "Nový závod", "Zadejte název závodu")
        if ok and title:
            file = Path.home() / ".ardfevent" / f"{title}.sqlite"
            if not file.exists():
                open(file, "w+").close()

            self.db = sqlalchemy.create_engine(f"sqlite:///{file}/", max_overflow=-1)
            models.Base.metadata.create_all(self.db)

            self.mw.show(file)
            self.close()
        else:
            return

    def _open_race(self, item: QListWidgetItem):
        for title, file in self.races:
            if item.text() == title:
                self.mw.show(file)
                self.close()
                break
