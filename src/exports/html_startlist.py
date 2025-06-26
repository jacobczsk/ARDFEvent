from jinja2 import Environment, PackageLoader, select_autoescape
from sqlalchemy import Select
from sqlalchemy.orm import Session

from exports import html_common
from models import Category, Runner


def export(filename, db):
    sess = Session(db)
    categories = []
    categories_db = sess.scalars(Select(Category).order_by(Category.name.asc())).all()

    for category in categories_db:
        runners = []
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
            runners.append(
                {
                    "name": person.name,
                    "reg": person.reg,
                    "si": person.si,
                    "starttime": starttime,
                }
            )
        categories.append(
            {
                "name": category.name,
                "controls": category.display_controls,
                "runners": runners,
            }
        )

    sess.close()

    env = Environment(loader=PackageLoader("exports"), autoescape=select_autoescape())
    template = env.get_template("startlist.html")

    if not filename.endswith(".html"):
        filename += ".html"

    with open(filename, "w+") as f:
        f.write(template.render(event=html_common.get_event(db), categories=categories))
