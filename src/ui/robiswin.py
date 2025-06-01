from datetime import datetime

import requests
from dateutil.parser import parser
from PySide6.QtWidgets import (
    QFormLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextBrowser,
    QWidget,
)
from sqlalchemy import Delete, Select
from sqlalchemy.orm import Session

import api
from exports import json_results as res_json
from models import Category, Runner


class ROBisWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        lay = QFormLayout()
        self.setLayout(lay)

        self.api_edit = QLineEdit()
        lay.addRow("API klíč", self.api_edit)

        self.id_edit = QSpinBox()
        self.id_edit.setRange(0, 10000)
        lay.addRow("ID soutěže", self.id_edit)

        self.etap_edit = QSpinBox()
        self.etap_edit.setRange(0, 10000)
        lay.addRow("Číslo etapy (EX)", self.etap_edit)

        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self._on_ok)
        lay.addRow(self.ok_btn)

        lay.addRow(QLabel(""))

        self.download_btn = QPushButton(
            "Stáhnout přihlášky, kategorie - Pozor! Tato akce smaže všechny stávající kategorie a závodníky!"
        )
        self.download_btn.clicked.connect(self._download)
        lay.addRow(self.download_btn)

        self.upload_btn = QPushButton("Nahrát výsledky")
        self.upload_btn.clicked.connect(self._upload)
        lay.addRow(self.upload_btn)

        lay.addRow(QLabel(""))

        self.log = QTextBrowser()
        lay.addWidget(self.log)

    def _on_ok(self):
        api.set_basic_info(
            self.mw.db,
            {
                "robis_api": self.api_edit.text(),
                "robis_id": self.id_edit.text(),
                "robis_etap": self.etap_edit.text(),
            },
        )

    def _show(self):
        basic_info = api.get_basic_info(self.mw.db)
        self.api_edit.setText(basic_info["robis_api"])
        self.id_edit.setValue(int(basic_info["robis_id"]))
        self.etap_edit.setValue(int(basic_info["robis_etap"]))

    def _upload(self):
        response = requests.post(
            "https://rob-is.cz/api/results/?valid=True",
            res_json.export(self.mw.db),
            headers={
                "Race-Api-Key": self.api_edit.text(),
                "Content-Type": "application/json",
            },
        )

        QMessageBox.information(
            self, "Stav nahrání", f"{response.status_code} {response.text}"
        )

    def _download(self):
        response = requests.get(
            f"https://rob-is.cz/api/?type=json&name=event&event_id={self.id_edit.value()}",
            headers={"Race-Api-Key": self.api_edit.text()},
            cookies={
                "authToken": QInputDialog.getText(
                    self,
                    "Přihlášení",
                    "Zadejte autentizační token (cookie authToken v prohlížeči)",
                )[0]
            },
        )
        if response.status_code != 200:
            QMessageBox.critical(
                self,
                "Chyba",
                f"Stahování se nezdařilo: {response.status_code} {response.text}",
            )
            return
        props = response.json()["properties"]
        race = props["races"][self.etap_edit.value() - 1]

        limit_str = race["race_time_limit"].split(":")
        limit = int(limit_str[0]) * 60 + int(limit_str[1])

        api.set_basic_info(
            self.mw.db,
            {
                "name": props["event_name"] + " - " + race["race_name"],
                "date_tzero": parser().parse(race["race_start"]).isoformat(),
                "organizer": props["event_organiser"],
                "limit": limit,
                "band": api.BANDS[["M2", "M80", "COMBINED"].index(race["race_band"])],
            },
        )

        sess = Session(self.mw.db)
        sess.execute(Delete(Category))
        sess.execute(Delete(Runner))
        sess.add_all(
            [
                Category(
                    name=cat["category_name"],
                    controls=[],
                )
                for cat in race["categories"]
            ]
        )

        for runner in race["competitors"]:
            sess.add(
                Runner(
                    name=runner["last_name"] + ", " + runner["first_name"],
                    club=runner["competitor_club"],
                    si=runner["si_number"] or 0,
                    reg=runner["competitor_index"],
                    category=sess.scalars(
                        Select(Category).where(
                            Category.name == runner["competitor_category"]
                        )
                    ).first(),
                    call="",
                )
            )
        sess.commit()
        sess.close()

        QMessageBox.information(self, "Stav stažení", "Stažení proběhlo úspěšně.")
