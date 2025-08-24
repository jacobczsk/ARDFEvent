import csv
from datetime import timedelta

from sqlalchemy import Select
from sqlalchemy.orm import Session

import results
from models import Category


def export(filename, db):
    if not filename.endswith(".csv"):
        filename += ".csv"

    with open(filename, "w+") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerows(generate(db))


def generate(db):
    sess = Session(db)
    categories_db = sess.scalars(Select(Category).order_by(Category.name.asc())).all()
    runners = [
        ["Kategorie", "Pořadí", "Jméno", "Index", "Čas", "TX", "Status", "Pořadí"]
    ]

    for category in categories_db:
        results_cat = list(
            filter(
                lambda x: x.status != "DNS",
                results.calculate_category(db, category.name),
            )
        )

        if not len(results_cat):
            continue

        for person in results_cat:
            if person.place == 0:
                place = person.status
            else:
                place = f"{person.place}."

            runners.append(
                [
                    category.name,
                    place,
                    person.name,
                    person.reg,
                    results.format_delta(timedelta(seconds=person.time)),
                    person.tx,
                    person.status,
                    "-".join(map(lambda x: x[0], person.order)),
                ]
            )

    sess.close()

    return runners
