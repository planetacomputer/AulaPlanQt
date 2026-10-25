import sys
from pathlib import Path
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag, QFont, QFontMetricsF, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QGridLayout, QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QSpinBox, QLabel, QCheckBox, QFileDialog, QMessageBox, QSplitter,
    QScrollArea, QFrame, QAbstractItemView, QInputDialog
)
from model import AulaPlanModel
from storage import AulaPlanStorage

class DraggableListWidget(QListWidget):
    """Llista personalitzada que transmet el nom de l'alumne en arrossegar"""
    def mimeData(self, items):
        mime = super().mimeData(items)
        if items:
            mime.setText(items[0].data(Qt.ItemDataRole.UserRole))
        return mime


class LeftPanelWidget(QWidget):
    """Panell esquerre adaptat per acceptar alumnes arrossegats des de la classe i desassignar-los"""
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith("seat:"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith("seat:"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        text = event.mimeData().text()
        event.acceptProposedAction()
        self.main_window.handle_unseat_drop(text)


class SeatFrame(QFrame):
    """Marc personalitzat per a cada seient que accepta Drag & Drop i permet arrossegar des d'ell"""
    def __init__(self, pos, student_name, main_window, parent=None):
        super().__init__(parent)
        self.seat_pos = pos
        self.student_name = student_name
        self.main_window = main_window
        self.setAcceptDrops(True)
        if self.student_name:
            self.setCursor(Qt.CursorShape.OpenHandCursor)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        text = event.mimeData().text()
        event.acceptProposedAction()
        self.main_window.handle_drop(text, self.seat_pos)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.student_name:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(f"seat:{self.seat_pos[0]},{self.seat_pos[1]}:{self.student_name}")
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.MoveAction)
        else:
            super().mousePressEvent(event)


class AulaPlanWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AulaPlan — Distribució de la Classe")
        icon_pixmap = QPixmap(64, 64)
        icon_pixmap.fill(Qt.GlobalColor.transparent)
        icon_font = QFont()
        icon_font.setPixelSize(52)
        icon_painter = QPainter(icon_pixmap)
        icon_painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        icon_painter.setFont(icon_font)
        icon_painter.drawText(
            icon_pixmap.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "🏫",
        )
        icon_painter.end()
        self.setWindowIcon(QIcon(icon_pixmap))
        self.resize(1850, 800)

        self.model = AulaPlanModel()
        self.highlighted_student = None

        self._build_ui()
        
        app_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        default_file = app_dir / "config_default.json"
        if AulaPlanStorage.load_default_json(default_file, self.model):
            # Bloquegem senyals per evitar rescriure el model amb valors per defecte
            self.spin_rows.blockSignals(True)
            self.spin_cols.blockSignals(True)
            self.chk_aisle.blockSignals(True)
            self.chk_computer_status.blockSignals(True)

            self.spin_rows.setValue(self.model.rows)
            self.spin_cols.setValue(self.model.cols)
            self.chk_aisle.setChecked(self.model.vertical_aisle_after > 0)
            self.chk_computer_status.setChecked(self.model.show_computer_status)

            self.spin_rows.blockSignals(False)
            self.spin_cols.blockSignals(False)
            self.chk_aisle.blockSignals(False)
            self.chk_computer_status.blockSignals(False)

            self.refresh_ui()

    def _build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- TOOLBAR ---
        toolbar = QHBoxLayout()
        
        btn_undo = QPushButton("↩ Desfer")
        btn_undo.clicked.connect(self.undo)
        toolbar.addWidget(btn_undo)

        btn_redo = QPushButton("↪ Refer")
        btn_redo.clicked.connect(self.redo)
        toolbar.addWidget(btn_redo)
        
        toolbar.addSpacing(10)
        toolbar.addWidget(QLabel("Files:"))
        self.spin_rows = QSpinBox()
        self.spin_rows.setRange(1, 10)
        self.spin_rows.setValue(self.model.rows)
        self.spin_rows.valueChanged.connect(self.update_grid_config)
        toolbar.addWidget(self.spin_rows)

        toolbar.addWidget(QLabel("Cols:"))
        self.spin_cols = QSpinBox()
        self.spin_cols.setRange(1, 10)
        self.spin_cols.setValue(self.model.cols)
        self.spin_cols.valueChanged.connect(self.update_grid_config)
        toolbar.addWidget(self.spin_cols)

        self.chk_aisle = QCheckBox("Passadís Vertical")
        self.chk_aisle.stateChanged.connect(self.update_grid_config)
        toolbar.addWidget(self.chk_aisle)

        self.chk_computer_status = QCheckBox("Mostrar estado ordenadores")
        self.chk_computer_status.setChecked(self.model.show_computer_status)
        self.chk_computer_status.toggled.connect(self.toggle_computer_status_visibility)
        toolbar.addWidget(self.chk_computer_status)

        toolbar.addStretch()

        btn_import = QPushButton("📂 Importar CSV")
        btn_import.clicked.connect(self.import_csv)
        toolbar.addWidget(btn_import)

        btn_html = QPushButton("🌐 Exportar HTML")
        btn_html.clicked.connect(self.export_html)
        toolbar.addWidget(btn_html)

        btn_svg = QPushButton("🎨 Exportar SVG")
        btn_svg.clicked.connect(self.export_svg)
        toolbar.addWidget(btn_svg)

        btn_save = QPushButton("💾 Desar JSON")
        btn_save.clicked.connect(self.save_json)
        toolbar.addWidget(btn_save)

        btn_load = QPushButton("📖 Carregar JSON")
        btn_load.clicked.connect(self.load_json)
        toolbar.addWidget(btn_load)

        main_layout.addLayout(toolbar)

        # --- SPLITTER PRINCIPAL ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # PANELL ESQUERRA: ALUMNES
        self.left_widget = LeftPanelWidget(self)
        left_layout = QVBoxLayout(self.left_widget)
        left_layout.addWidget(QLabel("<b>Llista d'Alumnes</b>"))

        entry_layout = QHBoxLayout()
        self.entry_student = QLineEdit()
        self.entry_student.setPlaceholderText("Nom de l'alumne...")
        self.entry_student.textChanged.connect(self.filter_students)
        self.entry_student.returnPressed.connect(self.add_student)
        entry_layout.addWidget(self.entry_student)

        btn_add = QPushButton("+")
        btn_add.setFixedWidth(30)
        btn_add.clicked.connect(self.add_student)
        entry_layout.addWidget(btn_add)
        left_layout.addLayout(entry_layout)

        self.listbox_students = DraggableListWidget()
        self.listbox_students.setDragEnabled(True)
        self.listbox_students.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.listbox_students.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.listbox_students.setStyleSheet("font-size: 14pt;")
        self.listbox_students.itemDoubleClicked.connect(self.rename_student)
        left_layout.addWidget(self.listbox_students)

        btn_remove = QPushButton("Eliminar Seleccionats")
        btn_remove.clicked.connect(self.remove_student)
        left_layout.addWidget(btn_remove)

        btn_unseat_all = QPushButton("Desassignar Tots els Seients")
        btn_unseat_all.clicked.connect(self.unseat_all_students)
        left_layout.addWidget(btn_unseat_all)

        splitter.addWidget(self.left_widget)

        # PANELL DRETA: GRAELLA DE L'AULA
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        board_lbl = QLabel("[ PISSARRA ]")
        board_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        board_lbl.setStyleSheet("font-size: 24px; background-color: #333; color: white; font-weight: bold; padding: 6px;")
        right_layout.addWidget(board_lbl)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.scroll_area.setWidget(self.grid_container)
        right_layout.addWidget(self.scroll_area)

        splitter.addWidget(right_widget)
        splitter.setSizes([250, 1000])

        self.refresh_ui()

    def refresh_ui(self):
        self.filter_students()

        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        aisle_col = self.model.vertical_aisle_after if self.chk_aisle.isChecked() else 0

        for r in range(self.model.rows):
            for c in range(self.model.cols):
                visual_c = c
                if aisle_col > 0 and c >= aisle_col:
                    visual_c = c + 1

                student_name = self.model.grid.get((r, c), "")
                is_highlighted = (student_name and student_name == self.highlighted_student)

                bg_color = "#2196f3" if is_highlighted else ("#e1f5fe" if student_name else "#f5f5f5")
                border_color = "#0d47a1" if is_highlighted else ("#90caf9" if student_name else "#cccccc")
                text_color = "white" if is_highlighted else ("#0d47a1" if student_name else "#bbbbbb")

                cell = SeatFrame((r, c), student_name, self)
                cell.setFixedSize(160, 80)
                cell.setStyleSheet(f"""
                    background-color: {bg_color};
                    border: 2px solid {border_color};
                    border-radius: 4px;
                """)
                
                cell_layout = QVBoxLayout(cell)
                cell_layout.setContentsMargins(1, 1, 1, 1)
                cell_layout.setSpacing(0)
                header_layout = QHBoxLayout()
                header_layout.setContentsMargins(2, 0, 2, 0)
                lbl_pos = QLabel(f"F{r+1}-C{c+1}")
                lbl_pos.setStyleSheet(f"color: {'white' if is_highlighted else '#777'}; font-weight: bold; border: none; background: transparent;")
                header_layout.addWidget(lbl_pos)

                computer_working = self.model.computer_working.get((r, c), True)
                chk_computer = QCheckBox("✓" if computer_working else "✗")
                chk_computer.setVisible(self.model.show_computer_status)
                chk_computer.setChecked(computer_working)
                chk_computer.setToolTip("Marca si l'ordinador funciona")
                chk_computer.setAccessibleName(f"Ordinador F{r+1}-C{c+1}")
                chk_computer.setStyleSheet("""
                    QCheckBox {
                        background: transparent;
                        border: none;
                        color: #d32f2f;
                        font-size: 18px;
                        font-weight: bold;
                    }
                    QCheckBox::indicator { width: 0; height: 0; }
                    QCheckBox:checked { color: #16803a; }
                """)
                chk_computer.toggled.connect(
                    lambda working, pos=(r, c), checkbox=chk_computer:
                    self.set_computer_status(pos, checkbox, working)
                )
                header_layout.addWidget(chk_computer)
                cell_layout.addLayout(header_layout)

                lbl_name = QLabel(student_name if student_name else "[ Buit ]")
                lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
                name_font = QFont()
                name_font.setPointSize(18)
                name_font.setBold(bool(student_name))
                available_width = cell.width() - 8
                name_width = QFontMetricsF(name_font).horizontalAdvance(lbl_name.text())
                if name_width > available_width:
                    name_font.setPointSizeF(
                        name_font.pointSizeF() * available_width / name_width
                    )
                    while (
                        name_font.pointSizeF() > 0.5
                        and QFontMetricsF(name_font).horizontalAdvance(lbl_name.text()) > available_width
                    ):
                        name_font.setPointSizeF(max(0.5, name_font.pointSizeF() - 0.1))
                lbl_name.setFont(name_font)
                lbl_name.setStyleSheet(f"color: {text_color}; border: none; background: transparent;")
                cell_layout.addWidget(lbl_name)

                self.grid_layout.addWidget(cell, r, visual_c)

        if aisle_col > 0:
            for r in range(self.model.rows):
                aisle_lbl = QLabel("│ │")
                aisle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                aisle_lbl.setStyleSheet("color: #ccc; font-size: 24pt;")
                self.grid_layout.addWidget(aisle_lbl, r, aisle_col)

    def set_computer_status(self, pos, checkbox, working):
        self.model.set_computer_working(pos, working)
        checkbox.setText("✓" if working else "✗")

    def toggle_computer_status_visibility(self, visible):
        self.model.show_computer_status = visible
        self.refresh_ui()

    def filter_students(self):
        query = self.entry_student.text().lower()
        self.listbox_students.clear()
        seated_students = set(self.model.grid.values())

        filtered = [name for name in self.model.students if query in name.lower()]
        def surname_sort_key(name):
            parts = name.split()
            second_part = parts[1] if len(parts) > 1 else name
            return second_part.casefold(), name.casefold()

        unseated_list = sorted(
            (name for name in filtered if name not in seated_students),
            key=surname_sort_key,
        )
        seated_list = sorted(
            (name for name in filtered if name in seated_students),
            key=surname_sort_key,
        )
        
        for name in unseated_list + seated_list:
            status_icon = "☑" if name in seated_students else "☐"
            item = QListWidgetItem(f"{status_icon}  {name}")
            item.setData(Qt.ItemDataRole.UserRole, name)
            if name == self.highlighted_student:
                item.setBackground(Qt.GlobalColor.blue)
            self.listbox_students.addItem(item)

    def handle_drop(self, mime_text, target_pos):
        if mime_text.startswith("seat:"):
            parts = mime_text.split(":", 2)
            coords = parts[1].split(",")
            src_pos = (int(coords[0]), int(coords[1]))
            
            if src_pos != target_pos:
                self.model.move_or_swap(src_pos, target_pos)
                self.refresh_ui()
        else:
            student_name = mime_text.split(" (")[0]
            
            already_seated_at = None
            for p, s in self.model.grid.items():
                if s == student_name:
                    already_seated_at = p
                    break
            
            if already_seated_at and already_seated_at != target_pos:
                QMessageBox.warning(self, "Seient ocupat", f"L'estudiant '{student_name}' ja està col·locat en un altre seient.")
                return
            
            self.model.assign_unseated(student_name, target_pos)
            self.highlighted_student = student_name
            self.refresh_ui()

    def handle_unseat_drop(self, mime_text):
        if mime_text.startswith("seat:"):
            parts = mime_text.split(":", 2)
            coords = parts[1].split(",")
            src_pos = (int(coords[0]), int(coords[1]))
            
            self.model.unseat_student(src_pos)
            self.refresh_ui()

    def add_student(self):
        name = self.entry_student.text().strip()
        if name:
            if self.model.add_student(name):
                self.entry_student.clear()
                self.refresh_ui()

    def rename_student(self, item=None):
        if item is None:
            selected_items = self.listbox_students.selectedItems()
            if len(selected_items) != 1:
                QMessageBox.information(
                    self,
                    "Editar nom",
                    "Fes doble clic sobre un alumne per editar-ne el nom.",
                )
                return
            item = selected_items[0]

        if not item:
            QMessageBox.information(
                self,
                "Editar nom",
                "Fes doble clic sobre un alumne per editar-ne el nom.",
            )
            return

        old_name = item.data(Qt.ItemDataRole.UserRole)
        new_name, accepted = QInputDialog.getText(
            self,
            "Editar nom",
            "Nom de l'alumne:",
            QLineEdit.EchoMode.Normal,
            old_name,
        )
        if not accepted:
            return

        new_name = new_name.strip()
        if not new_name:
            QMessageBox.warning(self, "Nom invàlid", "El nom no pot estar buit.")
            return
        if new_name == old_name:
            return
        if not self.model.rename_student(old_name, new_name):
            QMessageBox.warning(
                self,
                "Nom duplicat",
                f"Ja existeix un alumne amb el nom '{new_name}'.",
            )
            return

        if self.highlighted_student == old_name:
            self.highlighted_student = new_name
        self.refresh_ui()

    def remove_student(self):
        selected_items = self.listbox_students.selectedItems()
        if not selected_items:
            return

        count = len(selected_items)
        answer = QMessageBox.question(
            self,
            "Confirmar eliminació",
            f"Segur que vols eliminar els {count} estudiants seleccionats? "
            "També es desassignaran dels seus seients.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        for item in selected_items:
            name = item.data(Qt.ItemDataRole.UserRole)
            self.model.remove_student(name)
        self.refresh_ui()

    def unseat_all_students(self):
        if self.model.grid:
            if QMessageBox.question(self, "Confirmar", "Segur que vols treure tots els estudiants?") == QMessageBox.StandardButton.Yes:
                self.model.save_state()
                self.model.grid.clear()
                self.refresh_ui()

    def update_grid_config(self):
        r = self.spin_rows.value()
        c = self.spin_cols.value()
        aisle_active = self.chk_aisle.isChecked()
        aisle_pos = (c // 2 if c > 1 else 1) if aisle_active else 0
        self.model.set_grid_size(r, c, aisle_pos)
        self.refresh_ui()

    def undo(self):
        if self.model.undo():
            self.spin_rows.setValue(self.model.rows)
            self.spin_cols.setValue(self.model.cols)
            self.chk_aisle.setChecked(self.model.vertical_aisle_after > 0)
            self.chk_computer_status.setChecked(self.model.show_computer_status)
            self.refresh_ui()

    def redo(self):
        if self.model.redo():
            self.spin_rows.setValue(self.model.rows)
            self.spin_cols.setValue(self.model.cols)
            self.chk_aisle.setChecked(self.model.vertical_aisle_after > 0)
            self.chk_computer_status.setChecked(self.model.show_computer_status)
            self.refresh_ui()

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importar CSV", "", "Fitxers CSV (*.csv)")
        if path:
            AulaPlanStorage.import_csv(path, self.model)
            self.refresh_ui()

    def export_svg(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exportar SVG", "", "Fitxers SVG (*.svg)")
        if path:
            if not path.lower().endswith(".svg"):
                path += ".svg"
            AulaPlanStorage.export_svg(path, self.model)
            QMessageBox.information(self, "Èxit", "Fitxer SVG exportat correctament!")

    def export_html(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exportar HTML", "", "Fitxers HTML (*.html)")
        if path:
            if not path.lower().endswith(".html"):
                path += ".html"
            AulaPlanStorage.export_html(path, self.model)
            QMessageBox.information(self, "Èxit", "Fitxer HTML exportat correctament!")

    def save_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Desar JSON", "", "Fitxers JSON (*.json)")
        if path:
            AulaPlanStorage.save_json(path, self.model)

    def load_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Carregar JSON", "", "Fitxers JSON (*.json)")
        if path:
            AulaPlanStorage.load_json(path, self.model)
            
            # Bloquegem senyals aquí també
            self.spin_rows.blockSignals(True)
            self.spin_cols.blockSignals(True)
            self.chk_aisle.blockSignals(True)
            self.chk_computer_status.blockSignals(True)

            self.spin_rows.setValue(self.model.rows)
            self.spin_cols.setValue(self.model.cols)
            self.chk_aisle.setChecked(self.model.vertical_aisle_after > 0)
            self.chk_computer_status.setChecked(self.model.show_computer_status)

            self.spin_rows.blockSignals(False)
            self.spin_cols.blockSignals(False)
            self.chk_aisle.blockSignals(False)
            self.chk_computer_status.blockSignals(False)

            self.refresh_ui()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AulaPlanWindow()
    window.show()
    sys.exit(app.exec())