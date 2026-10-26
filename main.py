import sys
from pathlib import Path
from PyQt6.QtCore import Qt, QEvent, QItemSelectionModel, QMimeData
from PyQt6.QtGui import QBrush, QDrag, QFont, QFontMetricsF, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QGridLayout, QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QSpinBox, QLabel, QCheckBox, QFileDialog, QMessageBox, QSplitter,
    QScrollArea, QFrame, QAbstractItemView, QInputDialog, QDialog,
    QDialogButtonBox, QTextBrowser, QStyle
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

    def selectionCommand(self, index, event=None):
        if event is None:
            return super().selectionCommand(index, event)
        if event.type() == QEvent.Type.MouseMove:
            return QItemSelectionModel.SelectionFlag.NoUpdate

        modifiers = event.modifiers()
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            return super().selectionCommand(index, event)
        return (
            QItemSelectionModel.SelectionFlag.ClearAndSelect
            | QItemSelectionModel.SelectionFlag.Current
        )


class LeftPanelWidget(QWidget):
    """Panell esquerre adaptat per acceptar alumnes arrossegats des de la classe i desassignar-los"""
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith(
            ("seat:", "seats:")
        ):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith(
            ("seat:", "seats:")
        ):
            event.acceptProposedAction()

    def dropEvent(self, event):
        text = event.mimeData().text()
        event.acceptProposedAction()
        self.main_window.handle_unseat_drop(text)


