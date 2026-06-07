from datetime import timedelta, datetime

from PySide6.QtCore import QStringListModel, Qt, QCoreApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QCompleter,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSpinBox,
    QVBoxLayout,
    QWidget, QInputDialog, QLabel, QFrame, QDialog, QMessageBox,
)
from sqlalchemy import Delete, Select
from sqlalchemy.orm import Session

import api
from models import Category, Runner, Punch
from ui.qtaiconbutton import QTAIconButton


class RunnerWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        mainlay = QHBoxLayout()
        self.setLayout(mainlay)

        leftlay = QVBoxLayout()
        mainlay.addLayout(leftlay)

        linelay = QHBoxLayout()
        leftlay.addLayout(linelay)

        new_btn = QTAIconButton("mdi6.account-plus-outline", QCoreApplication.translate("RunnerWindow", "Nový"))
        new_btn.clicked.connect(self._new_runner)
        linelay.addWidget(new_btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)

        self.search = QLineEdit()
        self.search.setPlaceholderText(QCoreApplication.translate("RunnerWindow", "Hledat"))
        self.search.textEdited.connect(self._update_runners_cats)
        linelay.addWidget(self.search)

        import_btn = QTAIconButton("mdi6.import", QCoreApplication.translate("RunnerWindow", "Import"))
        import_btn.clicked.connect(self.mw.import_win.show)
        linelay.addWidget(import_btn)

        self.runners_list = QListWidget()
        self.runners_list.itemClicked.connect(self._select_by_user)
        leftlay.addWidget(self.runners_list)

        right_lay = QVBoxLayout()
        mainlay.addLayout(right_lay)

        btn_lay = QHBoxLayout()
        right_lay.addLayout(btn_lay)

        save_btn = QTAIconButton("mdi6.content-save-outline", QCoreApplication.translate("RunnerWindow", "Uložit"))
        save_btn.clicked.connect(self._save_runner)
        btn_lay.addWidget(save_btn)

        print_btn = QTAIconButton("mdi6.receipt-text-outline",
                                  QCoreApplication.translate("RunnerWindow", "Vytisknout výčet"))
        print_btn.clicked.connect(self._btn_print_readout)
        btn_lay.addWidget(print_btn)

        snura_btn = QTAIconButton("mdi6.receipt-text-plus-outline",
                                  QCoreApplication.translate("RunnerWindow", "Vytisknout výčet na šňůru"))
        snura_btn.clicked.connect(self._btn_print_snura)
        btn_lay.addWidget(snura_btn)

        send_btn = QTAIconButton("mdi6.earth-arrow-up", QCoreApplication.translate("RunnerWindow", "Odeslat online"))
        send_btn.clicked.connect(self._send_online)
        btn_lay.addWidget(send_btn)

        st_btn = QTAIconButton("mdi6.timer-edit-outline",
                               QCoreApplication.translate("RunnerWindow", "Změnit startovní čas"))
        st_btn.clicked.connect(self._set_starttime)
        btn_lay.addWidget(st_btn)

        punches_btn = QTAIconButton("mdi6.view-grid-plus", QCoreApplication.translate("RunnerWindow", "Ražení"))
        punches_btn.clicked.connect(self._open_punches_dialog)
        btn_lay.addWidget(punches_btn)

        btn_lay.addStretch()

        delete_btn = QTAIconButton("mdi6.account-minus-outline", QCoreApplication.translate("RunnerWindow", "Smazat"))
        delete_btn.clicked.connect(self._delete_runner)
        btn_lay.addWidget(delete_btn)

        details_lay = QFormLayout()
        right_lay.addLayout(details_lay)

        self.name_edit = QLineEdit()
        self.name_edit.textEdited.connect(self._save_runner)

        details_lay.addRow(QCoreApplication.translate("RunnerWindow", "Jméno"), self.name_edit)

        self.name_completer = QCompleter([])
        self.name_completer.highlighted.connect(self._prefill_runner)
        self.name_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.name_edit.setCompleter(self.name_completer)

        self.club_edit = QLineEdit()
        details_lay.addRow(QCoreApplication.translate("RunnerWindow", "Klub"), self.club_edit)

        self.SI_edit = QSpinBox()
        self.SI_edit.setMaximum(10_000_000)
        details_lay.addRow(QCoreApplication.translate("RunnerWindow", "SI"), self.SI_edit)

        self.reg_edit = QLineEdit()
        details_lay.addRow(QCoreApplication.translate("RunnerWindow", "Reg. číslo"), self.reg_edit)

        self.category_edit = QComboBox()
        details_lay.addRow(QCoreApplication.translate("RunnerWindow", "Kategorie"), self.category_edit)

        self.startno_edit = QSpinBox()
        details_lay.addRow(QCoreApplication.translate("RunnerWindow", "Startovní číslo"), self.startno_edit)

        self.starttime_lbl = QLabel()
        details_lay.addRow(QCoreApplication.translate("RunnerWindow", "Startovní čas"), self.starttime_lbl)

        self.dns_edit = QCheckBox()
        details_lay.addRow("DNS", self.dns_edit)

        self.dsq_edit = QCheckBox()
        details_lay.addRow("DSQ", self.dsq_edit)

        self.selected = 0
        self.category_indexes = {}

    def _set_starttime(self):
        with Session(self.mw.db) as sess:
            runner = self._get_runner(sess)
            if runner:
                runner.startlist_time = datetime.fromisoformat(
                    api.get_basic_info(self.mw.db)["date_tzero"]) + timedelta(minutes=
                                                                              QInputDialog.getDouble(
                                                                                  self,
                                                                                  QCoreApplication.translate(
                                                                                      "RunnerWindow", "Startovní čas"),
                                                                                  QCoreApplication.translate(
                                                                                      "RunnerWindow",
                                                                                      "Zadejte relativní startovní čas (min)"),
                                                                                  minValue=-1440,
                                                                                  maxValue=1440,
                                                                                  step=0.1)[0])

            sess.commit()

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

    def _save_btn(self):
        self._select_by_user(QListWidgetItem(self.name_edit.text()))

    def _save_runner(self):
        with Session(self.mw.db) as sess:
            runner = self._get_runner(sess)
            if runner:
                runner.name = self.name_edit.text()
                runner.club = self.club_edit.text()
                runner.si = self.SI_edit.value()
                runner.reg = self.reg_edit.text()
                runner.startno = self.startno_edit.value() or None

                runner.category = sess.scalars(
                    Select(Category).where(
                        Category.name == self.category_edit.currentText()
                    )
                ).one()
                runner.manual_dns = self.dns_edit.isChecked()
                runner.manual_disk = self.dsq_edit.isChecked()

            sess.commit()

        self._update_runners_cats()

    def _select_by_user(self, item: QListWidgetItem):
        text = item.text()
        self._save_runner()
        self._update_runners_cats()
        self._select(text)

    def _send_online(self):
        self.mw.pl.readout(int(self.SI_edit.text()))

    def _select(self, text):
        with Session(self.mw.db) as sess:
            runner = sess.scalars(Select(Runner).where(Runner.name == text)).one_or_none()

            if runner:
                self.name_edit.setText(runner.name)
                self.club_edit.setText(runner.club)
                self.SI_edit.setValue(runner.si)
                self.reg_edit.setText(runner.reg)
                self.startno_edit.setValue(runner.startno or 0)
                self.starttime_lbl.setText(runner.startlist_time.strftime("%H:%M:%S") if runner.startlist_time else "-")

                self.category_edit.setCurrentIndex(
                    self.category_indexes[runner.category.name]
                )

                self.dns_edit.setChecked(runner.manual_dns)
                self.dsq_edit.setChecked(runner.manual_disk)

                self.selected = runner.id
            else:
                raise ValueError("Runner not found")

    def _update_runners_cats(self):
        self.runners_list.clear()

        cat_index = self.category_edit.currentIndex()
        self.category_edit.clear()

        with Session(self.mw.db) as sess:
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

            self.category_edit.setCurrentIndex(cat_index)

            runners = sess.scalars(Select(Runner)).all()

            registered = api.get_registered_names()
            for runner in runners:
                if runner.name in registered:
                    registered.remove(runner.name)

            self.name_completer.setModel(QStringListModel(registered))

    def _new_runner(self):
        if not self.runners_list.count() == 0:
            self._save_runner()
        try:
            self._select("")
        except:
            with Session(self.mw.db) as sess:
                runner = Runner(
                    name=f"",
                    club="",
                    si=0,
                    reg=f"",
                    call="",
                    category=sess.scalars(Select(Category)).first(),
                    startlist_time=None,
                )
                sess.add(runner)

                sess.commit()

            self._select("")

            self._update_runners_cats()

    def _delete_runner(self):
        with Session(self.mw.db) as sess:
            sess.execute(Delete(Runner).where(Runner.id == self.selected))
            sess.commit()

        self._update_runners_cats()
        if self.runners_list.item(0):
            self._select(self.runners_list.item(0).text())
        else:
            self._new_runner()

    def _print_readout(self, snura):
        if self.mw.readout_win.printer:
            with Session(self.mw.db) as sess:
                runner = sess.scalars(
                    Select(Runner).where(Runner.id == self.selected)
                ).one_or_none()

                if runner:
                    self.mw.readout_win.print_readout(runner.si, snura)

    def _btn_print_readout(self):
        self._print_readout(False)

    def _btn_print_snura(self):
        self._print_readout(True)

    def _show(self):
        self._update_runners_cats()
        try:
            self._select(self.runners_list.item(0).text())
        except:
            ...

    def _open_punches_dialog(self):
        if not self.selected:
            QMessageBox.warning(self, QCoreApplication.translate("RunnerWindow", "Chyba"),
                                QCoreApplication.translate("RunnerWindow", "Vyberte závodníka nejdříve."))
            return
        dlg = RunnerPunchesDialog(self.mw, self.selected, parent=self)
        dlg.exec()


