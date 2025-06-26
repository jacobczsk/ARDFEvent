import time
from datetime import datetime, timedelta

from escpos.printer import Serial
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QCompleter,
    QDialog,
    QFormLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)
from serial.tools.list_ports import comports
from sportident import SIReaderReadout
from sqlalchemy import Delete, Select
from sqlalchemy.orm import Session

import api
import results
from models import Control, Punch, Runner
from results import format_delta


class ReadoutThread(QThread):
    def __init__(self, parent, si_port) -> None:
        super().__init__(parent)
        self.si_port = si_port

    def run(self) -> None:
        try:
            si = SIReaderReadout(self.si_port)

            si.beep(3)

            while True:
                while not si.poll_sicard():
                    time.sleep(0.01)

                try:
                    data = si.read_sicard()
                    si.ack_sicard()
                    self.parent().on_readout.emit(data)

                except Exception as e:
                    if str(e) != "No card in the device.":
                        si.beep(2)
                        self.parent().si_error.emit()
        except Exception as e:
            self.parent().thr_err.emit(e.__str__())


class ReadoutWindow(QWidget):
    on_readout = Signal(dict)
    si_error = Signal()
    thr_err = Signal(str)

    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        self.proc: ReadoutThread = None

        self.on_readout.connect(self._handle_readout)
        self.si_error.connect(self._show_si_error)
        self.thr_err.connect(self._proc_stopped)

        lay = QVBoxLayout()
        self.setLayout(lay)

        portslay = QFormLayout()
        lay.addLayout(portslay)

        self.state_label = QLabel("Stav: Neaktivní")
        lay.addWidget(self.state_label)
        self.state_label.setStyleSheet("color: red;")

        self.siport_edit = QComboBox()
        portslay.addRow("Port SI readeru", self.siport_edit)
        self.printer_edit = QComboBox()
        portslay.addRow("Port tiskárny", self.printer_edit)

        self.double_print_chk = QCheckBox()
        portslay.addRow("Dvojtisk", self.double_print_chk)

        self.log = QTextBrowser()
        lay.addWidget(self.log)

        startreadout_btn = QPushButton("Spustit/vypnout")
        startreadout_btn.clicked.connect(self._toggle_readout)
        lay.addWidget(startreadout_btn)

    def _show_si_error(self):
        QMessageBox.critical(self, "Chyba", "Zkuste to znovu")

    def _toggle_readout(self):
        if self.proc:
            self.proc.terminate()
            self.proc.wait()
            self.proc = None
        else:
            self.proc = ReadoutThread(self, self.siport_edit.currentText())
            self.proc.started.connect(self._proc_running)
            self.proc.finished.connect(self._proc_stopped)
            self.proc.start()

            self.printer = Serial(self.printer_edit.currentText())

    def _proc_running(self):
        self.state_label.setText("Stav: Aktivní")
        self.state_label.setStyleSheet("color: green;")

    def _proc_stopped(self, msg=None):
        self.state_label.setText("Stav: Neaktivní")
        self.state_label.setStyleSheet("color: red;")
        self.log.setText(
            self.log.toPlainText() + msg + "\n" if msg else "Čtení ukončeno.\n"
        )

    def _append_log(self, string: str):
        self.log.setText(self.log.toPlainText() + string + "\n")

    def _handle_readout(self, data):
        si_no = data["card_number"]

        self._append_log("---------------------------------")
        self._append_log(f"Byl vyčten čip {si_no}.")

        sess = Session(self.mw.db)
        runners = sess.scalars(Select(Runner).where(Runner.si == si_no)).all()

        if len(runners) == 0:
            all_runners = map(lambda x: x.name, sess.scalars(Select(Runner)).all())

            inpd = QInputDialog()
            inpd.setWindowTitle("Nepřiřazený čip")
            inpd.setLabelText("Čip není přiřazen. Zadejte jméno.")
            inpd.setTextValue("")
            completer = QCompleter(all_runners, inpd)
            label: QLineEdit = inpd.findChild(QLineEdit)
            label.setCompleter(completer)

            ok, name = (
                inpd.exec() == QDialog.Accepted,
                inpd.textValue(),
            )
            if ok:
                try:
                    runner = sess.scalars(
                        Select(Runner).where(Runner.name == name)
                    ).one()
                    runner.si = si_no
                except:
                    self._append_log(f"Nenalezeno.")
                    sess.close()
                    return
            else:
                self._append_log(f"Zrušeno vyčtení.")
                sess.close()
                return
        else:
            runner = runners[0]

        self._append_log(f"Závodník: {runner.name} ({runner.reg}).")

        if len(sess.scalars(Select(Punch).where(Punch.si == si_no)).all()) != 0:
            if (
                QMessageBox.warning(
                    self,
                    "Chyba",
                    f"Čip {si_no} byl již vyčten. Přepsat?",
                    QMessageBox.StandardButton.Yes,
                    QMessageBox.StandardButton.No,
                )
                == QMessageBox.StandardButton.Yes
            ):
                self._append_log(f"Přepsán předchozí zápis.")
                sess.execute(Delete(Punch).where(Punch.si == si_no))
            else:
                self._append_log(f"Zrušeno vyčtení.")
                sess.close()
                return
        for punch in data["punches"]:
            sess.add(Punch(si=si_no, code=punch[0], time=punch[1]))

        if data["start"]:
            sess.add(Punch(si=si_no, code=1000, time=data["start"]))

        if data["finish"]:
            sess.add(Punch(si=si_no, code=1001, time=data["finish"]))

        sess.commit()
        sess.close()

        self.mw.results_win._update_results()
        self.mw.robis_win._send_online_readout(self.mw.db, si_no)

        if self.printer != "Netisknout":
            print_readout(self.mw.db, si_no, self.printer)
            if (
                self.double_print_chk.isChecked()
                and QMessageBox.warning(
                    self,
                    "Dvojtisk",
                    "Tisknout podruhé?",
                    QMessageBox.StandardButton.Ok,
                    QMessageBox.StandardButton.Abort,
                )
                == QMessageBox.StandardButton.Ok
            ):
                print_readout(self.mw.db, si_no, self.printer, True)

    def _update_ports(self):
        oldportsi = self.siport_edit.currentText()
        oldportprinter = self.printer_edit.currentText()

        self.siport_edit.clear()
        self.printer_edit.clear()

        self.printer_edit.addItem("Netisknout")

        for port in comports()[::-1]:
            self.siport_edit.addItem(port.device)
            self.printer_edit.addItem(port.device)

        if self.proc != None:
            idx_si = self.siport_edit.findData(oldportsi)
            if idx_si != -1:
                self.siport_edit.setCurrentIndex(idx_si)

            idx_printer = self.printer_edit.findData(oldportprinter)
            if idx_printer != -1:
                self.printer_edit.setCurrentIndex(idx_printer)

    def _show(self):
        self._update_ports()

    def closeEvent(self, event: QCloseEvent) -> None:
        try:
            self.proc.terminate()
            self.proc.wait()
        except:
            ...
        super().closeEvent(event)


