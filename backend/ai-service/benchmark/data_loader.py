"""
Normalizes fake student records from three different source formats
(JSON, CSV, XML) into one common schema — simulating real institutions
exporting data differently.
"""
import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict

SOURCES_DIR = Path(__file__).parent.parent / "app" / "data" / "sources"


def load_json_source(filename: str) -> List[Dict]:
    path = SOURCES_DIR / filename
    return json.loads(path.read_text())


def load_csv_source(filename: str) -> List[Dict]:
    path = SOURCES_DIR / filename
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_xml_source(filename: str) -> List[Dict]:
    path = SOURCES_DIR / filename
    tree = ET.parse(path)
    root = tree.getroot()
    records = []
    for record in root.findall("record"):
        records.append({
            "student_id": record.attrib["student_id"],
            "prior_institution": record.attrib["institution"],
            "expected_mapping": record.attrib["expected_mapping"],
            "prior_course_title": record.find("course_title").text.strip(),
            "prior_course_description": record.find("course_description").text.strip(),
        })
    return records


def load_all_sources() -> List[Dict]:
    """Combined, normalized dataset from all three fake institution sources."""
    records = []
    records += load_json_source("institution_a.json")
    records += load_csv_source("institution_b.csv")
    records += load_xml_source("institution_c.xml")
    return records


if __name__ == "__main__":
    data = load_all_sources()
    print(f"Loaded {len(data)} records from 3 source formats (JSON, CSV, XML):\n")
    for r in data:
        print(f"  [{r['prior_institution']}] {r['prior_course_title']} -> expected {r['expected_mapping']}")
