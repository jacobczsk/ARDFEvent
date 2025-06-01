from datetime import timedelta

from sqlalchemy import Select
from sqlalchemy.orm import Session

from exports.pdf_common import ARDFEventPDF
from models import Category, Runner


def export(filename, db):
    pdf = ARDFEventPDF(db, "Startovní listina")
    pdf.add_page()

    data = []

    sess = Session(db)
    categories = sess.scalars(Select(Category).order_by(Category.name.asc())).all()

    for category in categories:
        controls = map(lambda x: x.name, category.controls)
        data.append(["CATEGORY", category.name, ", ".join(controls)])

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

            data.append(
                [
                    "RUNNER",
                    person.name,
                    person.reg,
                    starttime,
                ]
            )

    sess.close()

    pdf.table(data)

    if not filename.endswith(".pdf"):
        filename += ".pdf"
    pdf.output(filename)
