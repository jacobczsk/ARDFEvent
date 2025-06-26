import xml.etree.ElementTree as ET

from dateutil import parser
from sqlalchemy import Select
from sqlalchemy.orm import Session

import api
import exports.xml_common as xml_common
from models import Category, Runner


def export(filename, db):
    root = xml_common.get_xml_root("StartList")
    tree = ET.ElementTree(root)

    basic_info = api.get_basic_info(db)

    event = ET.SubElement(root, "Event")
    ET.SubElement(event, "Name").text = basic_info["name"]
    starttime = ET.SubElement(event, "StartTime")
    xml_common.separated_time(starttime, parser.parse(basic_info["date_tzero"]))

    sess = Session(db)
    categories = sess.scalars(Select(Category).order_by(Category.name.asc())).all()

    for category in categories:
        cat_startlist = ET.SubElement(root, "ClassStart")
        category_node = ET.SubElement(cat_startlist, "Class")
        ET.SubElement(category_node, "Id").text = str(category.id)
        ET.SubElement(category_node, "Name").text = category.name
        ET.SubElement(category_node, "StartName").text = "Start 1"

        for person in sess.scalars(
            Select(Runner)
            .where(Runner.category == category)
            .order_by(Runner.startlist_time.asc())
        ).all():

            runner_start = ET.SubElement(cat_startlist, "PersonStart")
            runner = ET.SubElement(runner_start, "Person")

            id_index = ET.SubElement(runner, "Id")
            id_index.text = person.reg
            id_index.attrib["type"] = "CZE"

            id_index = ET.SubElement(runner, "Id")
            id_index.text = str(person.id)
            id_index.attrib["type"] = "ARDFE"

            runner_name = ET.SubElement(runner, "Name")
            ET.SubElement(runner_name, "Family").text = person.name.split(", ")[0]
            ET.SubElement(runner_name, "Given").text = person.name.split(", ")[1]

            ET.SubElement(ET.SubElement(runner_start, "Organisation"), "Name").text = (
                person.club
            )

            start = ET.SubElement(runner_start, "Start")
            ET.SubElement(start, "ControlCard").text = str(person.si)

            if starttime is not None:
                ET.SubElement(start, "StartTime").text = str(
                    person.startlist_time.isoformat()
                )

    sess.close()

    if not filename.endswith(".xml"):
        filename += ".xml"
    tree.write(filename, encoding="utf-8", xml_declaration=True)
