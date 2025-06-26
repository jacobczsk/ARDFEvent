from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import Select
from sqlalchemy.orm import Session

import exports.html_startlist as stl_html
import exports.robis_csv_startlist as stl_robis_csv
import exports.xml_startlist as stl_xml
from models import Category, Runner
from ui import startlistdrawwin


class StartlistWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        lay = QVBoxLayout()
        self.setLayout(lay)

        btn_lay = QHBoxLayout()
        lay.addLayout(btn_lay)

        export_menu = QMenu(self)
        export_menu.addAction("HTML", self._export_html)
        export_menu.addAction("CSV pro ROBis", self._export_robis_csv)
        export_menu.addAction("IOF XML 3.0", self._export_iof_xml)

        export_btn = QPushButton("Exportovat")
        export_btn.setMenu(export_menu)
        btn_lay.addWidget(export_btn)

        draw_win_btn = QPushButton("Losovat startovku")
        draw_win_btn.clicked.connect(self.mw.startlistdraw_win.show)
        btn_lay.addWidget(draw_win_btn)

        btn_lay.addStretch()

        self.startlist_table = QTableWidget()
        self.startlist_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.startlist_table)

    def _export_html(self):
        fn = QFileDialog.getSaveFileName(
            self, "Export startovky do HTML", filter=("HTML (*.html)")
        )[0]

        if fn:
            stl_html.export(
                fn,
                self.mw.db,
            )

    def _export_robis_csv(self):
        fn = QFileDialog.getSaveFileName(
            self,
            "Export startovky do CSV pro ROBis",
            filter=("ROBis CSV (*.csv)"),
        )[0]

        if fn:
            stl_robis_csv.export(
                fn,
                self.mw.db,
            )

    def _export_iof_xml(self):
        fn = QFileDialog.getSaveFileName(
            self,
            "Export startovky do IOF XML 3.0",
            filter=("IOF XML 3.0 (*.xml)"),
        )[0]

        if fn:
            stl_xml.export(
                fn,
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

            self.startlist_table.setItem(
                row, 1, QTableWidgetItem(category.display_controls)
            )

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
