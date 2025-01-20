from PySide6.QtCore import QStringListModel, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from ui.readoutwin import print_readout
from escpos.printer import Serial
from serial.tools.list_ports import comports
from sqlalchemy import Delete, Select
from sqlalchemy.orm import Session

import api
from models import Category, Runner


class RunnerWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        sess = Session(self.mw.db)

        mainlay = QHBoxLayout()
        self.setLayout(mainlay)

        leftlay = QVBoxLayout()
        mainlay.addLayout(leftlay)

        new_btn = QPushButton("Nový")
        new_btn.clicked.connect(self._new_runner)
        leftlay.addWidget(new_btn)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Hledat")
        self.search.textEdited.connect(self._update_runners_cats)
        leftlay.addWidget(self.search)

        self.runners_list = QListWidget()
        self.runners_list.itemClicked.connect(self._select_by_user)
        leftlay.addWidget(self.runners_list)

        right_lay = QVBoxLayout()
        mainlay.addLayout(right_lay)

        details_lay = QFormLayout()
        right_lay.addLayout(details_lay)

        self.name_edit = QLineEdit()
        self.name_edit.textEdited.connect(self._save_runner)

        details_lay.addRow("Jméno", self.name_edit)

        self.name_completer = QCompleter([])
        self.name_completer.highlighted.connect(self._prefill_runner)
        self.name_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.name_edit.setCompleter(self.name_completer)

        self.club_edit = QLineEdit()
        details_lay.addRow("Klub", self.club_edit)

        self.SI_edit = QSpinBox()
        self.SI_edit.setMaximum(10_000_000)
        details_lay.addRow("SI", self.SI_edit)

        self.reg_edit = QLineEdit()
        details_lay.addRow("Reg. číslo", self.reg_edit)

        self.call_edit = QLineEdit()
        details_lay.addRow("Volačka", self.call_edit)

        self.category_edit = QComboBox()
        details_lay.addRow("Kategorie", self.category_edit)

        print_btn = QPushButton("Vytiknout výčet")
        print_btn.clicked.connect(self._print_readout)
        details_lay.addWidget(print_btn)

        delete_btn = QPushButton("Smazat")
        delete_btn.clicked.connect(self._delete_runner)
        details_lay.addWidget(delete_btn)

        self.selected = 0
        self.category_indexes = {}

        sess.close()

    def _prefill_runner(self, text):
        registration = api.get_registered_runners()
        runner = list(filter(lambda r: r["name"] == text, registration))
        if runner:
            runner = runner[0]
            self.name_edit.setText(runner["name"])
            self.SI_edit.setValue(runner["si"])
            self.reg_edit.setText(runner["reg"])
            self.club_edit.setText(api.get_clubs().get(runner["reg"][:3], ""))
            self._save_runner()

    def _get_runner(self, sess: Session):
        return sess.scalars(
            Select(Runner).where(Runner.id == self.selected)
        ).one_or_none()

    def _save_runner(self):
        sess = Session(self.mw.db)
        runner = self._get_runner(sess)
        if runner:
            runner.name = self.name_edit.text()
            runner.club = self.club_edit.text()
            runner.si = self.SI_edit.text()
            runner.reg = self.reg_edit.text()
            runner.call = self.call_edit.text()

            category = sess.scalars(
                Select(Category).where(
                    Category.name == self.category_edit.currentText()
                )
            ).one_or_none()
            if category:
                runner = self._get_runner(sess)
                runner.category = category
        sess.commit()
        sess.close()

        self._update_runners_cats()

    def _select_by_user(self, item: QListWidgetItem):
        text = item.text()
        self._save_runner()
        self._update_runners_cats()
        self._select(text)

    def _select(self, text):
        sess = Session(self.mw.db)
        runner = sess.scalars(Select(Runner).where(Runner.name == text)).one_or_none()

        if runner:
            self.name_edit.setText(runner.name)
            self.club_edit.setText(runner.club)
            self.SI_edit.setValue(runner.si)
            self.reg_edit.setText(runner.reg)
            self.call_edit.setText(runner.call)
            self.category_edit.setCurrentIndex(
                self.category_indexes[runner.category.name]
            )

            self.selected = runner.id

        sess.close()

    def _update_runners_cats(self):
        self.runners_list.clear()
        self.category_edit.clear()

        sess = Session(self.mw.db)
        api.renumber_runners(self.mw.db)

        runners = sess.scalars(
            Select(Runner)
            .where(Runner.name.icontains(self.search.text()))
            .order_by(Runner.name.asc())
        ).all()
        for runner in runners:
            self.runners_list.addItem(QListWidgetItem(runner.name))

        i = 0
        categories = sess.scalars(Select(Category).order_by(Category.name.asc())).all()
        for category in categories:
            self.category_edit.addItem(category.name)
            self.category_indexes[category.name] = i
            i += 1

        runners = sess.scalars(Select(Runner)).all()

        registered = api.get_registered_names()
        for runner in runners:
            if runner.name in registered:
                registered.remove(runner.name)

        self.name_completer.setModel(QStringListModel(registered))

        sess.commit()
        sess.close()

    def _new_runner(self):
        nereg = int(api.get_basic_info(self.mw.db)["nereg"] or 0)
        sess = Session(self.mw.db)
        category = sess.scalars(Select(Category)).first()
        sess.add(
            Runner(
                name=f"Nový závodník {nereg}",
                club="",
                si=0,
                reg=f"NNN{nereg:04}",
                call="",
                category=category,
            )
        )

        sess.commit()
        sess.close()

        self._update_runners_cats()

        api.set_basic_info(self.mw.db, {"nereg": nereg + 1})

    def _delete_runner(self):
        sess = Session(self.mw.db)
        sess.execute(Delete(Runner).where(Runner.id == self.selected))
        sess.commit()

        self._update_runners_cats()
        self._select(self.runners_list.item(0).text())

    def _print_readout(self):
        sess = Session(self.mw.db)
        runner = sess.scalars(
            Select(Runner).where(Runner.id == self.selected)
        ).one_or_none()

        if runner:
            inpd = QInputDialog()
            inpd.setComboBoxItems([p.device for p in comports()])
            inpd.setLabelText("Vyberte port tiskárny")
            inpd.setWindowTitle("Tisk")
            if inpd.exec() == QInputDialog.DialogCode.Accepted:
                print_readout(self.mw.db, runner.si, Serial(inpd.textValue()))

        sess.close()

    def show(self):
        super().show()

        self._update_runners_cats()
        try:
            self._select(self.runners_list.item(0).text())
        except:
            ...

    def closeEvent(self, event):
        self._save_runner()
        super().closeEvent(event)
