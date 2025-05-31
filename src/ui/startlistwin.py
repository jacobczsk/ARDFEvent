from datetime import timedelta

from PySide6.QtWidgets import (
    QFileDialog,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import Select
from sqlalchemy.orm import Session

import exports.pdf_results as res_pdf
import results
from models import Category


class StartlistWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        lay = QVBoxLayout()
        self.setLayout(lay)

        export_pdf_btn = QPushButton("Exportovat do PDF")
        export_pdf_btn.clicked.connect(self._export_pdf)
        lay.addWidget(export_pdf_btn)

        self.results_table = QTableWidget()
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.results_table)

    def _export_pdf(self):
        res_pdf.export(
            QFileDialog.getSaveFileName(
                self, "Export výsledků do PDF", selectedFilter=("PDF (*.pdf)")
            )[0],
            self.mw.db,
        )

    def _update_results(self):
        sess = Session(self.mw.db)
        categories = sess.scalars(Select(Category).order_by(Category.name.asc())).all()

        self.results_table.clear()
        self.results_table.setColumnCount(5)
        self.results_table.setRowCount(1000)

        row = 0

        for category in categories:
            cat_name = QTableWidgetItem(category.name)
            f = cat_name.font()
            f.setBold(True)
            f.setPointSize(15)
            cat_name.setFont(f)

            self.results_table.setItem(row, 0, cat_name)
            self.results_table.setSpan(row, 1, 1, 4)

            controls = map(lambda x: x.name, category.controls)
            self.results_table.setItem(row, 1, QTableWidgetItem(", ".join(controls)))

            row += 1

            results_cat = results.calculate_category(self.mw.db, category.name)

            for person in results_cat:
                if person.place == 0:
                    place = person.status
                else:
                    place = f"{person.place}."

                self.results_table.setItem(row, 0, QTableWidgetItem(place))
                self.results_table.setItem(row, 1, QTableWidgetItem(person.name))
                self.results_table.setItem(row, 2, QTableWidgetItem(f"{person.tx} TX"))
                self.results_table.setItem(
                    row, 3, QTableWidgetItem(" - ".join(person.order))
                )
                self.results_table.setItem(
                    row,
                    4,
                    QTableWidgetItem(
                        results.format_delta(timedelta(seconds=person.time))
                    ),
                )

                row += 1
            row += 1

        sess.close()

    def show(self):
        self._update_results()

        super().show()

        self.results_table.horizontalHeader().hide()
        self.results_table.verticalHeader().hide()
