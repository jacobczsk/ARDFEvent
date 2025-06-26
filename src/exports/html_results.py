from datetime import timedelta

from jinja2 import Environment, PackageLoader, select_autoescape
from sqlalchemy import Select
from sqlalchemy.orm import Session

import results
from exports import html_common
from models import Category


def export(filename, db, splits=False):
    sess = Session(db)
    categories = []
    categories_db = sess.scalars(Select(Category).order_by(Category.name.asc())).all()

    for category in categories_db:
        runners = []
        results_cat = results.calculate_category(db, category.name)

        for person in results_cat:
            if person.place == 0:
                place = person.status
            else:
                place = f"{person.place}."

            runner_splits = []

            if person.start:
                last = person.start

                for control in person.order:
                    runner_splits.append(
                        {
                            "control": control[0],
                            "time": results.format_delta(control[1] - person.start),
                            "split": results.format_delta(control[1] - last),
                        }
                    )
                    last = control[1]

            runners.append(
                {
                    "place": place,
                    "name": person.name,
                    "reg": person.reg,
                    "time": results.format_delta(timedelta(seconds=person.time)),
                    "tx": person.tx,
                    "order": " - ".join(map(lambda x: x[0], person.order)),
                    "splits": runner_splits,
                    "ok": person.status == "OK",
                }
            )
        categories.append(
            {
                "name": category.name,
                "controls": ", ".join(map(lambda x: x.name, category.controls)),
                "runners": runners,
            }
        )

    sess.close()

    env = Environment(loader=PackageLoader("exports"), autoescape=select_autoescape())
    template = env.get_template("results.html")

    if not filename.endswith(".html"):
        filename += ".html"

    with open(filename, "w+") as f:
        f.write(
            template.render(
                event=html_common.get_event(db), categories=categories, splits=splits
            )
        )
