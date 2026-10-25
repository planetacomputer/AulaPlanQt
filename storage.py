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
            "vertical_aisle_after": model.vertical_aisle_after,
            "students": model.students,
            "grid": {f"{r},{c}": name for (r, c), name in model.grid.items()},
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
            
            if "vertical_aisle_after" in data:
                model.vertical_aisle_after = data["vertical_aisle_after"]
            elif data.get("vertical_aisle", False):
                model.vertical_aisle_after = model.cols // 2 if model.cols > 1 else 1
            else:
                model.vertical_aisle_after = 0

            model.students = data["students"]
            model.grid = {
                tuple(map(int, k.split(","))): v
                for k, v in data["grid"].items()
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
        aisle_col = model.vertical_aisle_after
        total_visual_cols = model.cols + (1 if aisle_col > 0 else 0)
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
                visual_c = c
                if aisle_col > 0 and c >= aisle_col:
                    visual_c = c + 1

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
                svg_lines.append(
                    f'<text x="{x + (cell_w - 20)/2}" y="{y + 65}" font-family="Arial" font-size="25" font-weight="bold" fill="{text_color}" text-anchor="middle">{display_text}</text>'
                )

        if aisle_col > 0:
            ax = margin + aisle_col * cell_w + 5
            svg_lines.append(
                f'<line x1="{ax}" y1="{start_y}" x2="{ax}" y2="{start_y + model.rows * cell_h}" stroke="#e0e0e0" stroke-dasharray="6" stroke-width="2"/>'
            )

        svg_lines.append("</svg>")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(svg_lines))

    @staticmethod
    def export_html(filepath, model):
        aisle_col = model.vertical_aisle_after
        grid_columns = (
            f"repeat({aisle_col}, 240px) 20px repeat({model.cols - aisle_col}, 240px)"
            if aisle_col > 0
            else f"repeat({model.cols}, 240px)"
        )

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
        .pos {{ font-size: 12px; font-weight: bold; color: #777; }}
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
                if aisle_col > 0 and c == aisle_col:
                    html_content += '    <div class="aisle"></div>\n'
                student_name = model.grid.get((r, c), "")
                if student_name:
                    html_content += f"""    <div class="desk seated">
        <span class="pos">F{r+1}-C{c+1}</span>
        <span class="name">{html.escape(student_name)}</span>
    </div>\n"""
                else:
                    html_content += f"""    <div class="desk">
        <span class="pos">F{r+1}-C{c+1}</span>
        <span class="empty">[ Buit ]</span>
    </div>\n"""

        html_content += """    </div>
</body>
</html>"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)