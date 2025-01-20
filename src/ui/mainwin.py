import asyncio
import sys
from pathlib import Path

import requests
import sqlalchemy
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QInputDialog,
    QGridLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import models
import ui.resources
from ui import (
    basicinfowin,
    categorieswin,
    controlswin,
    importwin,
    readoutwin,
    resultswin,
    runnerwin,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        name, ok_name = QInputDialog.getText(
            self, "ARDFEvent", "Zadej název závodu", QLineEdit.Normal, ""
        )
        self.fn = Path.home() / f".ardf/{name}.sqlite"

        self.controls_win = controlswin.ControlsWindow(self)
        if not (ok_name and self.fn):
            QMessageBox.critical(self, "ARDFEvent", "Zadejte cestu")
            sys.exit(255)

        if not self.fn.exists():
            if (
                QMessageBox.information(
                    self, "ARDFEvent", "Cesta neexistuje, vytváří se nový"
                )
                == QMessageBox.StandardButton.Ok
            ):
                open(self.fn, "w+").close()

        self.db = sqlalchemy.create_engine(f"sqlite:////{self.fn.absolute()}/")
        models.Base.metadata.create_all(self.db)

        self.basicinfo_win = basicinfowin.BasicInfoWindow(self)
        self.controls_win = controlswin.ControlsWindow(self)
        self.categories_win = categorieswin.CategoriesWindow(self)
        self.import_win = importwin.ImportWindow(self)
        self.runners_win = runnerwin.RunnerWindow(self)
        self.readout_win = readoutwin.ReadoutWindow(self)
        self.results_win = resultswin.ResultsWindow(self)

        self.windows = [
            self.basicinfo_win,
            self.controls_win,
            self.categories_win,
            self.import_win,
            self.runners_win,
            self.readout_win,
            self.results_win,
        ]

        mainwid = QWidget()
        self.setCentralWidget(mainwid)

        lay = QGridLayout()
        mainwid.setLayout(lay)

        basicinfo_btn = QPushButton("Základní info")
        basicinfo_btn.setIcon(QIcon(":/icons/gear.png"))
        basicinfo_btn.clicked.connect(self.basicinfo_win.show)
        lay.addWidget(basicinfo_btn, 0, 0)

        controls_btn = QPushButton("Kontroly")
        controls_btn.setIcon(QIcon(":/icons/tx.png"))
        controls_btn.clicked.connect(self.controls_win.show)
        lay.addWidget(controls_btn, 0, 1)

        categories_btn = QPushButton("Kategorie")
        categories_btn.setIcon(QIcon(":/icons/categories.png"))
        categories_btn.clicked.connect(self.categories_win.show)
        lay.addWidget(categories_btn, 0, 2)

        import_btn = QPushButton("Import")
        import_btn.setIcon(QIcon(":/icons/import.png"))
        import_btn.clicked.connect(self.import_win.show)
        lay.addWidget(import_btn, 1, 0)

        runners_btn = QPushButton("Běžci")
        runners_btn.setIcon(QIcon(":/icons/runners.png"))
        runners_btn.clicked.connect(self.runners_win.show)
        lay.addWidget(runners_btn, 1, 1)

        readout_btn = QPushButton("Vyčítání")
        readout_btn.setIcon(QIcon(":/icons/readout.png"))
        readout_btn.clicked.connect(self.readout_win.show)
        lay.addWidget(readout_btn, 1, 2)

        results_btn = QPushButton("Výsledky")
        results_btn.setIcon(QIcon(":/icons/results.png"))
        results_btn.clicked.connect(self.results_win.show)
        lay.addWidget(results_btn, 2, 0)

        lay.setColumnStretch(3, 1)
        lay.setRowStretch(3, 1)

        self.show()

    def closeEvent(self, event):
        super().closeEvent(event)
        for win in self.windows:
            win.close()
