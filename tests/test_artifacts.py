"""Validate saved deliverables, not just in-memory model objects."""

import json
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import pytest
from src.data import ROOT

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def test_saved_workbook_cached_values_and_structure():
    model = json.loads((ROOT / "outputs/model.json").read_text())
    with ZipFile(ROOT / "models/acquisition_model.xlsx") as z:
        book = ET.fromstring(z.read("xl/workbook.xml"))
        sheets = book.find("m:sheets", NS)
        names = [s.attrib["name"] for s in sheets]
        assert len(names) == 16
        for name, cell, expected in [
            ("DCF", "D19", model["cases"]["base"]["dcf"]["enterprise_value"]),
            ("LBO", "D45", model["cases"]["base"]["lbo"]["irr"]),
        ]:
            xml = ET.fromstring(z.read(f"xl/worksheets/sheet{names.index(name)+1}.xml"))
            value = xml.find(f'.//m:c[@r="{cell}"]/m:v', NS)
            assert float(value.text) == pytest.approx(expected)
        for name in z.namelist():
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
                xml = ET.fromstring(z.read(name))
                assert not xml.findall('.//m:c[@t="e"]', NS), name
        assert any("/charts/" in p and p.endswith(".xml") for p in z.namelist())
        assert not any(p.startswith("xl/externalLinks/") for p in z.namelist())


def test_review_notebooks_execute():
    for path in (ROOT / "notebooks").glob("*.ipynb"):
        notebook = json.loads(path.read_text())
        scope = {}
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                code = cell["source"]
                exec("".join(code) if isinstance(code, list) else code, scope)