class StudentPhotoDropWidget(QLabel):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setFixedSize(120, 180)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            "background: #f3f3f3; border: 2px dashed #888; border-radius: 8px; color: #333; font-size: 11pt;"
        )
        self.setText("Arrastra la foto\n120×180")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return
        file_path = urls[0].toLocalFile()
        if file_path:
            self.main_window.attach_photo_to_selected_student(file_path)
            event.acceptProposedAction()

    def set_photo(self, photo_path):
        pixmap = QPixmap(photo_path)
        if pixmap.isNull():
            self.setText("Foto no válida")
            return
        scaled = pixmap.scaled(
            self.width(),
            self.height(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(scaled)
        self.setStyleSheet("background: transparent; border: 1px solid #ccc; border-radius: 8px;")

    def set_placeholder(self, name):
        self.clear()
        self.setPixmap(QPixmap())
        self.setText(f"{name}\nSin foto")
        self.setStyleSheet(
            "background: #f3f3f3; border: 2px dashed #888; border-radius: 8px; color: #333; font-size: 11pt;"
        )


class SeatComputerCheckBox(QCheckBox):
    def __init__(self, student_name, main_window, parent=None):
        super().__init__(parent)
        self.student_name = student_name
        self.main_window = main_window
        self._selecting_seat = False

    def mousePressEvent(self, event):
        if (
            self.student_name
            and event.button() == Qt.MouseButton.LeftButton
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self.main_window.select_student_from_seat(
                self.student_name,
                event.modifiers(),
            )
            self._selecting_seat = True
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._selecting_seat:
            self._selecting_seat = False
            event.accept()
            return
        super().mouseReleaseEvent(event)


class SeatFrame(QFrame):
    """Marc personalitzat per a cada seient que accepta Drag & Drop i permet arrossegar des d'ell"""
    def __init__(self, pos, student_name, main_window, parent=None):
        super().__init__(parent)
        self.seat_pos = pos
        self.student_name = student_name
        self.main_window = main_window
        self._press_position = None
        self._press_modifiers = Qt.KeyboardModifier.NoModifier
        self._drag_started = False
        self.setAcceptDrops(True)
        if self.student_name:
            self.setCursor(Qt.CursorShape.OpenHandCursor)

    def dragEnterEvent(self, event):
        if self.main_window.accepts_drop(event.mimeData()):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if self.main_window.accepts_drop(event.mimeData()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        text = event.mimeData().text()
        event.acceptProposedAction()
        target_pos = self.seat_pos
        if text.startswith("aisle:"):
            target_pos = (
                self.seat_pos[1]
                if event.position().x() < self.width() / 2
                else self.seat_pos[1] + 1
            )
        self.main_window.handle_drop(text, target_pos)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.student_name:
            self._press_position = event.position().toPoint()
            self._press_modifiers = event.modifiers()
            self._drag_started = False
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            self._press_position is not None
            and event.buttons() & Qt.MouseButton.LeftButton
            and (event.position().toPoint() - self._press_position).manhattanLength()
            >= QApplication.startDragDistance()
        ):
            self._drag_started = True
            selected_students = {
                item.data(Qt.ItemDataRole.UserRole)
                for item in self.main_window.listbox_students.selectedItems()
            }
            if self.student_name not in selected_students:
                self.main_window.select_student_from_seat(
                    self.student_name,
                    self._press_modifiers,
                )
                selected_students = {
                    item.data(Qt.ItemDataRole.UserRole)
                    for item in self.main_window.listbox_students.selectedItems()
                }

            selected_positions = sorted(
                pos
                for pos, name in self.main_window.model.grid.items()
                if name in selected_students
            )
            drag = QDrag(self)
            mime = QMimeData()
            if len(selected_positions) > 1:
                positions = ";".join(
                    f"{row},{col}" for row, col in selected_positions
                )
                mime.setText(f"seats:{positions}")
            else:
                mime.setText(
                    f"seat:{self.seat_pos[0]},{self.seat_pos[1]}:{self.student_name}"
                )
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.MoveAction)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.student_name:
            if not self._drag_started:
                self.main_window.select_student_from_seat(
                    self.student_name,
                    self._press_modifiers,
                )
            self._press_position = None
            self._press_modifiers = Qt.KeyboardModifier.NoModifier
            self._drag_started = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class AisleHandle(QLabel):
    def __init__(self, position, rows, main_window, parent=None):
        super().__init__("\n".join("│" for _ in range(rows)), parent)
        self.position = position
        self.main_window = main_window
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("color: #999; font-size: 24pt;")
        self.setToolTip("Arrossega el passadís a una altra separació entre columnes")
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setAcceptDrops(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(f"aisle:{self.position}")
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
            self.spin_aisles.blockSignals(True)
            self.chk_computer_status.blockSignals(True)

            self.spin_rows.setValue(self.model.rows)
            self.spin_cols.setValue(self.model.cols)
            self.spin_aisles.setMaximum(max(self.model.cols - 1, 0))
            self.spin_aisles.setValue(len(self.model.vertical_aisles))
            self.chk_computer_status.setChecked(self.model.show_computer_status)

            self.spin_rows.blockSignals(False)
            self.spin_cols.blockSignals(False)
            self.spin_aisles.blockSignals(False)
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

        toolbar.addWidget(QLabel("Passadissos:"))
        self.spin_aisles = QSpinBox()
        self.spin_aisles.setRange(0, self.model.cols - 1)
        self.spin_aisles.setToolTip(
            "Nombre de passadissos verticals; arrossega'ls per canviar-ne la posició"
        )
        self.spin_aisles.valueChanged.connect(self.update_grid_config)
        toolbar.addWidget(self.spin_aisles)

        self.chk_computer_status = QCheckBox("Mostra l'estat dels ordinadors")
        self.chk_computer_status.setChecked(self.model.show_computer_status)
        self.chk_computer_status.toggled.connect(self.toggle_computer_status_visibility)
        toolbar.addWidget(self.chk_computer_status)

        btn_help = QPushButton("Guia ràpida")
        btn_help.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
        )
        btn_help.setToolTip("Obre la guia ràpida")
        btn_help.setAccessibleName("Guia ràpida")
        btn_help.clicked.connect(self.show_quick_guide)
        toolbar.addWidget(btn_help)

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
        self.listbox_students.itemChanged.connect(self.on_student_check_toggled)
        self.listbox_students.itemSelectionChanged.connect(
            self.on_student_selection_changed
        )
        left_layout.addWidget(self.listbox_students)

        self.photo_label = QLabel("Foto del carnet")
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(self.photo_label)
        self.student_photo_panel = StudentPhotoDropWidget(self)
        self.student_photo_panel.setToolTip("Arrossega una foto 120×180 aquí per assignar-la a l'alumne seleccionat")
        left_layout.addWidget(self.student_photo_panel, alignment=Qt.AlignmentFlag.AlignCenter)

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

    def show_quick_guide(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Guia ràpida d'AulaPlan")
        dialog.resize(640, 560)

        layout = QVBoxLayout(dialog)
        guide = QTextBrowser(dialog)
        guide.setOpenExternalLinks(False)
        guide.setHtml("""
            <h1>Guia ràpida d'AulaPlan</h1>
            <p>Organitzeu l'aula, assigneu alumnes i indiqueu l'estat
            dels ordinadors des d'una sola pantalla.</p>

            <h2>Alumnes</h2>
            <ul>
                <li>Escriviu un nom al camp de l'esquerra i premeu
                <b>+</b> o <i>Retorn</i> per afegir-lo.</li>
                <li>Feu doble clic sobre un alumne per editar-ne el nom.
                El canvi també es reflecteix al seu seient.</li>
                <li>Seleccioneu un o diversos alumnes i premeu
                <b>Eliminar Seleccionats</b> per eliminar-los. Els seients
                dels alumnes seleccionats queden ressaltats.</li>
            </ul>

            <h2>Seients</h2>
            <ul>
                <li>Arrossegueu un alumne de la llista fins a un seient lliure.</li>
                <li>Feu clic sobre un seient per seleccionar l'alumne.
                Feu Ctrl+clic a la llista o als seients per afegir o treure
                alumnes de la selecció; és l'única manera de fer una
                multiselecció. Arrossegueu qualsevol seient seleccionat fins
                al panell esquerre per desassignar tots els seients
                seleccionats alhora.</li>
                <li>Arrossegueu un alumne d'un seient a un altre per moure'l
                o intercanviar-lo.</li>
                <li>Arrossegueu un alumne des del seu seient fins al panell de
                l'esquerra per deixar-lo sense assignar.</li>
                <li>Feu servir els controls <b>Files</b>, <b>Cols</b> i
                <b>Passadissos</b> per configurar la graella. Arrossegueu un
                passadís vertical fins a una altra separació entre columnes
                per canviar-ne la posició. Es pot col·locar com a màxim un
                passadís a cada separació.</li>
            </ul>

            <h2>Estat dels ordinadors</h2>
            <ul>
                <li>Premeu l'indicador de cada seient per alternar entre
                <span style="color:#16803a"><b>✓ funciona</b></span> i
                <span style="color:#d32f2f"><b>✗ no funciona</b></span>.</li>
                <li>Desmarqueu <b>Mostra l'estat dels ordinadors</b> per amagar
                els indicadors sense canviar-ne l'estat. També s'amaguen
                a les exportacions HTML i SVG.</li>
            </ul>

            <h2>Desar, carregar i exportar</h2>
            <ul>
                <li><b>Importar CSV</b> carrega alumnes des d'un fitxer CSV.</li>
                <li><b>Desar JSON</b> i <b>Carregar JSON</b> desen i recuperen
                la distribució i l'estat dels ordinadors.</li>
                <li><b>Exportar HTML</b> crea una pàgina imprimible i
                <b>Exportar SVG</b> crea un gràfic vectorial.</li>
            </ul>

            <h2>Desfer i refer</h2>
            <p>Feu servir <b>Desfer</b> i <b>Refer</b> per desfer o recuperar canvis.</p>
        """)
        layout.addWidget(guide)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, dialog)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    @property
    def selected_student_name(self):
        current_item = self.listbox_students.currentItem()
        if current_item is None:
            return None
        return current_item.data(Qt.ItemDataRole.UserRole)

    def attach_photo_to_selected_student(self, file_path):
        student_name = self.selected_student_name
        if student_name is None:
            QMessageBox.warning(self, "Selecció requerida", "Selecciona primer un alumne de la llista.")
            return False
        if self.model.set_student_photo(student_name, file_path):
            self.refresh_ui()
            return True
        QMessageBox.warning(self, "Foto no vàlida", "La imatge no és vàlida o no s'ha pogut guardar.")
        return False

    def update_selected_student_photo(self):
        student_name = self.selected_student_name
        if student_name is None:
            self.student_photo_panel.setText("Selecciona un alumne")
            return
        photo_path = self.model.student_photos.get(student_name)
        if photo_path and Path(photo_path).exists():
            self.student_photo_panel.set_photo(photo_path)
        else:
            self.student_photo_panel.set_placeholder(student_name)

    def refresh_ui(self, refresh_students=True):
        if refresh_students:
            self.filter_students()

        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        aisle_positions = self.model.vertical_aisles
        selected_students = {
            item.data(Qt.ItemDataRole.UserRole)
            for item in self.listbox_students.selectedItems()
        }

        for r in range(self.model.rows):
            for c in range(self.model.cols):
                visual_c = c + sum(position <= c for position in aisle_positions)

                student_name = self.model.grid.get((r, c), "")
                is_highlighted = student_name in selected_students

                bg_color = "#2196f3" if is_highlighted else ("#e1f5fe" if student_name else "#f5f5f5")
                border_color = "#0d47a1" if is_highlighted else ("#90caf9" if student_name else "#cccccc")
                text_color = "white" if is_highlighted else ("#0d47a1" if student_name else "#bbbbbb")

                cell = SeatFrame((r, c), student_name, self)
                cell.setFixedSize(160, 120)
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
                lbl_pos.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                lbl_pos.setStyleSheet(f"color: {'white' if is_highlighted else '#777'}; font-weight: bold; border: none; background: transparent;")
                header_layout.addWidget(lbl_pos)

                computer_working = self.model.computer_working.get((r, c), True)
                chk_computer = SeatComputerCheckBox(
                    student_name,
                    self,
                )
                chk_computer.setText("✓" if computer_working else "✗")
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

                photo_path = self.model.student_photos.get(student_name) if student_name else None
                if photo_path and Path(photo_path).exists():
                    photo_label = QLabel()
                    photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    pixmap = QPixmap(photo_path)
                    scaled = pixmap.scaled(
                        100,
                        120,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    photo_label.setPixmap(scaled)
                    cell_layout.addWidget(photo_label)
                else:
                    lbl_name = QLabel(student_name if student_name else "[ Buit ]")
                    lbl_name.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
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

        for index, position in enumerate(aisle_positions):
            visual_c = position + index
            aisle_handle = AisleHandle(position, self.model.rows, self)
            self.grid_layout.addWidget(
                aisle_handle,
                0,
                visual_c,
                self.model.rows,
                1,
            )

        self.update_selected_student_photo()

    def set_computer_status(self, pos, checkbox, working):
        self.model.set_computer_working(pos, working)
        checkbox.setText("✓" if working else "✗")

    def toggle_computer_status_visibility(self, visible):
        self.model.show_computer_status = visible
        self.refresh_ui()

    def accepts_drop(self, mime_data):
        if not mime_data.hasText():
            return False
        text = mime_data.text()
        return (
            text.startswith("seat:")
            or text.startswith("aisle:")
            or text in self.model.students
        )

    def filter_students(self):
        query = self.entry_student.text().lower()
        selected_names = {
            item.data(Qt.ItemDataRole.UserRole)
            for item in self.listbox_students.selectedItems()
        }
        current_item = self.listbox_students.currentItem()
        current_name = (
            current_item.data(Qt.ItemDataRole.UserRole)
            if current_item
            else None
        )
        signals_were_blocked = self.listbox_students.blockSignals(True)
        try:
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
                item = QListWidgetItem(name)
                item.setData(Qt.ItemDataRole.UserRole, name)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(
                    Qt.CheckState.Checked
                    if name in seated_students
                    else Qt.CheckState.Unchecked
                )
                if name == self.highlighted_student:
                    item.setBackground(Qt.GlobalColor.blue)
                self.listbox_students.addItem(item)
                if name in selected_names:
                    item.setSelected(True)
                if name == current_name:
                    self.listbox_students.setCurrentItem(
                        item,
                        QItemSelectionModel.SelectionFlag.NoUpdate,
                    )
        finally:
            self.listbox_students.blockSignals(signals_were_blocked)

    def on_student_check_toggled(self, item):
        if item is None:
            return

        student_name = item.data(Qt.ItemDataRole.UserRole)
        if student_name is None:
            return

        is_seated = student_name in self.model.grid.values()
        if item.checkState() == Qt.CheckState.Checked:
            if not is_seated:
                item.setCheckState(Qt.CheckState.Unchecked)
            return

        if is_seated:
            for seat_pos, assigned_student in list(self.model.grid.items()):
                if assigned_student == student_name:
                    self.model.unseat_student(seat_pos)
                    break
            self.refresh_ui()

    def on_student_selection_changed(self):
        selected_items = self.listbox_students.selectedItems()
        current_item = self.listbox_students.currentItem()
        if current_item not in selected_items:
            current_item = selected_items[-1] if selected_items else None

        selected_student = (
            current_item.data(Qt.ItemDataRole.UserRole)
            if current_item
            else None
        )
        previous_student = self.highlighted_student
        self.highlighted_student = selected_student
        for index in range(self.listbox_students.count()):
            item = self.listbox_students.item(index)
            name = item.data(Qt.ItemDataRole.UserRole)
            if name == previous_student:
                item.setBackground(QBrush())
            if name == selected_student:
                item.setBackground(Qt.GlobalColor.blue)
        self.update_selected_student_photo()
        self.refresh_ui(refresh_students=False)

    def select_student_from_seat(
        self,
        student_name,
        modifiers=Qt.KeyboardModifier.NoModifier,
    ):
        item = next(
            (
                self.listbox_students.item(index)
                for index in range(self.listbox_students.count())
                if self.listbox_students.item(index).data(
                    Qt.ItemDataRole.UserRole
                ) == student_name
            ),
            None,
        )
        if item is None and student_name in self.model.students:
            self.entry_student.clear()
            item = next(
                (
                    self.listbox_students.item(index)
                    for index in range(self.listbox_students.count())
                    if self.listbox_students.item(index).data(
                        Qt.ItemDataRole.UserRole
                    ) == student_name
                ),
                None,
            )

        if item is not None:
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                selection_command = (
                    QItemSelectionModel.SelectionFlag.Toggle
                    | QItemSelectionModel.SelectionFlag.Current
                )
            else:
                selection_command = (
                    QItemSelectionModel.SelectionFlag.ClearAndSelect
                    | QItemSelectionModel.SelectionFlag.Current
                )

            signals_were_blocked = self.listbox_students.blockSignals(True)
            try:
                self.listbox_students.setCurrentItem(item, selection_command)
            finally:
                self.listbox_students.blockSignals(signals_were_blocked)
            self.on_student_selection_changed()

    def handle_drop(self, mime_text, target_pos):
        if mime_text.startswith("aisle:"):
            source_position = int(mime_text.split(":", 1)[1])
            self.move_vertical_aisle(source_position, target_pos)
        elif mime_text.startswith("seat:"):
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
        if mime_text.startswith("seats:"):
            positions = [
                tuple(map(int, coords.split(",")))
                for coords in mime_text.split(":", 1)[1].split(";")
                if coords
            ]
            positions = [pos for pos in positions if pos in self.model.grid]
            if positions:
                self.model.save_state()
                for pos in positions:
                    del self.model.grid[pos]
                self.refresh_ui()
        elif mime_text.startswith("seat:"):
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
        self.spin_aisles.blockSignals(True)
        self.spin_aisles.setMaximum(max(c - 1, 0))
        aisle_count = self.spin_aisles.value()
        self.spin_aisles.blockSignals(False)
        self.model.set_grid_size(r, c, aisle_count)
        self.refresh_ui()

    def move_vertical_aisle(self, source_position, target_position):
        if self.model.move_vertical_aisle(source_position, target_position):
            self.refresh_ui()

    def undo(self):
        if self.model.undo():
            self.update_controls_from_model()
            self.refresh_ui()

    def redo(self):
        if self.model.redo():
            self.update_controls_from_model()
            self.refresh_ui()

    def update_controls_from_model(self):
        for control in (
            self.spin_rows,
            self.spin_cols,
            self.spin_aisles,
            self.chk_computer_status,
        ):
            control.blockSignals(True)
        self.spin_rows.setValue(self.model.rows)
        self.spin_cols.setValue(self.model.cols)
        self.spin_aisles.setMaximum(max(self.model.cols - 1, 0))
        self.spin_aisles.setValue(len(self.model.vertical_aisles))
        self.chk_computer_status.setChecked(self.model.show_computer_status)
        for control in (
            self.spin_rows,
            self.spin_cols,
            self.spin_aisles,
            self.chk_computer_status,
        ):
            control.blockSignals(False)

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
            self.spin_aisles.blockSignals(True)
            self.chk_computer_status.blockSignals(True)

            self.spin_rows.setValue(self.model.rows)
            self.spin_cols.setValue(self.model.cols)
            self.spin_aisles.setMaximum(max(self.model.cols - 1, 0))
            self.spin_aisles.setValue(len(self.model.vertical_aisles))
            self.chk_computer_status.setChecked(self.model.show_computer_status)

            self.spin_rows.blockSignals(False)
            self.spin_cols.blockSignals(False)
            self.spin_aisles.blockSignals(False)
            self.chk_computer_status.blockSignals(False)

            self.refresh_ui()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AulaPlanWindow()
    window.show()
    sys.exit(app.exec())