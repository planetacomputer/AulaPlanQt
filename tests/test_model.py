import pytest

from model import AulaPlanModel


def test_add_student_strips_name_and_rejects_empty_or_duplicate_names():
    model = AulaPlanModel()

    assert model.add_student("  Ada Lovelace  ")
    assert not model.add_student("Ada Lovelace")
    assert not model.add_student("   ")
    assert model.students == ["Ada Lovelace"]


def test_move_swap_and_unseat_students():
    model = AulaPlanModel(rows=1, cols=2)
    model.assign_unseated("Ada", (0, 0))
    model.assign_unseated("Grace", (0, 1))

    model.move_or_swap((0, 0), (0, 1))
    assert model.grid == {(0, 0): "Grace", (0, 1): "Ada"}

    model.unseat_student((0, 0))
    assert model.grid == {(0, 1): "Ada"}


def test_resize_removes_out_of_bounds_seats_and_statuses():
    model = AulaPlanModel(rows=2, cols=2)
    model.assign_unseated("Ada", (1, 1))
    model.set_computer_working((1, 1), False)
    model.set_computer_working((0, 1), False)

    model.set_grid_size(1, 1, 0)

    assert model.grid == {}
    assert model.computer_working == {}


def test_rename_student_updates_seat_and_supports_undo_redo():
    model = AulaPlanModel(rows=1, cols=1)
    model.add_student("Ada")
    model.assign_unseated("Ada", (0, 0))

    assert model.rename_student("Ada", "  Ada Byron ")
    assert model.students == ["Ada Byron"]
    assert model.grid == {(0, 0): "Ada Byron"}

    assert model.undo()
    assert model.students == ["Ada"]
    assert model.grid == {(0, 0): "Ada"}

    assert model.redo()
    assert model.students == ["Ada Byron"]
    assert model.grid == {(0, 0): "Ada Byron"}


@pytest.mark.parametrize(
    ("old_name", "new_name"),
    [
        ("Ada", ""),
        ("Ada", "Grace"),
        ("Unknown", "New name"),
    ],
)
def test_rename_rejects_empty_duplicate_or_unknown_names(old_name, new_name):
    model = AulaPlanModel()
    model.add_student("Ada")
    model.add_student("Grace")

    assert not model.rename_student(old_name, new_name)
    assert model.students == ["Ada", "Grace"]


def test_computer_working_status_supports_undo_and_redo():
    model = AulaPlanModel(rows=1, cols=1)

    model.set_computer_working((0, 0), False)
    assert model.computer_working[(0, 0)] is False

    assert model.undo()
    assert model.computer_working.get((0, 0), True) is True

    assert model.redo()
    assert model.computer_working[(0, 0)] is False


def test_clear_all_seats_supports_undo():
    model = AulaPlanModel(rows=1, cols=1)
    model.assign_unseated("Ada", (0, 0))

    assert model.clear_all_seats()
    assert model.grid == {}
    assert model.undo()
    assert model.grid == {(0, 0): "Ada"}

