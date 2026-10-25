import json
import xml.etree.ElementTree as ET

import pytest

from model import AulaPlanModel
from storage import AulaPlanStorage


def test_json_round_trip_preserves_class_and_computer_status(tmp_path):
    model = AulaPlanModel(rows=1, cols=2, vertical_aisle_after=1)
    model.add_student("Ada")
    model.assign_unseated("Ada", (0, 0))
    model.set_computer_working((0, 1), False)
    model.show_computer_status = False
    json_path = tmp_path / "class.json"

    AulaPlanStorage.save_json(json_path, model)

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["show_computer_status"] is False
    assert data["computer_working"] == {"0,0": True, "0,1": False}

    loaded = AulaPlanModel()
    AulaPlanStorage.load_json(json_path, loaded)
    assert loaded.rows == 1
    assert loaded.cols == 2
    assert loaded.vertical_aisle_after == 1
    assert loaded.students == ["Ada"]
    assert loaded.grid == {(0, 0): "Ada"}
    assert loaded.computer_working == {(0, 0): True, (0, 1): False}
    assert loaded.show_computer_status is False


def test_loading_legacy_json_defaults_computer_status_to_visible_and_working(
    tmp_path,
):
    json_path = tmp_path / "legacy.json"
    json_path.write_text(
        json.dumps(
            {
                "rows": 1,
                "cols": 2,
                "vertical_aisle": True,
                "students": [],
                "grid": {},
            }
        ),
        encoding="utf-8",
    )
    model = AulaPlanModel()

    AulaPlanStorage.load_json(json_path, model)

    assert model.vertical_aisle_after == 1
    assert model.show_computer_status is True
    assert model.computer_working == {}
    assert model.computer_working.get((0, 0), True) is True


def test_import_csv_adds_unique_nonempty_student_names(tmp_path):
    csv_path = tmp_path / "students.csv"
    csv_path.write_text("Ada Lovelace\nGrace Hopper\n\nAda Lovelace\n", encoding="utf-8")
    model = AulaPlanModel()

    AulaPlanStorage.import_csv(csv_path, model)

    assert model.students == ["Ada Lovelace", "Grace Hopper"]


@pytest.mark.parametrize(
    ("visible", "expected_icons"),
    [
        (True, {"working": "✓", "not-working": "✗"}),
        (False, {}),
    ],
)
def test_html_export_respects_status_visibility_and_state(
    tmp_path, visible, expected_icons
):
    model = AulaPlanModel(rows=1, cols=2)
    model.set_computer_working((0, 1), False)
    model.show_computer_status = visible
    html_path = tmp_path / "class.html"

    AulaPlanStorage.export_html(html_path, model)

    exported = html_path.read_text(encoding="utf-8")
    if visible:
        assert 'class="computer-status working"' in exported
        assert 'class="computer-status not-working"' in exported
        assert ">✓</span>" in exported
        assert ">✗</span>" in exported
    else:
        assert 'class="computer-status' not in exported
        assert ">✓</span>" not in exported
        assert ">✗</span>" not in exported


def test_html_export_escapes_student_names(tmp_path):
    model = AulaPlanModel(rows=1, cols=1)
    model.assign_unseated("<Ada & Grace>", (0, 0))
    html_path = tmp_path / "class.html"

    AulaPlanStorage.export_html(html_path, model)

    exported = html_path.read_text(encoding="utf-8")
    assert "&lt;Ada &amp; Grace&gt;" in exported
    assert "<Ada & Grace>" not in exported


@pytest.mark.parametrize(
    ("visible", "expected_colors"),
    [
        (True, {"#16803a", "#d32f2f"}),
        (False, set()),
    ],
)
def test_svg_export_respects_status_visibility_and_colors(
    tmp_path, visible, expected_colors
):
    model = AulaPlanModel(rows=1, cols=2)
    model.set_computer_working((0, 1), False)
    model.show_computer_status = visible
    svg_path = tmp_path / "class.svg"

    AulaPlanStorage.export_svg(svg_path, model)

    root = ET.parse(svg_path).getroot()
    paths = [
        element for element in root.iter()
        if element.tag.endswith("path")
    ]
    assert {element.get("stroke") for element in paths} == expected_colors

