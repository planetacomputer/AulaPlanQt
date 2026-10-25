import csv
import html
import json


class AulaPlanStorage:

    @staticmethod
    def import_csv(filepath, model):
        with open(filepath, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    model.add_student(row[0])

    @staticmethod
    def save_json(filepath, model):
        data = {
            "rows": model.rows,
            "cols": model.cols,
            "vertical_aisles": model.vertical_aisles,
            "show_computer_status": model.show_computer_status,
            "students": model.students,
            "grid": {f"{r},{c}": name for (r, c), name in model.grid.items()},
            "computer_working": {
                f"{r},{c}": model.computer_working.get((r, c), True)
                for r in range(model.rows)
                for c in range(model.cols)
            },
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @staticmethod
    def load_json(filepath, model):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            model.save_state()
            model.rows = data["rows"]
            model.cols = data["cols"]
            
            if "vertical_aisles" in data:
                model.vertical_aisles = model._normalize_aisles(
                    data["vertical_aisles"],
                    model.cols,
                )
            elif "vertical_aisle_after" in data:
                model.vertical_aisle_after = data["vertical_aisle_after"]
            elif data.get("vertical_aisle", False):
                model.vertical_aisle_after = model.cols // 2 if model.cols > 1 else 1
            else:
                model.vertical_aisle_after = 0
            model.show_computer_status = data.get("show_computer_status", True)

            model.students = data["students"]
            model.grid = {
                tuple(map(int, k.split(","))): v
                for k, v in data["grid"].items()
            }
            model.computer_working = {
                tuple(map(int, k.split(","))): bool(working)
                for k, working in data.get("computer_working", {}).items()
            }

    @staticmethod
    def load_default_json(filename, model):
        import os
        if os.path.exists(filename):
            try:
                AulaPlanStorage.load_json(filename, model)
                return True
            except Exception:
                pass
        return False

    @staticmethod
    def export_svg(filepath, model):
        aisle_positions = model.vertical_aisles
        total_visual_cols = model.cols + len(aisle_positions)
        cell_w, cell_h = 240, 125
        margin = 40
        width = total_visual_cols * cell_w + 2 * margin
        height = (model.rows + 2) * cell_h + 2 * margin

        svg_lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        ]
        svg_lines.append('<rect width="100%" height="100%" fill="#ffffff"/>')

        board_w = total_visual_cols * cell_w - 20
        svg_lines.append(
            f'<rect x="{margin + 10}" y="{margin}" width="{board_w}" height="50" fill="#333333" rx="6"/>'
        )
        svg_lines.append(
            f'<text x="{margin + board_w/2}" y="{margin + 31}" fill="#ffffff" font-family="Arial" font-size="16" font-weight="bold" text-anchor="middle">[ PISSARRA ]</text>'
        )

        start_y = margin + 80
        for r in range(model.rows):
            for c in range(model.cols):
                visual_c = c + sum(position <= c for position in aisle_positions)

                x = margin + visual_c * cell_w + 10
                y = start_y + r * cell_h + 10

                student_name = model.grid.get((r, c), "")
                bg = "#e1f5fe" if student_name else "#f5f5f5"
                border = "#90caf9" if student_name else "#cccccc"
                text_color = "#0d47a1" if student_name else "#bbbbbb"
                display_text = (
                    html.escape(student_name) if student_name else "[ Buit ]"
                )

                svg_lines.append(
                    f'<rect x="{x}" y="{y}" width="{cell_w - 20}" height="{cell_h - 20}" fill="{bg}" stroke="{border}" stroke-width="2" rx="8"/>'
                )
                svg_lines.append(
                    f'<text x="{x + 15}" y="{y + 24}" font-family="Arial" font-size="12" font-weight="bold" fill="#777777">F{r+1}-C{c+1}</text>'
                )
                if model.show_computer_status:
                    checkbox_x = x + cell_w - 46
                    checkbox_y = y + 10
                    computer_working = model.computer_working.get((r, c), True)
                    status_text = "Ordinador funciona" if computer_working else "Ordinador no funciona"
                    svg_lines.append(
                        f'<g aria-label="{status_text}"><title>{status_text}</title>'
                        + (
                            f'<path d="M {checkbox_x + 2} {checkbox_y + 8} l 4 4 l 8 -9" fill="none" stroke="#16803a" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
                            if computer_working
                            else f'<path d="M {checkbox_x + 3} {checkbox_y + 3} l 10 10 M {checkbox_x + 13} {checkbox_y + 3} l -10 10" fill="none" stroke="#d32f2f" stroke-width="3" stroke-linecap="round"/>'
                        )
                        + "</g>"
                    )
                svg_lines.append(
                    f'<text x="{x + (cell_w - 20)/2}" y="{y + 65}" font-family="Arial" font-size="25" font-weight="bold" fill="{text_color}" text-anchor="middle">{display_text}</text>'
                )

        for index, position in enumerate(aisle_positions):
            ax = margin + (position + index) * cell_w + 5
            svg_lines.append(
                f'<line x1="{ax}" y1="{start_y}" x2="{ax}" y2="{start_y + model.rows * cell_h}" stroke="#e0e0e0" stroke-dasharray="6" stroke-width="2"/>'
            )

        svg_lines.append("</svg>")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(svg_lines))

    @staticmethod
    def export_html(filepath, model):
        aisle_positions = model.vertical_aisles
        grid_tracks = []
        for c in range(model.cols):
            grid_tracks.append("240px")
            if c + 1 in aisle_positions:
                grid_tracks.append("20px")
        grid_columns = " ".join(grid_tracks)

        html_content = f"""<!DOCTYPE html>
<html lang="ca">
<head>
    <meta charset="UTF-8">
    <title>AulaPlan — Distribució de l'Aula</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 30px; background: #fdfdfd; color: #333; }}
        h1 {{ text-align: center; color: #2c3e50; margin-bottom: 25px; }}
        .board {{ background: #ed5b5b; color: #fff; text-align: center; padding: 14px; font-size: 30px; font-weight: bold; border-radius: 6px; margin-bottom: 25px; max-width: 1000px; margin-left: auto; margin-right: auto; }}
        .classroom {{ display: grid; grid-template-columns: {grid_columns}; gap: 14px; justify-content: center; }}
        .desk {{ background: #f5f5f5; border: 2px solid #ccc; border-radius: 8px; padding: 12px; height: 100px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 4px rgba(0,0,0,0.06); }}
        .desk.seated {{ background: #e1f5fe; border-color: #90caf9; }}
        .desk-header {{ display: flex; justify-content: space-between; align-items: center; }}
        .pos {{ font-size: 12px; font-weight: bold; color: #777; }}
        .computer-status {{ width: 20px; text-align: center; font-size: 20px; line-height: 1; font-weight: bold; }}
        .computer-status.working {{ color: #16803a; }}
        .computer-status.not-working {{ color: #d32f2f; }}
        .name {{ font-size: 40px; font-weight: bold; text-align: center; color: #0d47a1; word-wrap: break-word; }}
        .empty {{ font-size: 16px; color: #bbb; text-align: center; font-style: italic; }}
        .aisle {{ width: 20px; }}
        @media print {{ body {{ background: #fff; }} }}
    </style>
</head>
<body>
    <h1>AulaPlan — Distribució de la Classe</h1>
    <div class="board">[ PISSARRA ]</div>
    <div class="classroom">
"""

        for r in range(model.rows):
            for c in range(model.cols):
                student_name = model.grid.get((r, c), "")
                status_markup = ""
                if model.show_computer_status:
                    computer_working = model.computer_working.get((r, c), True)
                    status_text = "Ordinador funciona" if computer_working else "Ordinador no funciona"
                    status_class = "working" if computer_working else "not-working"
                    status_icon = "✓" if computer_working else "✗"
                    status_markup = f'<span class="computer-status {status_class}" aria-label="{status_text}" title="{status_text}">{status_icon}</span>'
                header = f"""        <div class="desk-header">
            <span class="pos">F{r+1}-C{c+1}</span>
            {status_markup}
        </div>
"""
                if student_name:
                    html_content += f"""    <div class="desk seated">
{header}        <span class="name">{html.escape(student_name)}</span>
    </div>\n"""
                else:
                    html_content += f"""    <div class="desk">
{header}        <span class="empty">[ Buit ]</span>
    </div>\n"""
                if c + 1 in aisle_positions:
                    html_content += '    <div class="aisle"></div>\n'

        html_content += """    </div>
</body>
</html>"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)