def print_readout(db, si: int, printer: Serial, snura=False):
    def text(string: str = ""):
        printer._raw(string.encode("cp852"))

    def line(string: str = ""):
        text(string + "\n")

    basic_info = api.get_basic_info(db)

    if not snura:
        printer.set(align="center", double_height=True)
        line(basic_info["name"])
        printer.set(align="center", double_height=False)
        line(datetime.fromisoformat(basic_info["date_tzero"]).strftime("%d. %m. %Y"))
        printer.set(align="left")
        line()
    else:
        text("\n\n\n\n\n\n")

    sess = Session(db)

    runner = sess.scalars(Select(Runner).where(Runner.si == si)).one()
    punches = list(sess.scalars(Select(Punch).where(Punch.si == si)).all())
    punches.sort(key=lambda x: x.time)

    start = sess.scalars(
        Select(Punch).where(Punch.si == si).where(Punch.code == 1000)
    ).one_or_none()

    if not snura:
        printer.set(bold=True)
        text(runner.name)
        printer.set(bold=False)
        line(f" ({runner.reg})")
        line(f"Kat.:  {runner.category.name}")
        line(f"Klub:  {runner.club}")
        line(f"SI:    {runner.si}")
    else:
        printer.set(align="center", double_height=True)
        line(runner.name)
        printer.set(align="left", double_height=False)
        line(f"{runner.reg}, {runner.category.name}")

    startovka = None

    if runner.startlist_time:
        startovka = runner.startlist_time
        line(f"Start: {startovka.strftime('%H:%M:%S')}")

    line("")

    if start:
        stime: datetime = start.time
    elif startovka:
        stime: datetime = startovka
    else:
        stime: datetime = datetime.fromisoformat(api.get_basic_info(db)["date_tzero"])

    lasttime = stime

    printer.set(bold=True)
    line("Kód\tČas\tMezičas".expandtabs(10))
    printer.set(bold=False)

    for punch in punches:
        control = sess.scalars(
            Select(Control).where(Control.code == punch.code)
        ).one_or_none()
        if control:
            cn_name = f"({punch.code}) {control.name}"
        elif punch.code == 1000:
            cn_name = "Start"
        elif punch.code == 1001:
            cn_name = "Finish"
        else:
            cn_name = f"({punch.code}) N/A"
        ptime: datetime = punch.time
        fromstart = ptime - stime
        split = ptime - lasttime

        line(
            f"{cn_name}\t{format_delta(fromstart)}\t+{format_delta(split)}".expandtabs(
                10
            )
        )

        lasttime = ptime

    results_cat = results.calculate_category(db, runner.category.name)
    result = list(filter(lambda x: x.name == runner.name, results_cat))[0]

    line()

    text("Výsledek: ")
    printer.set(bold=True)
    line(
        f"{format_delta(timedelta(seconds=result.time))}, {result.tx} TX, {result.status}\n"
    )
    printer.set(bold=False)
    if not snura:
        printer.set(bold=True)
        line("Výsledky:")
        printer.set(bold=False)

        for result_lp in results_cat[:3]:
            place = f"{result_lp.place}." if result_lp.status == "OK" else "-"
            printer.set(align="left")
            line(f"{place} {result_lp.name}")
            printer.set(align="right")
            line(
                f"{format_delta(timedelta(seconds=result_lp.time))}, {result_lp.tx} TX"
            )

        if result.place > 3:
            printer.set(bold=True)
            place = f"{result.place}." if result.status == "OK" else "-"
            printer.set(align="left")
            line(f"{place} {result.name}")
            printer.set(align="right")
            line(f"{format_delta(timedelta(seconds=result.time))}, {result.tx} TX")
            printer.set(bold=False)

    printer.set(align="center")
    line("ARDFEvent, (C) Jakub Jiroutek")

    printer.print_and_feed(4)
    sess.close()
