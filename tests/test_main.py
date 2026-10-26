from main import (
    display_student_full_name,
    sort_students_by_assignment,
    student_photo_icon_color,
    student_surname_sort_key,
)


def test_display_student_full_name_shows_given_name_before_surnames():
    assert display_student_full_name("Aixalá Samit, José") == "José Aixalá Samit"
    assert display_student_full_name("") == ""


def test_student_surname_sort_key_sorts_abbreviated_names_by_surname():
    names = ["Zabala, A.", "Aixalá, J.", "Cañete, I."]

    assert sorted(names, key=student_surname_sort_key) == [
        "Aixalá, J.",
        "Cañete, I.",
        "Zabala, A.",
    ]


def test_student_surname_sort_key_handles_full_names_and_accents():
    names = ["José Aixalá", "Amin Aouzal", "Iker Cañete"]

    assert sorted(names, key=student_surname_sort_key) == [
        "José Aixalá",
        "Amin Aouzal",
        "Iker Cañete",
    ]


def test_students_are_grouped_by_assignment_and_sorted_by_surname_within_groups():
    students = [
        "Zabala, A.",
        "Aixalá, J.",
        "Cañete, I.",
        "Aouzal, A.",
    ]
    seated = {"Cañete, I.", "Aixalá, J."}

    assert sort_students_by_assignment(students, seated) == [
        "Aouzal, A.",
        "Zabala, A.",
        "Aixalá, J.",
        "Cañete, I.",
    ]


def test_student_sidebar_display_marks_students_with_assigned_photos():
    assert student_photo_icon_color(True) == "#526b80"
    assert student_photo_icon_color(False) == "#c9cdd1"
