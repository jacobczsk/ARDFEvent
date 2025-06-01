from PySide6.QtWidgets import (
    QFileDialog,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import Select
from sqlalchemy.orm import Session

import exports.pdf_startlist as stl_pdf
from models import Category, Runner
from ui import startlistdrawwin


class StartlistWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw
        self.sldw = startlistdrawwin.StartlistDrawWindow(self.mw)

        lay = QVBoxLayout()
        self.setLayout(lay)

        export_pdf_btn = QPushButton("Exportovat do PDF")
        export_pdf_btn.clicked.connect(self._export_pdf)
        lay.addWidget(export_pdf_btn)

        draw_win_btn = QPushButton("Losovat startovku")
        draw_win_btn.clicked.connect(self.sldw.show)
        lay.addWidget(draw_win_btn)

        self.startlist_table = QTableWidget()
        self.startlist_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.startlist_table)

    def _export_pdf(self):
        stl_pdf.export(
            QFileDialog.getSaveFileName(
                self, "Export startovky do PDF", filter="PDF (*.pdf)"
            )[0],
            self.mw.db,
        )

    def _update_startlist(self):
        sess = Session(self.mw.db)
        categories = sess.scalars(Select(Category).order_by(Category.name.asc())).all()

        self.startlist_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.startlist_table.clear()
        self.startlist_table.setColumnCount(4)
        self.startlist_table.setRowCount(1000)

        row = 0

        for category in categories:
            cat_name = QTableWidgetItem(category.name)
            f = cat_name.font()
            f.setBold(True)
            f.setPointSize(15)
            cat_name.setFont(f)

            self.startlist_table.setItem(row, 0, cat_name)
            self.startlist_table.setSpan(row, 1, 1, 3)

            controls = map(lambda x: x.name, category.controls)
            self.startlist_table.setItem(row, 1, QTableWidgetItem(", ".join(controls)))

            row += 1

            for person in sess.scalars(
                Select(Runner)
                .where(Runner.category == category)
                .order_by(Runner.startlist_time.asc())
            ).all():
                starttime = person.startlist_time
                if starttime is None:
                    starttime = "-"
                else:
                    starttime = starttime.strftime("%H:%M:%S")
                self.startlist_table.setItem(row, 0, QTableWidgetItem(person.name))
                self.startlist_table.setItem(row, 1, QTableWidgetItem(person.reg))
                self.startlist_table.setItem(row, 2, QTableWidgetItem(str(person.si)))
                self.startlist_table.setItem(row, 3, QTableWidgetItem(starttime))

                row += 1
            row += 1

        sess.close()

    def _show(self):
        self._update_startlist()

        self.startlist_table.horizontalHeader().hide()
        self.startlist_table.verticalHeader().hide()
