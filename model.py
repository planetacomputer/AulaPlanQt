import random
from pathlib import Path


class AulaPlanModel:

    def __init__(self, rows=4, cols=4, vertical_aisle_after=0, vertical_aisles=None):
        self.rows = rows
        self.cols = cols
        if vertical_aisles is None:
            vertical_aisles = [vertical_aisle_after] if vertical_aisle_after else []
        self.vertical_aisles = self._normalize_aisles(vertical_aisles, cols)
        self.show_computer_status = True
        self.students = []
        self.grid = {}  # (row, col) -> student_name
        self.computer_working = {}  # (row, col) -> bool; missing entries default to working
        self.student_photos = {}  # student_name -> str path to photo file
        self.student_full_names = {}  # student_name -> surname(s), given name
        self.undo_stack = []
        self.redo_stack = []

    @staticmethod
    def _normalize_aisles(positions, cols):
        return sorted({
            int(position)
            for position in positions
            if 0 < int(position) < cols
        })

    @property
    def vertical_aisle_after(self):
        return self.vertical_aisles[0] if self.vertical_aisles else 0

    @vertical_aisle_after.setter
    def vertical_aisle_after(self, position):
        self.vertical_aisles = self._normalize_aisles(
            [position] if position else [],
            self.cols,
        )

    @staticmethod
    def _distributed_aisles(cols, count):
        count = min(max(int(count), 0), max(cols - 1, 0))
        return [
            (index * cols) // (count + 1)
            for index in range(1, count + 1)
        ]

    def save_state(self):
        state = {
            "rows": self.rows,
            "cols": self.cols,
            "vertical_aisles": list(self.vertical_aisles),
            "students": list(self.students),
            "grid": dict(self.grid),
            "computer_working": dict(self.computer_working),
            "student_photos": dict(self.student_photos),
            "student_full_names": dict(self.student_full_names),
        }
        self.undo_stack.append(state)
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return False
        current_state = {
            "rows": self.rows,
            "cols": self.cols,
            "vertical_aisles": list(self.vertical_aisles),
            "students": list(self.students),
            "grid": dict(self.grid),
            "computer_working": dict(self.computer_working),
            "student_photos": dict(self.student_photos),
            "student_full_names": dict(self.student_full_names),
        }
        self.redo_stack.append(current_state)

        prev_state = self.undo_stack.pop()
        self.rows = prev_state["rows"]
        self.cols = prev_state["cols"]
        self.vertical_aisles = prev_state.get(
            "vertical_aisles",
            [prev_state["vertical_aisle_after"]]
            if prev_state.get("vertical_aisle_after", 0)
            else [],
        )
        self.students = prev_state["students"]
        self.grid = prev_state["grid"]
        self.computer_working = prev_state.get("computer_working", {})
        self.student_photos = prev_state.get("student_photos", {})
        self.student_full_names = prev_state.get("student_full_names", {})
        return True

    def redo(self):
        if not self.redo_stack:
            return False
        current_state = {
            "rows": self.rows,
            "cols": self.cols,
            "vertical_aisles": list(self.vertical_aisles),
            "students": list(self.students),
            "grid": dict(self.grid),
            "computer_working": dict(self.computer_working),
            "student_photos": dict(self.student_photos),
            "student_full_names": dict(self.student_full_names),
        }
        self.undo_stack.append(current_state)

        next_state = self.redo_stack.pop()
        self.rows = next_state["rows"]
        self.cols = next_state["cols"]
        self.vertical_aisles = next_state.get(
            "vertical_aisles",
            [next_state["vertical_aisle_after"]]
            if next_state.get("vertical_aisle_after", 0)
            else [],
        )
        self.students = next_state["students"]
        self.grid = next_state["grid"]
        self.computer_working = next_state.get("computer_working", {})
        self.student_photos = next_state.get("student_photos", {})
        self.student_full_names = next_state.get("student_full_names", {})
        return True

    def set_grid_size(self, rows, cols, aisle_count):
        aisle_count = min(max(int(aisle_count), 0), max(cols - 1, 0))
        retained_aisles = [
            position for position in self.vertical_aisles
            if position < cols
        ]
        if len(retained_aisles) != aisle_count:
            retained_aisles = self._distributed_aisles(cols, aisle_count)

        changed = (
            self.rows != rows
            or self.cols != cols
            or self.vertical_aisles != retained_aisles
        )
        if changed:
            self.save_state()
        self.rows = rows
        self.cols = cols
        self.vertical_aisles = retained_aisles
        self.grid = {
            pos: name
            for pos, name in self.grid.items()
            if pos[0] < rows and pos[1] < cols
        }
        self.computer_working = {
            pos: working
            for pos, working in self.computer_working.items()
            if pos[0] < rows and pos[1] < cols
        }

    def move_vertical_aisle(self, source_position, target_position):
        if (
            source_position not in self.vertical_aisles
            or not 0 < target_position < self.cols
            or target_position in self.vertical_aisles
        ):
            return False
        if source_position == target_position:
            return True

        self.save_state()
        self.vertical_aisles.remove(source_position)
        self.vertical_aisles.append(target_position)
        self.vertical_aisles.sort()
        return True

    def set_computer_working(self, pos, working):
        working = bool(working)
        if self.computer_working.get(pos, True) != working:
            self.save_state()
            self.computer_working[pos] = working

    def add_student(self, name):
        name = name.strip()
        if name and name not in self.students:
            self.save_state()
            self.students.append(name)
            return True
        return False

    def set_student_photo(self, student_name, image_path):
        if student_name not in self.students:
            return False

        source = Path(image_path)
        if not source.exists() or not source.is_file():
            return False

        images_dir = Path(__file__).resolve().parent / "images"
        images_dir.mkdir(exist_ok=True)

        stem = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in student_name.strip())
        stem = stem.strip("_") or "student"
        suffix = source.suffix.lower() or ".png"
        dest = images_dir / f"{stem}{suffix}"
        if dest.exists() and str(dest) != str(source):
            dest.unlink()
        if str(source) != str(dest):
            import shutil
            shutil.copy2(source, dest)
        self.save_state()
        self.student_photos[student_name] = str(dest)
        return True

    def clear_student_photo(self, student_name):
        if student_name not in self.student_photos:
            return False

        self.save_state()
        del self.student_photos[student_name]
        return True

    def remove_student(self, name):
        if name in self.students:
            self.save_state()
            self.students.remove(name)
            self.grid = {
                pos: st for pos, st in self.grid.items() if st != name
            }
            self.student_photos.pop(name, None)
            self.student_full_names.pop(name, None)
            return True
        return False

    def rename_student(self, old_name, new_name):
        new_name = new_name.strip()
        if old_name not in self.students or not new_name:
            return False
        if new_name == old_name:
            return True
        if new_name in self.students:
            return False

        self.save_state()
        self.students[self.students.index(old_name)] = new_name
        self.grid = {
            pos: new_name if name == old_name else name
            for pos, name in self.grid.items()
        }
        if old_name in self.student_photos:
            photo_path = self.student_photos.pop(old_name)
            self.student_photos[new_name] = photo_path
        if old_name in self.student_full_names:
            full_name = self.student_full_names.pop(old_name)
            self.student_full_names[new_name] = full_name
        return True

    def move_or_swap(self, src_pos, dst_pos):
        self.save_state()
        src_student = self.grid.get(src_pos)
        dst_student = self.grid.get(dst_pos)

        if src_student:
            if dst_student:
                self.grid[src_pos] = dst_student
                self.grid[dst_pos] = src_student
            else:
                del self.grid[src_pos]
                self.grid[dst_pos] = src_student

    def assign_unseated(self, student_name, dst_pos):
        self.save_state()
        self.grid[dst_pos] = student_name

    def unseat_student(self, src_pos):
        if src_pos in self.grid:
            self.save_state()
            del self.grid[src_pos]
    
    def clear_all_seats(self):
        if self.grid:
            self.save_state()
            self.grid.clear()
            return True
        return False