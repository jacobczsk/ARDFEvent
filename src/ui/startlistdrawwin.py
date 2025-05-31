import random
import time
from datetime import timedelta

from dateutil.parser import parser
from PySide6.QtWidgets import QDateTimeEdit, QFormLayout, QPushButton, QSpinBox, QWidget
from sqlalchemy import Select
from sqlalchemy.orm import Session

import api
from models import Category, Runner


class StartlistDrawWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        self.mainlay = QFormLayout()
        self.setLayout(self.mainlay)
        self.setWindowTitle("Startovní listina")

        self.base_interval_edit = QSpinBox()
        self.mainlay.addRow("Startovní interval", self.base_interval_edit)

        self.draw_btn = QPushButton("Losovat!")
        self.draw_btn.clicked.connect(self._draw)
        self.mainlay.addRow(self.draw_btn)

        self.edits = {}

    def show(self):
        super().show()

        for edit in self.edits.values():
            self.mainlay.removeRow(edit)

        sess = Session(self.mw.db)

        zero = parser().parse(api.get_basic_info(self.mw.db)["date_tzero"])

        categories = sess.scalars(Select(Category)).all()

        for cat in categories:
            cat_edit = QDateTimeEdit()
            cat_edit.setDateTime(zero)

            self.mainlay.addRow(cat.name, cat_edit)
            self.edits[cat.name] = cat_edit

        sess.close()

    def _draw(self):
        baseint_delta = timedelta(seconds=self.base_interval_edit.value() * 60)
        sess = Session(self.mw.db)
        for cat_name in self.edits.keys():
            cat = sess.scalars(
                Select(Category).where(Category.name == cat_name)
            ).first()
            runners = list(
                sess.scalars(Select(Runner).where(Runner.category == cat)).all()
            )

            random.shuffle(runners)

            cat_zero = self.edits[cat_name].dateTime().toPython()

            for i, runner in enumerate(runners):
                runner.startlist_time = cat_zero + baseint_delta * i

        sess.commit()
        sess.close()
