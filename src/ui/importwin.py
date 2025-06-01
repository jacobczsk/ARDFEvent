import csv

from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import Delete, Select
from sqlalchemy.orm import Session

import api
import import_runners
from models import Category, Runner


class ImportWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        lay = QVBoxLayout()
        self.setLayout(lay)

        file_btn = QPushButton("Vyberte soubor (.csv)")
        file_btn.clicked.connect(self._select_file)
        lay.addWidget(file_btn)

        lay.addWidget(
            QLabel(
                'Soubor musí obsahovat hlavičku "Jméno;Registrace;SI;Kategorie", podle toho se musí řídit další sloupce.'
            )
        )
        lay.addWidget(QLabel("Pro import z ROBis využijte okno ROBis!"))

        self.log = QTextBrowser()
        lay.addWidget(self.log)

    def _select_file(self):
        file = QFileDialog.getOpenFileName(self, "Import CSV", filter="CSV (*.csv)")

        with open(file[0], "r") as f:
            reader = csv.reader(f, delimiter=";")
            data = list(reader)[1:]
            self.log.append(f"Načten soubor {file[0]}. Počet závodníků: {len(data)}.")

        clubs = api.get_clubs()

        runners = []

        for runner in data:
            runners.append(
                import_runners.RunnerToImport(
                    name=runner[0],
                    reg=runner[1],
                    si=int(runner[2]),
                    category_name=runner[3],
                    call="",
                )
            )

        for code, runner in import_runners.import_runners(self.mw.db, runners, clubs):
            match code:
                case 0:
                    self.log.append(
                        f"OK: Závodník {runner.name} byl úspěšně importován."
                    )
                case 1:
                    self.log.append(
                        f"/!\\ WAR: Závodník {runner.name} s registračním číslem {runner.reg} již existuje! Přepisuje se."
                    )
                case 2:
                    self.log.append(
                        f"/!\\ WAR: Pro závodníka {runner.name} nebyla nalezena kategorie {runner.category_name}! Kategorie vytvořena."
                    )
                case 3:
                    self.log.append(
                        f"/!\\ WAR: Závodník {runner.name} nemá platný klub {runner.reg[:3]}. Přesto se importuje."
                    )

    def _show(self):
        self.log.setPlainText("")
