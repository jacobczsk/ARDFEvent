from datetime import timedelta

from sqlalchemy import Select
from sqlalchemy.orm import Session

import results
from exports.pdf_common import ARDFEventPDF
from models import Category


def export(filename, db):
    pdf = ARDFEventPDF(db, "Výsledky")
    pdf.add_page()

    data = []

    sess = Session(db)
    categories = sess.scalars(Select(Category).order_by(Category.name.asc())).all()

    for category in categories:
        controls = map(lambda x: x.name, category.controls)
        data.append(["CATEGORY", category.name, ", ".join(controls)])

        results_cat = results.calculate_category(db, category.name)

        for person in results_cat:
            if person.place == 0:
                place = person.status
            else:
                place = f"{person.place}."

            if person.start is not None:
                start = person.start

            splits0 = []
            splits1 = []
            last = start

            for control in person.order:
                splits0.append(control[0])
                splits0.append(results.format_delta(control[1] - start))
                splits1.append("")
                splits1.append("+" + results.format_delta(control[1] - last))
                last = control[1]

            data.append(
                [
                    "RUNNER",
                    place,
                    person.name,
                    f"{person.tx} TX",
                    results.format_delta(timedelta(seconds=person.time)),
                ]
            )
            if not len(splits0) + len(splits1) == 0:
                data.append(["SPLITS"] + splits0)
                data.append(["SPLITS"] + splits1)

    sess.close()

    pdf.table(data)

    if not filename.endswith(".pdf"):
        filename += ".pdf"
    pdf.output(filename)
