from datetime import datetime, timedelta

from sqlalchemy import Engine, Select
from sqlalchemy.orm import Session

import api
from models import Category, Punch


class Result:
    def __init__(
        self,
        name: str,
        reg: str,
        si: int,
        tx: int,
        time: int,
        status: str,
        order: list,
        club: str,
        start: datetime | None = None,
        finish: datetime | None = None,
    ):
        self.name = name
        self.reg = reg
        self.si = si
        self.tx = tx
        self.time = time
        self.status = status
        self.order = order
        self.place = 0
        self.club = club
        self.start = start
        self.finish = finish


def calculate_category(db: Engine, name: str, include_unknown: bool = False):
    limit = int(api.get_basic_info(db)["limit"])

    sess = Session(db)
    category = sess.scalars(Select(Category).where(Category.name == name)).first()

    results: list[Result] = []

    runners = category.runners
    controls = category.controls
    mandatory = list(map(lambda c: c.code, filter(lambda c: c.mandatory, controls)))
    cat_codes = list(map(lambda c: c.code, controls))

    for runner in runners:
        if runner.manual_dns:
            results.append(
                Result(
                    runner.name,
                    runner.reg,
                    runner.si,
                    0,
                    0,
                    "DNS",
                    [],
                    runner.club,
                    start,
                )
            )
            continue
        elif runner.manual_disk:
            results.append(
                Result(
                    runner.name,
                    runner.reg,
                    runner.si,
                    0,
                    0,
                    "DSQ",
                    [],
                    runner.club,
                    start,
                )
            )
            continue

        loc_controls = cat_codes.copy()
        loc_mandatory = mandatory.copy()

        tx = 0
        mandatory_cnt = 0
        start = runner.startlist_time
        finish = None

        punches = sess.scalars(Select(Punch).where(Punch.si == runner.si)).all()
        order = []

        if len(punches) == 0:
            if include_unknown:
                results.append(
                    Result(
                        runner.name,
                        runner.reg,
                        runner.si,
                        0,
                        0,
                        "?",
                        [],
                        runner.club,
                        start,
                    )
                )
            continue

        for punch in punches:
            if punch.code == 1000:
                start = punch.time
            elif punch.code == 1001:
                finish = punch.time
            elif punch.code in loc_controls:
                tx += 1
                control = list(filter(lambda c: c.code == punch.code, controls))
                order.append((control[0].name, punch.time))
            else:
                continue

            if punch.code in loc_mandatory:
                mandatory_cnt += 1
                try:
                    loc_mandatory.remove(punch.code)
                except:
                    ...

            try:
                loc_controls.remove(punch.code)
            except:
                ...

        status = "OK"

        if not start:
            start = api.get_basic_info(db)["date_tzero"]
        elif not finish:
            status = "DNF"
        else:
            time = (finish - start).seconds

        if len(mandatory) > mandatory_cnt or tx - mandatory_cnt < 1 and status == "OK":
            status = "MP"
        elif time > limit * 60:
            status = "OVT"

        results.append(
            Result(
                runner.name,
                runner.reg,
                runner.si,
                tx,
                time,
                status,
                order,
                runner.club,
                start,
                finish,
            )
        )

    ok = filter(lambda x: x.status == "OK", results)
    nok = list(filter(lambda x: x.status != "OK", results))
    nok.sort(key=lambda x: x.name)

    ok_dict = {}

    for runner in ok:
        if str(runner.tx) in ok_dict:
            ok_dict[str(runner.tx)].append(runner)
        else:
            ok_dict[str(runner.tx)] = [runner]

    keys = list(ok_dict.keys())
    keys.sort()
    keys.reverse()

    ok_dict = {i: ok_dict[i] for i in keys}

    final_results = []
    i = 0
    lastplace = 0

    for key in ok_dict:
        ok_dict[key].sort(key=lambda x: x.time)
        lasttime = 0
        for runner in ok_dict[key]:
            i += 1
            if not runner.time == lasttime:
                place = i
            else:
                place = lastplace
            runner.place = place
            lasttime = runner.time
            lastplace = place
        final_results += ok_dict[key]

    final_results += nok

    sess.close()

    return final_results


def format_delta(td: timedelta):
    mins = td.seconds // 60
    secs = td.seconds - mins * 60
    return f"{mins:02}:{secs:02}"
