import asyncio
import sys
from pathlib import Path

import requests
import sqlalchemy
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QGridLayout,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
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
    robiswin,
    runnerwin,
    startlistwin,
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

        self.db = sqlalchemy.create_engine(
            f"sqlite:////{self.fn.absolute()}/", max_overflow=-1
        )
        models.Base.metadata.create_all(self.db)

        self.setWindowTitle(f"ARDFEvent - {name}")

        self.basicinfo_win = basicinfowin.BasicInfoWindow(self)
        self.controls_win = controlswin.ControlsWindow(self)
        self.categories_win = categorieswin.CategoriesWindow(self)
        self.import_win = importwin.ImportWindow(self)
        self.runners_win = runnerwin.RunnerWindow(self)
        self.readout_win = readoutwin.ReadoutWindow(self)
        self.results_win = resultswin.ResultsWindow(self)
        self.startlist_win = startlistwin.StartlistWindow(self)
        self.robis_win = robiswin.ROBisWindow(self)

        self.windows = [
            self.basicinfo_win,
            self.controls_win,
            self.categories_win,
            self.import_win,
            self.runners_win,
            self.readout_win,
            self.results_win,
            self.startlist_win,
            self.robis_win,
        ]

        self.mainwid = QTabWidget()
        self.setCentralWidget(self.mainwid)
        self.mainwid.currentChanged.connect(self._on_tab_changed)

        self.mainwid.addTab(self.basicinfo_win, "Základní info")
        self.mainwid.setTabIcon(0, QIcon(":/icons/gear.png"))

        self.mainwid.addTab(self.controls_win, "Kontroly")
        self.mainwid.setTabIcon(1, QIcon(":/icons/tx.png"))

        self.mainwid.addTab(self.categories_win, "Kategorie")
        self.mainwid.setTabIcon(2, QIcon(":/icons/categories.png"))

        self.mainwid.addTab(self.import_win, "Import")
        self.mainwid.setTabIcon(3, QIcon(":/icons/import.png"))

        self.mainwid.addTab(self.runners_win, "Běžci")
        self.mainwid.setTabIcon(4, QIcon(":/icons/runners.png"))

        self.mainwid.addTab(self.readout_win, "Vyčítání")
        self.mainwid.setTabIcon(5, QIcon(":/icons/readout.png"))

        self.mainwid.addTab(self.startlist_win, "Startovka")
        # results_btn.setIcon(QIcon(":/icons/startlist.png"))

        self.mainwid.addTab(self.results_win, "Výsledky")
        self.mainwid.setTabIcon(7, QIcon(":/icons/results.png"))

        self.mainwid.addTab(self.robis_win, "ROBis")

        self.mainwid.setTabPosition(QTabWidget.TabPosition.North)

        self.showMaximized()

    def _on_tab_changed(self, index):
        self.mainwid.currentWidget()._show()

    def closeEvent(self, event):
        super().closeEvent(event)
        for win in self.windows:
            win.close()
