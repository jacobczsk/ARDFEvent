from datetime import timedelta
from pathlib import Path
import sys

from dateutil.parser import parser
from fpdf import FPDF
from sqlalchemy import Engine, Select
from sqlalchemy.orm import Session

import api, results
from models import Category


class PDF(FPDF):
    def __init__(self, db: Engine):
        super().__init__("portrait", "mm", "A4")
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=25)
        self._load_fonts()
        self.set_author("ARDFEvent")
        self.set_title("Výsledky")

        self.pages_count = 0
        self.db = db

    def _load_fonts(self):
        FONTS = {
            "DejaVuSans": {
                "--name--": "DejaVu",
                "": "",
                "Bold": "B",
                "Oblique": "I",
                "BoldOblique": "BI",
            },
            "DejaVuSansMono": {
                "--name--": "DejaVuMono",
                "": "",
                "Bold": "B",
                "Oblique": "I",
                "BoldOblique": "BI",
            },
        }

        for font, font_info in FONTS.items():
            name = font_info["--name--"]
            for style, style_code in font_info.items():
                if style == "--name--":
                    continue
                self.add_font(
                    name,
                    style_code,
                    Path(sys.argv[0])
                    .parent.joinpath(
                        f"font/{font}{"-" if style != "" else ""}{style}.ttf"
                    )
                    .absolute(),
                    uni=True,
                )

    def header(self):
        self.pages_count += 1

        if self.pages_count == 1:
            basic_info = api.get_basic_info(self.db)
            race_time = parser().parse(basic_info["date_tzero"])
            details = (
                f"Datum: {race_time.strftime("%d.%m.%Y")}\n"
                + f"První start: {race_time.strftime("%H:%M")}\n"
                + f"Pořadatel: {basic_info["organizer"]}\n"
                + f"Limit: {basic_info["limit"]} min\n"
                + f"Pásmo: {basic_info["band"]}\n"
            )
            self.set_font("DejaVu", "B", 16)
            self.cell(0, 8, basic_info["name"], 0, 1, "C")
            self.set_font("DejaVu", "B", 14)
            self.cell(0, 6, "Výsledky", 0, 1, "C")
            self.set_font("DejaVu", "", 12)
            self.multi_cell(0, 5, details, 0)
            self.cell(0, 8, "", 0, 1)
        else:
            self.set_font("DejaVu", "", 8)
            self.cell(0, 8, "(pokrač.)", 0, 1)

    def footer(self):
        self.set_y(-25)
        self.set_font("DejaVu", "", 8)
        self.cell(0, 8, "ARDFEvent, (C) Jakub Jiroutek", 0, 1, "C")
        self.set_font("DejaVu", "", 12)
        self.cell(0, 8, str(self.pages_count), 0, 1, "C")

    def table(self, data):
        def _print_row(row, widths):
            for i, item in enumerate(row):
                self.cell(widths[i], 6, item, 0)
            self.ln()

        def _get_table_widths(data):
            widths = []
            for row in data:
                if len(row) == 2:
                    continue
                for i, item in enumerate(row):
                    if i >= len(widths):
                        widths.append(self.get_string_width(item) + 5)
                    else:
                        widths[i] = max(widths[i], self.get_string_width(item) + 5)
            return widths

        self.set_font("DejaVu", "", 12)
        widths = _get_table_widths(data)

        self.set_font("DejaVu", "", 12)

        for row in data:
            if len(row) == 2:
                self.set_font("DejaVu", "B", 14)
                self.cell(self.get_string_width(row[0]) + 6, 6, row[0], 0)
                self.set_font("DejaVu", "B", 12)
                self.cell(0, 6, row[1], 0)
                self.ln()
            else:
                self.set_font("DejaVu", "", 10)
                _print_row(row, widths)


def export(filename, db):
    pdf = PDF(db)
    pdf.add_page()

    data = []

    sess = Session(db)
    categories = sess.scalars(Select(Category).order_by(Category.name.asc())).all()

    for category in categories:
        controls = map(lambda x: x.name, category.controls)
        data.append([category.name, ", ".join(controls)])

        results_cat = results.calculate_category(db, category.name)

        for person in results_cat:
            if person.place == 0:
                place = person.status
            else:
                place = f"{person.place}."

            data.append(
                [
                    place,
                    person.name,
                    f"{person.tx} TX",
                    " - ".join(person.order),
                    results.format_delta(timedelta(seconds=person.time)),
                ]
            )

    pdf.table(data)

    pdf.output(filename)
