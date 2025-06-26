import csv

from dateutil.parser import parser
from sqlalchemy import Select
from sqlalchemy.orm import Session

import api
from models import Category, Runner


def export(filename, db):
    if not filename.endswith(".csv"):
        filename += ".csv"
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";")

        sess = Session(db)
        categories = sess.scalars(Select(Category).order_by(Category.name.asc())).all()

        for category in categories:
            for person in sess.scalars(
                Select(Runner)
                .where(Runner.category == category)
                .order_by(Runner.startlist_time.asc())
            ).all():
                starttime = person.startlist_time or parser().parse(
                    api.get_basic_info(db)["date_tzero"]
                )

                writer.writerow(
                    [
                        "",
                        person.name.split(", ")[0],
                        person.name.split(", ")[1],
                        category.name,
                        "",
                        starttime.strftime("%H:%M:%S"),
                        person.reg,
                        "",
                        "CZE",
                        person.si,
                    ]
                )

        sess.close()
