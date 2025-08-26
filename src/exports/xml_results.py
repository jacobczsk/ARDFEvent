import xml.etree.ElementTree as ET

from dateutil import parser
from sqlalchemy import Select
from sqlalchemy.orm import Session

import api
import exports.xml_common as xml_common
import results
from models import Category

IOF_STATUS = {
    "OK": "OK",
    "DNF": "DidNotFinish",
    "DSQ": "Disqualified",
    "MP": "MissingPunch",
    "DNS": "DidNotStart",
    "OVT": "OverTime",
}


def export(filename, db):
    root = xml_common.get_xml_root("Results")
    tree = ET.ElementTree(root)

    basic_info = api.get_basic_info(db)

    event = ET.SubElement(root, "Event")
    ET.SubElement(event, "Name").text = basic_info["name"]
    starttime = ET.SubElement(event, "StartTime")
    xml_common.separated_time(starttime, parser.parse(basic_info["date_tzero"]))

    sess = Session(db)
    categories = sess.scalars(Select(Category).order_by(Category.name.asc())).all()

    for category in categories:
        cat_course = ET.SubElement(root, "RaceCourseData")
        ET.SubElement(cat_course, "CourseFamily").text = category.name
        for control in category.controls:
            ET.SubElement(
                ET.SubElement(cat_course, "CourseControl"), "Control"
            ).text = control.name

    for category in categories:
        cat_res = ET.SubElement(root, "ClassResult")
        category_node = ET.SubElement(cat_res, "Class")
        ET.SubElement(category_node, "Id").text = str(category.id)
        ET.SubElement(category_node, "Name").text = category.name

        results_cat = results.calculate_category(db, category.name)

        for person in results_cat:
            person_res = ET.SubElement(cat_res, "PersonResult")
            runner = ET.SubElement(person_res, "Person")

            id_index = ET.SubElement(runner, "Id")
            id_index.text = person.reg
            id_index.attrib["type"] = "CZE"

            ET.SubElement(runner, "ControlCard").text = str(person.si)

            runner_name = ET.SubElement(runner, "Name")
            ET.SubElement(runner_name, "Family").text = person.name.split(", ")[0]
            ET.SubElement(runner_name, "Given").text = person.name.split(", ")[1]

            ET.SubElement(ET.SubElement(person_res, "Organisation"), "Name").text = (
                person.club
            )

            result = ET.SubElement(person_res, "Result")

            if person.start:
                ET.SubElement(result, "StartTime").text = person.start.isoformat()

            if person.finish:
                ET.SubElement(result, "FinishTime").text = person.finish.isoformat()

            ET.SubElement(result, "Time").text = (
                str(person.time) if person.status == "OK" else "0"
            )

            if person.status == "OK":
                ET.SubElement(result, "Position").text = str(person.place)

            start = person.start or parser.parse(basic_info["date_tzero"])
            for control in person.order:
                split = ET.SubElement(result, "SplitTime")
                ET.SubElement(split, "ControlCode").text = control[0]
                ET.SubElement(split, "Time").text = str((control[1] - start).seconds)

    sess.close()

    if not filename.endswith(".xml"):
        filename += ".xml"
    tree.write(filename, encoding="utf-8", xml_declaration=True)