class RunnerPunchesDialog(QDialog):
    def __init__(self, mw, runner_id: int, parent=None):
        super().__init__(parent)
        self.mw = mw
        self.runner_id = runner_id

        self.setWindowTitle(QCoreApplication.translate("RunnerWindow", "Ražení závodníka"))

        lay = QVBoxLayout(self)

        self.punches_list = QListWidget()
        lay.addWidget(self.punches_list)

        btn_lay = QHBoxLayout()
        lay.addLayout(btn_lay)

        add_btn = QTAIconButton("mdi6.plus-box-outline", QCoreApplication.translate("RunnerWindow", "Přidat"))
        add_btn.clicked.connect(self._add_punch)
        btn_lay.addWidget(add_btn)

        edit_btn = QTAIconButton("mdi6.pencil", QCoreApplication.translate("RunnerWindow", "Upravit"))
        edit_btn.clicked.connect(self._edit_punch)
        btn_lay.addWidget(edit_btn)

        del_btn = QTAIconButton("mdi6.delete", QCoreApplication.translate("RunnerWindow", "Smazat"))
        del_btn.clicked.connect(self._delete_punch)
        btn_lay.addWidget(del_btn)

        close_btn = QTAIconButton("mdi6.close", QCoreApplication.translate("RunnerWindow", "Zavřít"))
        close_btn.clicked.connect(self.accept)
        btn_lay.addWidget(close_btn)

        self._load_punches()

    def _get_runner(self, sess: Session):
        return sess.scalars(Select(Runner).where(Runner.id == self.runner_id)).one_or_none()

    def _load_punches(self):
        self.punches_list.clear()
        with Session(self.mw.db) as sess:
            runner = self._get_runner(sess)
            if not runner:
                return
            if not runner.si:
                QMessageBox.information(self, QCoreApplication.translate("RunnerWindow", "Žádné SI"),
                                        QCoreApplication.translate("RunnerWindow", "Běžec nemá přiřazené SI."))
                return
            punches = sess.scalars(Select(Punch).where(Punch.si == runner.si).order_by(Punch.time)).all()
            for p in punches:
                text = f"{p.code if p.code not in [1000, 1001, 1002] else ["start", "cíl", "OChecklist"][p.code - 1000]} - {p.time.strftime('%Y-%m-%d %H:%M:%S')}"
                if getattr(p, "modified", False):
                    text += " (upraveno)"
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, p.id)
                self.punches_list.addItem(item)

    def _add_punch(self):
        with Session(self.mw.db) as sess:
            runner = self._get_runner(sess)
            if not runner or not runner.si:
                QMessageBox.warning(self, QCoreApplication.translate("RunnerWindow", "Chyba"),
                                    QCoreApplication.translate("RunnerWindow", "Běžec nemá SI. Nejprve přiřaďte SI."))
                return
            code, ok = QInputDialog.getInt(self, QCoreApplication.translate("RunnerWindow", "Kód ražení"),
                                           QCoreApplication.translate("RunnerWindow", "Zadejte kód ražení (číslo)"), 0)
            if not ok:
                return
            timestr, ok = QInputDialog.getText(self, QCoreApplication.translate("RunnerWindow", "Čas"),
                                               QCoreApplication.translate("RunnerWindow",
                                                                          "Zadejte čas (HH:MM:SS)"),
                                               text=datetime.now().strftime('%H:%M:%S'))
            if not ok:
                return
            try:

                ttime = datetime.strptime(timestr, "%H:%M:%S").time()
                base_date = datetime.fromisoformat(api.get_basic_info(self.mw.db)["date_tzero"]).date()
                t = datetime.combine(base_date, ttime)
            except Exception:
                QMessageBox.warning(self, QCoreApplication.translate("RunnerWindow", "Chybný čas"),
                                    QCoreApplication.translate("RunnerWindow",
                                                               "Neplatný formát času. Použijte HH:MM:SS."))
                return
            sess.add(Punch(si=runner.si, code=code, time=t, modified=True))
            sess.commit()
        self._load_punches()

    def _edit_punch(self):
        it = self.punches_list.currentItem()
        if not it:
            return
        pid = it.data(Qt.ItemDataRole.UserRole)
        with Session(self.mw.db) as sess:
            punch = sess.get(Punch, pid)
            if not punch:
                return

            timestr, ok = QInputDialog.getText(self, QCoreApplication.translate("RunnerWindow", "Čas"),
                                               QCoreApplication.translate("RunnerWindow",
                                                                          "Zadejte čas (HH:MM:SS)"),
                                               text=punch.time.strftime('%H:%M:%S'))
            if not ok:
                return
            try:
                ttime = datetime.strptime(timestr, "%H:%M:%S").time()
                t = datetime.combine(punch.time.date(), ttime)
            except Exception:
                QMessageBox.warning(self, QCoreApplication.translate("RunnerWindow", "Chybný čas"),
                                    QCoreApplication.translate("RunnerWindow",
                                                               "Neplatný formát času. Použijte HH:MM:SS."))
                return
            punch.time = t
            punch.modified = True
            sess.commit()
        self._load_punches()

    def _delete_punch(self):
        it = self.punches_list.currentItem()
        if not it:
            return
        if QMessageBox.question(self, QCoreApplication.translate("RunnerWindow", "Smazat"),
                                QCoreApplication.translate("RunnerWindow",
                                                           "Opravdu smazat vybrané ražení?")) != QMessageBox.StandardButton.Yes:
            return
        pid = it.data(Qt.ItemDataRole.UserRole)
        with Session(self.mw.db) as sess:
            sess.execute(Delete(Punch).where(Punch.id == pid))
            sess.commit()
        self._load_punches()

    def closeEvent(self, event):
        super().closeEvent(event)
