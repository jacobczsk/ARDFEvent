from datetime import datetime
from pathlib import Path

import sqlalchemy
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
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

        self.setWindowTitle("JJ ARDFEvent")

        lay = QVBoxLayout()
        self.setLayout(lay)

        img_lbl = QLabel()
        img_lbl.setPixmap(QPixmap(":/icons/logo.png"))
        lay.addWidget(img_lbl)

        new_btn = QPushButton("Nový závod")
        new_btn.clicked.connect(self._new_race)
        lay.addWidget(new_btn)

        del_btn = QPushButton("Smazat závod")
        del_btn.clicked.connect(self._delete)
        lay.addWidget(del_btn)

        self.races_list = QListWidget()
        self.races_list.itemDoubleClicked.connect(self._open_race)
        lay.addWidget(self.races_list)

        self._load_races()

    def _load_races(self):
        self.races_list.clear()

        self.races = []

        for file in (Path.home() / ".ardfevent").glob("*.sqlite"):
            try:
                self.db = sqlalchemy.create_engine(f"sqlite:///{file}", max_overflow=-1)

                title = f"{datetime.fromisoformat(api.get_basic_info(self.db)["date_tzero"]).strftime('%d.%m.%Y %H:%M')} - {api.get_basic_info(self.db)["name"]} ({file.name})"
                self.races.append((title, file))

                self.races_list.addItem(QListWidgetItem(title))
            except:
                ...

    def _new_race(self):
        title, ok = QInputDialog.getText(self, "Nový závod", "Zadejte ID závodu")
        if ok and title:
            file = Path.home() / ".ardfevent" / f"{title}.sqlite"
            if not file.exists():
                open(file, "w+").close()

            self.db = sqlalchemy.create_engine(f"sqlite:///{file}/", max_overflow=-1)
            models.Base.metadata.create_all(self.db)
            api.set_basic_info(
                self.db,
                {
                    "name": title,
                    "date_tzero": datetime.now().isoformat(),
                    "band": "2m",
                    "limit": 0,
                },
            )

            self.mw.show(file)
            self.close()
        else:
            return

    def _delete(self):
        item = self.races_list.currentItem()
        if not item:
            return
        if (
            QMessageBox.critical(
                self,
                "Smazat závod",
                f"Opravdu chcete smazat závod {item.text()}?",
                QMessageBox.Yes | QMessageBox.No,
            )
            == QMessageBox.Yes
        ):
            for title, file in self.races:
                if item.text() == title:
                    file.unlink()
                    self._load_races()
                    break

    def _open_race(self, item: QListWidgetItem):
        for title, file in self.races:
            if item.text() == title:
                self.mw.show(file)
                self.close()
                break
