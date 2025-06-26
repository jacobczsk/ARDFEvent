import xml.etree.ElementTree as ET
from datetime import datetime


def get_xml_root(type: str):
    root = ET.Element(
        type,
        {
            "xmlns": "http://www.orienteering.org/datastandard/3.0",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "iofVersion": "3.0",
            "createTime": datetime.now().isoformat(timespec="seconds"),
            "creator": "ARDFEvent",
        },
    )
    return root


def separated_time(parent, time: datetime):
    ET.SubElement(parent, "Date").text = time.strftime("%Y-%m-%d")
    ET.SubElement(parent, "Time").text = time.strftime("%H:%M:%S%z")
